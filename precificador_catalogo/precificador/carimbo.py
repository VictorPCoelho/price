"""Geração do PDF precificado: carimba o novo preço sobre (ou ao lado) do original."""

from __future__ import annotations

from dataclasses import dataclass

import fitz  # PyMuPDF

from .regras import formatar_brl

_FONTE = "helv"
_FONTE_NEGRITO = "hebo"


@dataclass
class ItemCarimbo:
    """Um preço a ser carimbado no PDF."""

    pagina: int  # 0-based
    bbox: tuple[float, float, float, float]  # bbox do preço original
    novo_valor: float
    tinha_rs: bool = True


def _cor_de_fundo(page: fitz.Page, bbox: tuple) -> tuple[float, float, float]:
    """Amostra a cor ao redor do preço para o carimbo se misturar ao layout."""
    x0, y0, x1, y1 = bbox
    margem = 3
    clip = fitz.Rect(x0 - margem, y0 - margem, x1 + margem, y1 + margem)
    clip = clip & page.rect
    if clip.is_empty:
        return (1, 1, 1)
    try:
        pix = page.get_pixmap(clip=clip, colorspace=fitz.csRGB)
    except Exception:
        return (1, 1, 1)
    if pix.width < 2 or pix.height < 2:
        return (1, 1, 1)
    # Amostra pixels da borda do recorte (fora do texto em si).
    pontos = []
    w, h = pix.width, pix.height
    for px, py in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1),
                   (w // 2, 0), (w // 2, h - 1), (0, h // 2), (w - 1, h // 2)]:
        pontos.append(pix.pixel(px, py))
    r = sum(p[0] for p in pontos) / len(pontos) / 255
    g = sum(p[1] for p in pontos) / len(pontos) / 255
    b = sum(p[2] for p in pontos) / len(pontos) / 255
    return (r, g, b)


def _cor_do_texto(fundo: tuple[float, float, float]) -> tuple[float, float, float]:
    luminancia = 0.299 * fundo[0] + 0.587 * fundo[1] + 0.114 * fundo[2]
    return (0, 0, 0) if luminancia > 0.5 else (1, 1, 1)


def _tamanho_fonte_que_cabe(texto: str, largura: float, altura: float) -> float:
    """Maior tamanho de fonte em que o texto cabe no retângulo."""
    fonte = fitz.Font(_FONTE_NEGRITO)
    tamanho = altura * 0.92
    while tamanho > 4 and fonte.text_length(texto, fontsize=tamanho) > largura:
        tamanho -= 0.25
    return max(tamanho, 4)


def carimbar(
    pdf_bytes: bytes,
    itens: list[ItemCarimbo],
    modo: str = "substituir",
) -> bytes:
    """Aplica os carimbos e retorna os bytes do novo PDF.

    No modo "substituir" o preço original é de fato removido do PDF
    (redação), não apenas coberto — copiar o texto do PDF final não
    revela o preço de custo.
    """
    if modo not in ("substituir", "adicionar"):
        raise ValueError(f"Modo de carimbo desconhecido: {modo}")

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    por_pagina: dict[int, list[ItemCarimbo]] = {}
    for item in itens:
        por_pagina.setdefault(item.pagina, []).append(item)

    for num_pagina, itens_pagina in por_pagina.items():
        page = doc[num_pagina]
        if modo == "substituir":
            _substituir_na_pagina(page, itens_pagina)
        else:
            for item in itens_pagina:
                _adicionar(page, item.bbox,
                           formatar_brl(item.novo_valor, com_rs=item.tinha_rs))

    saida = doc.tobytes(garbage=3, deflate=True)
    doc.close()
    return saida


def _substituir_na_pagina(page: fitz.Page, itens: list[ItemCarimbo]) -> None:
    # 1) Amostra as cores de fundo ANTES de redigir.
    planos = []
    for item in itens:
        rect = fitz.Rect(item.bbox)
        fundo = _cor_de_fundo(page, item.bbox)
        planos.append((item, rect, fundo, _cor_do_texto(fundo)))

    # 2) Remove os preços originais da camada de texto (redação real),
    #    preenchendo com a cor do fundo e preservando as imagens.
    for _, rect, fundo, _cor in planos:
        folga = fitz.Rect(rect.x0 - 1, rect.y0 - 1, rect.x1 + 1, rect.y1 + 1)
        page.add_redact_annot(folga, fill=fundo)
    page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)

    # 3) Escreve os novos preços no lugar.
    fonte = fitz.Font(_FONTE_NEGRITO)
    for item, rect, _fundo, cor_texto in planos:
        texto = formatar_brl(item.novo_valor, com_rs=item.tinha_rs)
        # O novo texto pode ser mais largo (ex.: 99,90 → 199,90): permite
        # extravasar um pouco à direita antes de reduzir a fonte.
        largura_max = rect.width * 1.25
        tamanho = _tamanho_fonte_que_cabe(texto, largura_max, rect.height)
        baseline = rect.y1 - fonte.descender * -1 * tamanho * 0.25
        page.insert_text(
            fitz.Point(rect.x0, baseline),
            texto,
            fontname=_FONTE_NEGRITO,
            fontsize=tamanho,
            color=cor_texto,
        )


def _adicionar(page: fitz.Page, bbox: tuple, texto: str) -> None:
    """Desenha uma etiqueta com o novo preço logo abaixo do original."""
    x0, y0, x1, y1 = bbox
    altura = (y1 - y0) * 1.1
    tamanho = _tamanho_fonte_que_cabe(texto, 10_000, altura * 0.8)
    fonte = fitz.Font(_FONTE_NEGRITO)
    largura_texto = fonte.text_length(texto, fontsize=tamanho)
    pad = 3
    etiqueta = fitz.Rect(x0, y1 + 1, x0 + largura_texto + 2 * pad, y1 + 1 + altura)
    if etiqueta.y1 > page.rect.y1:  # sem espaço abaixo: desenha acima
        etiqueta = fitz.Rect(x0, y0 - 1 - altura, x0 + largura_texto + 2 * pad, y0 - 1)
    page.draw_rect(etiqueta, color=None, fill=(0.85, 0.1, 0.2), radius=0.2)
    baseline = etiqueta.y1 - (etiqueta.height - tamanho * 0.75) / 2
    page.insert_text(
        fitz.Point(etiqueta.x0 + pad, baseline),
        texto,
        fontname=_FONTE_NEGRITO,
        fontsize=tamanho,
        color=(1, 1, 1),
    )


def imagem_pagina(pdf_bytes: bytes, pagina: int, destaques: list[tuple] | None = None,
                  zoom: float = 2.0) -> bytes:
    """Renderiza uma página como PNG, com retângulos de destaque opcionais."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc[pagina]
    if destaques:
        for bbox in destaques:
            rect = fitz.Rect(bbox)
            page.draw_rect(rect, color=(1, 0, 0), width=1.2)
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    png = pix.tobytes("png")
    doc.close()
    return png
