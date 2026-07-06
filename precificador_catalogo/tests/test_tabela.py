"""Testes do fluxo de dois arquivos: tabela de preços + localização de códigos."""

import io
import sys
from pathlib import Path

import fitz
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from precificador.carimbo import ItemCarimbo, carimbar
from precificador.extracao import localizar_codigos
from precificador.tabela import (
    adivinhar_colunas,
    extrair_linhas,
    ler_planilha,
    ler_tabela_pdf,
    normalizar_codigo,
)


def _catalogo_com_codigos() -> bytes:
    """Catálogo com fotos (simuladas) e códigos, sem preços."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 100), "Body manga longa", fontsize=12)
    page.insert_text((72, 118), "Ref: 1023", fontsize=11)
    page.insert_text((300, 100), "Conjunto 2 pecas", fontsize=12)
    page.insert_text((300, 118), "REF2044", fontsize=11)
    page.insert_text((72, 300), "Codigo parecido: 10235", fontsize=10)
    page2 = doc.new_page()
    page2.insert_text((72, 100), "Vestido festa - ref 30-77", fontsize=12)
    dados = doc.tobytes()
    doc.close()
    return dados


# ------------------------------------------------------------- normalização
@pytest.mark.parametrize(
    "bruto, esperado",
    [
        ("1023", "1023"),
        ("Ref: 10-23", "REF1023"),
        (" ref 1023 ", "REF1023"),
        ("1023.0", "1023"),  # Excel transformou em float
        (1023, "1023"),
        ("AB-12/3", "AB123"),
    ],
)
def test_normalizar_codigo(bruto, esperado):
    assert normalizar_codigo(bruto) == esperado


# ---------------------------------------------------------------- planilha
def _planilha_exemplo() -> bytes:
    df = pd.DataFrame({
        "Referência": ["1023", "2044", "3077", "9999", ""],
        "Descrição": ["Body", "Conjunto", "Vestido", "Sem preço", "Vazia"],
        "Preço": ["R$ 29,90", "89,90", 119.9, None, None],
    })
    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    return buf.getvalue()


def _precos(linha):
    return [(p.rotulo, p.valor) for p in linha.precos]


def test_ler_planilha_e_adivinhar_colunas():
    df = ler_planilha(_planilha_exemplo(), "precos.xlsx")
    col_codigo, cols_preco = adivinhar_colunas(df)
    assert col_codigo == "Referência"
    assert cols_preco == ["Preço"]


def test_extrair_linhas_planilha():
    df = ler_planilha(_planilha_exemplo(), "precos.xlsx")
    linhas, avisos = extrair_linhas(df, "Referência", ["Preço"])
    assert [(l.codigo, _precos(l)) for l in linhas] == [
        ("1023", [("", 29.90)]), ("2044", [("", 89.90)]), ("3077", [("", 119.90)])
    ]
    assert linhas[0].descricao == "Body"
    assert any("9999" in a for a in avisos)  # código sem preço vira aviso


def test_extrair_linhas_planilha_varias_colunas_de_preco():
    df = pd.DataFrame({
        "Ref": ["1023", "2044"],
        "Preço 1 a 3": ["49,90", "59,90"],
        "Preço 4 a 8": ["54,90", None],
    })
    linhas, _ = extrair_linhas(df, "Ref", ["Preço 1 a 3", "Preço 4 a 8"])
    assert _precos(linhas[0]) == [("Preço 1 a 3", 49.90), ("Preço 4 a 8", 54.90)]
    assert _precos(linhas[1]) == [("Preço 1 a 3", 59.90)]


def test_extrair_linhas_csv():
    csv = "codigo;valor\n1023;29,90\n2044;R$ 89,90\n"
    df = ler_planilha(csv.encode(), "precos.csv")
    linhas, _ = extrair_linhas(df, "codigo", ["valor"])
    assert [(l.codigo, _precos(l)) for l in linhas] == [
        ("1023", [("", 29.90)]), ("2044", [("", 89.90)])
    ]


def test_tabela_pdf_simples():
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 100), "1023  Body manga longa  R$ 29,90", fontsize=11)
    page.insert_text((72, 120), "2044  Conjunto 2 pecas  89,90", fontsize=11)
    page.insert_text((72, 140), "Tabela de precos - validade 30 dias", fontsize=9)
    dados = doc.tobytes()
    doc.close()
    linhas, avisos = ler_tabela_pdf(dados)
    assert [(l.codigo, _precos(l)) for l in linhas] == [
        ("1023", [("", 29.90)]), ("2044", [("", 89.90)])
    ]
    assert avisos == []


def test_tabela_pdf_com_faixas_de_tamanho():
    """Reproduz o layout real (UP BABY): cabeçalho com faixas de tamanho,
    "R$" separado do valor, preços alinhados por coluna e páginas de
    continuação sem cabeçalho próprio."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((40, 80), "Referência", fontsize=9)
    page.insert_text((145, 80), "Descrição", fontsize=9)
    page.insert_text((255, 80), "1 a 3", fontsize=9)
    page.insert_text((293, 80), "4 a 8", fontsize=9)
    page.insert_text((362, 80), "10 a 12", fontsize=9)
    page.insert_text((48, 100), "47179", fontsize=9)
    page.insert_text((77, 100), "VESTIDO MEIA MALHA", fontsize=9)
    for x, v in [(248, "79,90"), (285, "89,90"), (358, "99,90")]:
        page.insert_text((x, 100), "R$", fontsize=9)
        page.insert_text((x + 15, 100), v, fontsize=9)
    page.insert_text((48, 112), "47180", fontsize=9)
    page.insert_text((77, 112), "CONJUNTO BLUSA E SHORT", fontsize=9)
    page.insert_text((248, 112), "R$", fontsize=9)
    page.insert_text((263, 112), "59,90", fontsize=9)
    # página de continuação, sem cabeçalho: herda as colunas
    page2 = doc.new_page()
    page2.insert_text((48, 100), "47181", fontsize=9)
    page2.insert_text((77, 100), "MACAQUINHO", fontsize=9)
    page2.insert_text((285, 100), "R$", fontsize=9)
    page2.insert_text((300, 100), "44,90", fontsize=9)
    dados = doc.tobytes()
    doc.close()

    linhas, avisos = ler_tabela_pdf(dados)
    assert avisos == []
    assert [(l.codigo, _precos(l)) for l in linhas] == [
        ("47179", [("1 a 3", 79.90), ("4 a 8", 89.90), ("10 a 12", 99.90)]),
        ("47180", [("1 a 3", 59.90)]),
        ("47181", [("4 a 8", 44.90)]),
    ]
    assert linhas[0].descricao == "VESTIDO MEIA MALHA"


# -------------------------------------------------------------- localização
def test_localizar_codigos():
    pdf = _catalogo_com_codigos()
    ocorrencias, avisos = localizar_codigos(pdf, ["1023", "2044", "3077", "8888"])
    assert len(ocorrencias["1023"]) == 1  # "Ref: 1023", e NAO dentro de "10235"
    assert ocorrencias["1023"][0].pagina == 0
    assert len(ocorrencias["2044"]) == 1  # "REF2044" (fronteira letra-numero)
    assert len(ocorrencias["3077"]) == 1  # "ref 30-77" na pagina 2
    assert ocorrencias["3077"][0].pagina == 1
    assert ocorrencias["8888"] == []  # nao existe
    assert avisos == []


def test_localizar_avisa_pagina_escaneada():
    doc = fitz.open()
    doc.new_page()
    dados = doc.tobytes()
    doc.close()
    ocorrencias, avisos = localizar_codigos(dados, ["1023"])
    assert ocorrencias["1023"] == []
    assert any("sem texto" in a for a in avisos)


def test_tabela_pdf_blocos_lado_a_lado_com_grade():
    """Reproduz o layout de tabela com blocos lado a lado
    ("Código Grade Preço | Código Grade Preço") e o mesmo código repetido
    em linhas seguidas com grades diferentes."""
    doc = fitz.open()
    page = doc.new_page()
    # cabeçalho dos dois blocos
    for x in (36, 196):
        page.insert_text((x, 36), "Código", fontsize=8)
        page.insert_text((x + 54, 36), "Grade", fontsize=8)
        page.insert_text((x + 108, 36), "Preço", fontsize=8)
    # bloco 1: mesmo código com duas grades; bloco 2: outro código
    dados_linhas = [
        (48, [("1.264.006", "B/MB/GB/GG", "59,90"), ("1.264.030", "B/MB/GB/GG", "87,90")]),
        (63, [("1.264.006", "1/2/3", "65,90"), ("1.264.030", "1/2/3", "89,90")]),
        (78, [("1.264.007", "B/MB/GB/GG", "41,90"), ("1.264.031", "ÚNICO", "99,90")]),
    ]
    for y, blocos in dados_linhas:
        for k, (cod, grade, preco) in enumerate(blocos):
            x = 36 + k * 160
            page.insert_text((x - 3, y), cod, fontsize=8)
            page.insert_text((x + 44, y), grade, fontsize=8)
            page.insert_text((x + 103, y), "R$", fontsize=8)
            page.insert_text((x + 121, y), preco, fontsize=8)
    dados = doc.tobytes()
    doc.close()

    linhas, avisos = ler_tabela_pdf(dados)
    assert avisos == []
    por = {l.codigo: _precos(l) for l in linhas}
    assert por["1264006"] == [("B/MB/GB/GG", 59.90), ("1/2/3", 65.90)]
    assert por["1264030"] == [("B/MB/GB/GG", 87.90), ("1/2/3", 89.90)]
    assert por["1264007"] == [("B/MB/GB/GG", 41.90)]
    assert por["1264031"] == [("ÚNICO", 99.90)]


# ------------------------------------------------------- etiquetas e logo
def test_etiquetas_nao_se_sobrepoem():
    """Códigos empilhados (como em catálogos com várias refs por foto)
    não podem gerar etiquetas umas em cima das outras."""
    doc = fitz.open()
    page = doc.new_page()
    for i, ref in enumerate(["47187", "47188", "47189"]):
        page.insert_text((72, 100 + i * 14), f"REF {ref}", fontsize=10)
    pdf = doc.tobytes()
    doc.close()

    ocorrencias, _ = localizar_codigos(pdf, ["47187", "47188", "47189"])
    itens = []
    for cod, ocs in ocorrencias.items():
        for oc in ocs:
            itens.append(ItemCarimbo(
                pagina=oc.pagina, bbox=oc.bbox, novo_valor=0.0,
                linhas_etiqueta=[f"1 a 3: R$ {cod[-2:]},90", "4 a 8: R$ 99,90"],
            ))
    doc = fitz.open(stream=carimbar(pdf, itens, modo="adicionar"), filetype="pdf")
    # reconstrói os retângulos desenhados (fills) e checa interseção 2 a 2
    fills = [d["rect"] for d in doc[0].get_drawings() if d.get("fill")]
    doc.close()
    assert len(fills) == 3
    for i in range(len(fills)):
        for j in range(i + 1, len(fills)):
            assert not fills[i].intersects(fills[j]), (fills[i], fills[j])


def test_linhas_da_etiqueta():
    from precificador.regras import linhas_da_etiqueta

    assert linhas_da_etiqueta("BERMUDA MOLETINHO", [("1 a 3", 119.90)]) == [
        "BERMUDA MOLETINHO", "1 a 3: R$ 119,90"
    ]
    # sem rótulo de tamanho ("—") a linha é só o preço
    assert linhas_da_etiqueta("", [("—", 59.90)]) == ["R$ 59,90"]
    # descrição comprida é abreviada
    linhas = linhas_da_etiqueta("CONJUNTO BATA EM MEIA MALHA E BERMUDA", [("", 99.90)])
    assert linhas[0].endswith("…") and len(linhas[0]) <= 30


def test_etiqueta_nao_cobre_descricao_quando_ha_espaco():
    """Reproduz o layout dos catálogos: código com descrição logo abaixo,
    no canto inferior da página, e foto (sem texto) acima. A etiqueta deve
    ir para um lugar sem texto, nunca sobre a descrição."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    # canto inferior esquerdo
    page.insert_text((40, 700), "1.264.084", fontsize=10)
    page.insert_text((40, 714), "CONJUNTO BATA EM MEIA MALHA E BERMUDA", fontsize=8)
    page.insert_text((40, 726), "EM MOLETINHO ECO LISTRADO", fontsize=8)
    # canto inferior direito
    page.insert_text((400, 700), "1.264.090", fontsize=10)
    page.insert_text((400, 714), "VESTIDO EM COTTON", fontsize=8)
    pdf = doc.tobytes()
    doc.close()

    ocorrencias, _ = localizar_codigos(pdf, ["1264084", "1264090"])
    itens = [
        ItemCarimbo(pagina=oc.pagina, bbox=oc.bbox, novo_valor=0.0,
                    linhas_etiqueta=["BERMUDA…", "1/2/3: R$ 100,90", "4/6/8/10: R$ 119,90"])
        for ocs in ocorrencias.values() for oc in ocs
    ]
    saida = carimbar(pdf, itens, modo="adicionar")

    doc = fitz.open(stream=saida, filetype="pdf")
    etiquetas = [d["rect"] for d in doc[0].get_drawings() if d.get("fill")]
    # palavras originais (sem os textos que a própria etiqueta escreveu:
    # filtra pelos que existiam no pdf de entrada)
    orig = fitz.open(stream=pdf, filetype="pdf")
    palavras = [fitz.Rect(w[:4]) for w in orig[0].get_text("words")]
    orig.close()
    doc.close()
    assert len(etiquetas) == 2
    for e in etiquetas:
        for p in palavras:
            assert not e.intersects(p), (e, p)


def test_cor_da_etiqueta_personalizada():
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 100), "REF 1023", fontsize=10)
    pdf = doc.tobytes()
    doc.close()
    ocs, _ = localizar_codigos(pdf, ["1023"])
    itens = [ItemCarimbo(pagina=0, bbox=ocs["1023"][0].bbox, novo_valor=59.90)]
    saida = carimbar(pdf, itens, modo="adicionar", cor_etiqueta=(0.1, 0.3, 0.6))
    doc = fitz.open(stream=saida, filetype="pdf")
    fills = [d["fill"] for d in doc[0].get_drawings() if d.get("fill")]
    doc.close()
    assert any(abs(f[0] - 0.1) < 0.02 and abs(f[2] - 0.6) < 0.02 for f in fills)


def test_inserir_logo_primeira_pagina():
    from precificador.carimbo import inserir_logo

    doc = fitz.open()
    doc.new_page()
    doc.new_page()
    pdf = doc.tobytes()
    doc.close()

    # logo: PNG pequeno gerado na hora
    img = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 40, 20))
    img.set_rect(img.irect, (200, 30, 60))
    logo = img.tobytes("png")

    saida = inserir_logo(pdf, logo, posicao="inferior-direito", largura_frac=0.2)
    doc = fitz.open(stream=saida, filetype="pdf")
    assert len(doc[0].get_images()) == 1
    assert len(doc[1].get_images()) == 0  # só na primeira página
    doc.close()

    saida = inserir_logo(pdf, logo, todas_as_paginas=True)
    doc = fitz.open(stream=saida, filetype="pdf")
    assert len(doc[0].get_images()) == 1 and len(doc[1].get_images()) == 1
    doc.close()


def test_hex_para_rgb():
    from precificador.regras import hex_para_rgb
    assert hex_para_rgb("#FFFFFF") == (1.0, 1.0, 1.0)
    r, g, b = hex_para_rgb("#3D3D45")
    assert abs(r - 0.239) < 0.01 and abs(b - 0.27) < 0.01


# ---------------------------------------------------------- fluxo completo
def test_fluxo_dois_arquivos_carimba_preco_ao_lado():
    pdf = _catalogo_com_codigos()
    ocorrencias, _ = localizar_codigos(pdf, ["1023", "3077"])
    itens = [
        ItemCarimbo(pagina=oc.pagina, bbox=oc.bbox, novo_valor=59.90, tinha_rs=True)
        for oc in ocorrencias["1023"]
    ] + [
        ItemCarimbo(pagina=oc.pagina, bbox=oc.bbox, novo_valor=249.90, tinha_rs=True)
        for oc in ocorrencias["3077"]
    ]
    saida = carimbar(pdf, itens, modo="adicionar")
    doc = fitz.open(stream=saida, filetype="pdf")
    texto_p1, texto_p2 = doc[0].get_text(), doc[1].get_text()
    doc.close()
    assert "1023" in texto_p1 and "59,90" in texto_p1  # codigo mantido + preco
    assert "249,90" in texto_p2
