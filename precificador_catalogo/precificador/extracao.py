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


@dataclass
class CodigoLocalizado:
    """Uma ocorrência de um código de produto no catálogo."""

    codigo: str  # código normalizado
    pagina: int  # 0-based
    bbox: tuple[float, float, float, float]


def localizar_codigos(
    caminho_ou_bytes, codigos: list[str]
) -> tuple[dict[str, list[CodigoLocalizado]], list[str]]:
    """Procura códigos de produto (já normalizados) nas páginas do PDF.

    A comparação ignora maiúsculas/minúsculas e pontuação: o código "1023"
    casa com "Ref: 10-23" desde que os caracteres alfanuméricos batam e o
    trecho não faça parte de um token maior (evita achar "1023" dentro de
    "10235").

    Retorna ({codigo: [ocorrências]}, avisos). Códigos não encontrados
    ficam com lista vazia.
    """
    if isinstance(caminho_ou_bytes, (bytes, bytearray)):
        doc = fitz.open(stream=caminho_ou_bytes, filetype="pdf")
    else:
        doc = fitz.open(caminho_ou_bytes)

    resultado: dict[str, list[CodigoLocalizado]] = {c: [] for c in codigos}
    avisos: list[str] = []
    paginas_sem_texto = []

    for num_pagina, page in enumerate(doc):
        linhas = _linhas_com_chars(page)
        if sum(len(bb) for _, bb in linhas) < 5:
            paginas_sem_texto.append(num_pagina + 1)
            continue
        for texto_linha, bboxes in linhas:
            # versão normalizada da linha + mapa de volta para o índice do char
            norm_chars = []
            mapa = []
            for i, ch in enumerate(texto_linha):
                if ch.isalnum():
                    norm_chars.append(ch.upper())
                    mapa.append(i)
            norm = "".join(norm_chars)
            for codigo in codigos:
                inicio = 0
                while True:
                    pos = norm.find(codigo, inicio)
                    if pos < 0:
                        break
                    inicio = pos + 1
                    fim = pos + len(codigo)
                    # Fronteira de token: rejeita se o vizinho alfanumérico
                    # cola no código E é do mesmo tipo (dígito com dígito,
                    # letra com letra). Assim "1023" não casa dentro de
                    # "10235", mas casa em "REF1023".
                    i_ini, i_fim = mapa[pos], mapa[fim - 1]
                    if (
                        pos > 0
                        and mapa[pos - 1] == i_ini - 1
                        and norm[pos - 1].isdigit() == codigo[0].isdigit()
                    ):
                        continue
                    if (
                        fim < len(norm)
                        and mapa[fim] == i_fim + 1
                        and norm[fim].isdigit() == codigo[-1].isdigit()
                    ):
                        continue
                    resultado[codigo].append(
                        CodigoLocalizado(
                            codigo=codigo,
                            pagina=num_pagina,
                            bbox=_bbox_do_trecho(bboxes, i_ini, i_fim + 1),
                        )
                    )
    doc.close()

    if paginas_sem_texto:
        avisos.append(
            "Páginas do catálogo sem texto legível (imagem escaneada): "
            f"{_lista(paginas_sem_texto)}. Os códigos dessas páginas não podem "
            "ser localizados automaticamente."
        )
    return resultado, avisos
