"""Extração de preços de PDFs de catálogo.

Detecta valores monetários no texto do PDF junto com a posição exata
(bounding box) de cada ocorrência, para permitir o carimbo do novo
preço no mesmo lugar.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import fitz  # PyMuPDF

# Preço brasileiro: "R$ 1.234,56", "R$129,90", "1.234,56", "129,90"
# O prefixo R$ é capturado quando presente para o carimbo cobrir o texto todo.
_PRECO_COM_RS = re.compile(r"R\$\s*\d{1,3}(?:\.\d{3})*,\d{2}")
_PRECO_SEM_RS = re.compile(r"(?<![\d.,])\d{1,3}(?:\.\d{3})*,\d{2}(?![\d,])")


@dataclass
class PrecoDetectado:
    """Um preço encontrado no PDF."""

    pagina: int  # 0-based
    texto: str  # texto exato encontrado, ex.: "R$ 129,90"
    valor: float  # valor numérico, ex.: 129.90
    bbox: tuple[float, float, float, float]  # (x0, y0, x1, y1) em pontos
    tinha_rs: bool = True
    avisos: list[str] = field(default_factory=list)


def _texto_para_valor(texto: str) -> float:
    """Converte "R$ 1.234,56" em 1234.56."""
    limpo = texto.replace("R$", "").strip()
    limpo = limpo.replace(".", "").replace(",", ".")
    return float(limpo)


def _linhas_com_chars(page: fitz.Page):
    """Retorna as linhas de texto da página como (texto, lista de bbox por char)."""
    raw = page.get_text("rawdict")
    linhas = []
    for bloco in raw.get("blocks", []):
        for linha in bloco.get("lines", []):
            chars: list[tuple[str, tuple]] = []
            for span in linha.get("spans", []):
                for ch in span.get("chars", []):
                    chars.append((ch["c"], ch["bbox"]))
            if chars:
                texto = "".join(c for c, _ in chars)
                bboxes = [b for _, b in chars]
                linhas.append((texto, bboxes))
    return linhas


def _bbox_do_trecho(bboxes: list[tuple], inicio: int, fim: int) -> tuple:
    """União dos bboxes dos caracteres [inicio:fim]."""
    xs0, ys0, xs1, ys1 = zip(*bboxes[inicio:fim])
    return (min(xs0), min(ys0), max(xs1), max(ys1))


def extrair_precos(
    caminho_ou_bytes,
    exigir_rs: bool = True,
    valor_minimo: float = 1.0,
    valor_maximo: float = 10000.0,
) -> tuple[list[PrecoDetectado], list[str]]:
    """Extrai todos os preços de um PDF.

    ``exigir_rs=True`` considera apenas valores precedidos de "R$" — mais
    seguro contra falsos positivos (códigos, medidas). Com ``False`` também
    captura números soltos no formato 99,90 (para catálogos que omitem o R$).

    Retorna (precos, avisos_gerais). Avisos gerais incluem páginas sem texto
    (provável PDF escaneado) e páginas sem nenhum preço detectado.
    """
    if isinstance(caminho_ou_bytes, (bytes, bytearray)):
        doc = fitz.open(stream=caminho_ou_bytes, filetype="pdf")
    else:
        doc = fitz.open(caminho_ou_bytes)

    padrao = _PRECO_COM_RS if exigir_rs else re.compile(
        f"(?:{_PRECO_COM_RS.pattern})|(?:{_PRECO_SEM_RS.pattern})"
    )

    precos: list[PrecoDetectado] = []
    avisos_gerais: list[str] = []
    paginas_sem_texto = []
    paginas_sem_preco = []

    for num_pagina, page in enumerate(doc):
        linhas = _linhas_com_chars(page)
        total_chars = sum(len(bb) for _, bb in linhas)
        if total_chars < 5:
            paginas_sem_texto.append(num_pagina + 1)
            continue

        achou_na_pagina = False
        for texto_linha, bboxes in linhas:
            for m in padrao.finditer(texto_linha):
                trecho = m.group(0)
                try:
                    valor = _texto_para_valor(trecho)
                except ValueError:
                    continue
                item = PrecoDetectado(
                    pagina=num_pagina,
                    texto=trecho,
                    valor=valor,
                    bbox=_bbox_do_trecho(bboxes, m.start(), m.end()),
                    tinha_rs="R$" in trecho,
                )
                if valor < valor_minimo:
                    item.avisos.append(f"valor muito baixo (R$ {valor:.2f})")
                if valor > valor_maximo:
                    item.avisos.append(f"valor muito alto (R$ {valor:.2f})")
                precos.append(item)
                achou_na_pagina = True

        if not achou_na_pagina:
            paginas_sem_preco.append(num_pagina + 1)

    doc.close()

    if paginas_sem_texto:
        avisos_gerais.append(
            "Páginas sem texto (provavelmente imagem escaneada — os preços "
            f"delas NÃO foram detectados): {_lista(paginas_sem_texto)}. "
            "Confira essas páginas manualmente."
        )
    if paginas_sem_preco:
        avisos_gerais.append(
            f"Páginas com texto mas sem preço detectado: {_lista(paginas_sem_preco)}. "
            "Se deveriam ter preço, confira manualmente ou desative a opção "
            "de exigir o R$."
        )
    return precos, avisos_gerais


def _lista(nums: list[int]) -> str:
    return ", ".join(str(n) for n in nums)
