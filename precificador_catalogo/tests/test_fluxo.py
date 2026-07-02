"""Testes do fluxo completo: extração → regra de preço → carimbo."""

import sys
from pathlib import Path

import fitz
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from precificador.carimbo import ItemCarimbo, carimbar
from precificador.extracao import extrair_precos
from precificador.regras import (
    PerfilMarca,
    RepositorioPerfis,
    arredondar,
    calcular_preco,
    formatar_brl,
)


def _catalogo_exemplo() -> bytes:
    """Gera um PDF de catálogo com preços em posições variadas."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 100), "Body manga longa - Ref 1023", fontsize=12)
    page.insert_text((72, 118), "R$ 29,90", fontsize=14)
    page.insert_text((300, 100), "Conjunto 2 pecas - Ref 2044", fontsize=12)
    page.insert_text((300, 118), "R$ 1.234,56", fontsize=14)
    page.insert_text((72, 200), "Macacao plush", fontsize=12)
    page.insert_text((72, 218), "49,90", fontsize=14)  # sem R$
    page.insert_text((72, 300), "Ref 300,45 nao e preco? Tamanho 1,20", fontsize=10)
    page2 = doc.new_page()
    page2.insert_text((72, 100), "Vestido festa", fontsize=12)
    page2.insert_text((72, 118), "R$ 89,90", fontsize=14)
    dados = doc.tobytes()
    doc.close()
    return dados


# ------------------------------------------------------------- arredondamento
@pytest.mark.parametrize(
    "valor, regra, esperado",
    [
        (47.32, "nenhum", 47.32),
        (47.32, "inteiro", 48.0),
        (47.0, "inteiro", 47.0),
        (47.32, "90", 47.90),
        (47.95, "90", 48.90),
        (47.90, "90", 47.90),
        (47.32, "99", 47.99),
        (47.32, "50", 47.50),
        (47.50, "50", 47.50),
        (47.51, "50", 48.00),
    ],
)
def test_arredondar(valor, regra, esperado):
    assert arredondar(valor, regra) == pytest.approx(esperado)


def test_arredondar_nunca_abaixa():
    for regra in ("inteiro", "90", "99", "50"):
        for valor in (10.0, 10.01, 10.89, 10.9, 10.91, 10.99, 11.0):
            assert arredondar(valor, regra) >= valor - 1e-9, (regra, valor)


def test_calcular_preco():
    assert calcular_preco(29.90, 2.0, "90") == pytest.approx(59.90)


def test_formatar_brl():
    assert formatar_brl(1234.5) == "R$ 1.234,50"
    assert formatar_brl(9.9, com_rs=False) == "9,90"
    assert formatar_brl(59.9) == "R$ 59,90"


# ------------------------------------------------------------------ extração
def test_extrai_apenas_com_rs():
    precos, _ = extrair_precos(_catalogo_exemplo(), exigir_rs=True)
    valores = sorted(p.valor for p in precos)
    assert valores == [29.90, 89.90, 1234.56]
    assert {p.pagina for p in precos} == {0, 1}


def test_extrai_sem_exigir_rs():
    precos, _ = extrair_precos(_catalogo_exemplo(), exigir_rs=False)
    valores = sorted(p.valor for p in precos)
    # pega tambem o 49,90 sem R$ e os numeros soltos 300,45 e 1,20
    assert 49.90 in valores
    assert 29.90 in valores


def test_alerta_valores_fora_da_faixa():
    precos, _ = extrair_precos(_catalogo_exemplo(), exigir_rs=True, valor_maximo=500.0)
    com_alerta = [p for p in precos if p.avisos]
    assert len(com_alerta) == 1
    assert com_alerta[0].valor == 1234.56


def test_aviso_pdf_escaneado():
    doc = fitz.open()
    doc.new_page()  # pagina em branco = sem texto
    dados = doc.tobytes()
    doc.close()
    precos, avisos = extrair_precos(dados)
    assert precos == []
    assert any("sem texto" in a for a in avisos)


# ------------------------------------------------------------------- carimbo
def test_carimbo_substitui_preco():
    pdf = _catalogo_exemplo()
    precos, _ = extrair_precos(pdf, exigir_rs=True)
    itens = [
        ItemCarimbo(
            pagina=p.pagina,
            bbox=p.bbox,
            novo_valor=calcular_preco(p.valor, 2.0, "90"),
            tinha_rs=p.tinha_rs,
        )
        for p in precos
    ]
    saida = carimbar(pdf, itens, modo="substituir")

    doc = fitz.open(stream=saida, filetype="pdf")
    texto_p1 = doc[0].get_text()
    texto_p2 = doc[1].get_text()
    doc.close()
    # novos precos presentes: 29,90*2=59,80->59,90 ; 89,90*2=179,80->179,90
    assert "59,90" in texto_p1
    assert "179,90" in texto_p2
    # os novos precos devem ser reencontraveis pela propria extracao
    precos_novos, _ = extrair_precos(saida, exigir_rs=True)
    assert sorted(p.valor for p in precos_novos) == [59.90, 179.90, 2469.90]


def test_carimbo_modo_adicionar_mantem_original():
    pdf = _catalogo_exemplo()
    precos, _ = extrair_precos(pdf, exigir_rs=True)
    itens = [
        ItemCarimbo(pagina=p.pagina, bbox=p.bbox, novo_valor=99.90, tinha_rs=True)
        for p in precos
        if p.pagina == 0
    ]
    saida = carimbar(pdf, itens, modo="adicionar")
    doc = fitz.open(stream=saida, filetype="pdf")
    texto = doc[0].get_text()
    doc.close()
    assert "29,90" in texto  # original preservado
    assert "99,90" in texto  # novo adicionado


# -------------------------------------------------------------------- perfis
def test_repositorio_perfis(tmp_path):
    repo = RepositorioPerfis(tmp_path / "perfis.json")
    assert repo.carregar() == {}
    perfil = PerfilMarca(nome="Marca X", multiplicador=2.3, arredondamento="99")
    repo.salvar({"Marca X": perfil})
    lidos = repo.carregar()
    assert lidos["Marca X"].multiplicador == 2.3
    assert lidos["Marca X"].arredondamento == "99"
    assert lidos["Marca X"].nome == "Marca X"
