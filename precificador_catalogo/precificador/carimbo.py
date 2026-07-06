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
    # No modo "adicionar", linhas de texto customizadas para a etiqueta
    # (ex.: um preço por faixa de tamanho). Se None, usa o novo_valor.
    linhas_etiqueta: list[str] | None = None


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


COR_ETIQUETA_PADRAO = (0.24, 0.24, 0.27)  # grafite neutro


def carimbar(
    pdf_bytes: bytes,
    itens: list[ItemCarimbo],
    modo: str = "substituir",
    cor_etiqueta: tuple[float, float, float] = COR_ETIQUETA_PADRAO,
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
            # etiquetas não podem cobrir os códigos nem umas às outras;
            # os demais textos da página são evitados quando há espaço
            obstaculos = [fitz.Rect(i.bbox) for i in itens_pagina]
            textos_da_pagina = [fitz.Rect(w[:4]) for w in page.get_text("words")]
            for item in itens_pagina:
                linhas = item.linhas_etiqueta or [
                    formatar_brl(item.novo_valor, com_rs=item.tinha_rs)
                ]
                etiqueta = _adicionar(
                    page, item.bbox, linhas, obstaculos, cor_etiqueta,
                    evitar_se_der=textos_da_pagina,
                )
                obstaculos.append(etiqueta)

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


def _adicionar(
    page: fitz.Page,
    bbox: tuple,
    linhas: list[str],
    obstaculos: list[fitz.Rect],
    cor: tuple[float, float, float] = COR_ETIQUETA_PADRAO,
    evitar_se_der: list[fitz.Rect] | None = None,
) -> fitz.Rect:
    """Desenha uma etiqueta com o(s) novo(s) preço(s) perto do código.

    Tenta várias posições (abaixo, à direita, acima, mais abaixo...) até
    achar uma que não cubra os códigos nem as outras etiquetas da página
    (``obstaculos``, obrigatórios). Os retângulos de ``evitar_se_der``
    (demais textos da página) só são respeitados se alguma posição
    permitir. Retorna o retângulo usado, para entrar nos obstáculos.
    """
    x0, y0, x1, y1 = bbox
    altura_linha = (y1 - y0) * 1.1
    tamanho = _tamanho_fonte_que_cabe("Ag", 10_000, altura_linha * 0.8)
    fonte = fitz.Font(_FONTE_NEGRITO)
    largura_texto = max(fonte.text_length(t, fontsize=tamanho) for t in linhas)
    pad = 3
    w = largura_texto + 2 * pad
    h = altura_linha * len(linhas)

    afasta = 4  # maior que a folga de 2pt da checagem de colisão
    # candidatas em ordem de preferência: colada no código primeiro
    # (abaixo, direita, acima, esquerda), depois varrendo mais longe
    candidatas = [
        fitz.Rect(x0, y1 + afasta, x0 + w, y1 + afasta + h),      # abaixo
        fitz.Rect(x1 + afasta, y0, x1 + afasta + w, y0 + h),      # à direita
        fitz.Rect(x0, y0 - afasta - h, x0 + w, y0 - afasta),      # acima
        fitz.Rect(x0 - afasta - w, y0, x0 - afasta, y0 + h),      # à esquerda
    ]
    deslocs_x = [0, w / 2 + 2, -(w / 2 + 2), w + 4, -(w + 4)]
    for passo in range(1, 7):
        dy = (h + 2) * passo
        for dx in deslocs_x:
            candidatas.append(fitz.Rect(
                x0 + dx, y1 + afasta + dy, x0 + dx + w, y1 + afasta + dy + h
            ))
            candidatas.append(fitz.Rect(
                x0 + dx, y0 - afasta - dy - h, x0 + dx + w, y0 - afasta - dy
            ))

    # o próprio código não é obstáculo para a etiqueta dele
    propria = fitz.Rect(bbox)
    duros = [o for o in obstaculos if o != propria]
    textos = evitar_se_der or []

    def _cabe_na_pagina(r: fitz.Rect) -> bool:
        return (page.rect.x0 <= r.x0 and r.x1 <= page.rect.x1
                and page.rect.y0 <= r.y0 and r.y1 <= page.rect.y1)

    def _bate_nos_duros(r: fitz.Rect) -> bool:
        folga = fitz.Rect(r.x0 - 2, r.y0 - 2, r.x1 + 2, r.y1 + 2)
        return any(folga.intersects(o) for o in duros)

    def _area_de_texto_coberta(r: fitz.Rect) -> float:
        folga = fitz.Rect(r.x0 - 2, r.y0 - 2, r.x1 + 2, r.y1 + 2)
        return sum((folga & o).get_area() for o in textos if folga.intersects(o))

    # escolhe a primeira posição que não cobre texto nenhum; se não houver,
    # a que cobre a MENOR área de texto (nunca outra etiqueta ou código)
    etiqueta = None
    menor = None
    for r in candidatas:
        if not _cabe_na_pagina(r) or _bate_nos_duros(r):
            continue
        area = _area_de_texto_coberta(r)
        if area == 0:
            etiqueta = r
            break
        if menor is None or area < menor[0]:
            menor = (area, r)
    if etiqueta is None:
        etiqueta = menor[1] if menor else candidatas[0]

    page.draw_rect(etiqueta, color=None, fill=cor, radius=0.2 / len(linhas))
    cor_texto = _cor_do_texto(cor)
    for i, texto in enumerate(linhas):
        topo = etiqueta.y0 + i * altura_linha
        baseline = topo + altura_linha - (altura_linha - tamanho * 0.75) / 2
        page.insert_text(
            fitz.Point(etiqueta.x0 + pad, baseline),
            texto,
            fontname=_FONTE_NEGRITO,
            fontsize=tamanho,
            color=cor_texto,
        )
    return etiqueta


POSICOES_LOGO = {
    "superior-esquerdo": "Canto superior esquerdo",
    "superior-direito": "Canto superior direito",
    "inferior-esquerdo": "Canto inferior esquerdo",
    "inferior-direito": "Canto inferior direito",
}


def inserir_logo(
    pdf_bytes: bytes,
    logo_bytes: bytes,
    posicao: str = "inferior-direito",
    largura_frac: float = 0.20,
    todas_as_paginas: bool = False,
    margem: float = 16.0,
) -> bytes:
    """Insere o logo da marca (PNG/JPG) na primeira página (ou em todas).

    ``largura_frac`` é a largura do logo como fração da largura da página;
    a altura acompanha a proporção da imagem.
    """
    if posicao not in POSICOES_LOGO:
        raise ValueError(f"Posição de logo desconhecida: {posicao}")
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    img = fitz.open(stream=logo_bytes)
    prop = img[0].rect.height / img[0].rect.width if img[0].rect.width else 1.0
    img.close()

    paginas = range(len(doc)) if todas_as_paginas else [0]
    for num in paginas:
        page = doc[num]
        pw, ph = page.rect.width, page.rect.height
        w = pw * largura_frac
        h = w * prop
        if "esquerdo" in posicao:
            x0 = margem
        else:
            x0 = pw - margem - w
        if "superior" in posicao:
            y0 = margem
        else:
            y0 = ph - margem - h
        page.insert_image(fitz.Rect(x0, y0, x0 + w, y0 + h),
                          stream=logo_bytes, keep_proportion=True)
    saida = doc.tobytes(garbage=3, deflate=True)
    doc.close()
    return saida


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
