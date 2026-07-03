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


def test_ler_planilha_e_adivinhar_colunas():
    df = ler_planilha(_planilha_exemplo(), "precos.xlsx")
    col_codigo, col_preco = adivinhar_colunas(df)
    assert col_codigo == "Referência"
    assert col_preco == "Preço"


def test_extrair_linhas_planilha():
    df = ler_planilha(_planilha_exemplo(), "precos.xlsx")
    linhas, avisos = extrair_linhas(df, "Referência", "Preço")
    assert [(l.codigo, l.preco) for l in linhas] == [
        ("1023", 29.90), ("2044", 89.90), ("3077", 119.90)
    ]
    assert any("9999" in a for a in avisos)  # código sem preço vira aviso


def test_extrair_linhas_csv():
    csv = "codigo;valor\n1023;29,90\n2044;R$ 89,90\n"
    df = ler_planilha(csv.encode(), "precos.csv")
    linhas, _ = extrair_linhas(df, "codigo", "valor")
    assert [(l.codigo, l.preco) for l in linhas] == [("1023", 29.90), ("2044", 89.90)]


def test_tabela_pdf():
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 100), "1023  Body manga longa  R$ 29,90", fontsize=11)
    page.insert_text((72, 120), "2044  Conjunto 2 pecas  89,90", fontsize=11)
    page.insert_text((72, 140), "Tabela de precos - validade 30 dias", fontsize=9)
    dados = doc.tobytes()
    doc.close()
    linhas, avisos = ler_tabela_pdf(dados)
    assert [(l.codigo, l.preco) for l in linhas] == [("1023", 29.90), ("2044", 89.90)]
    assert avisos == []


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
