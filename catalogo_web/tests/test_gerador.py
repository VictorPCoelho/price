"""Testes do gerador do catálogo web."""

import io
import json
import re
import sys
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from catalogo_web.gerador import gerar_site, limpar_whatsapp

JPG_FALSO = b"\xff\xd8\xff\xe0fakejpg\xff\xd9"

ITENS = [
    {
        "codigo": "1264062",
        "descricao": "POLO EM PIQUET",
        "pagina": 0,
        "pontos": [[0.12, 0.9]],
        "precos": [{"tamanho": "1/2/3", "valor": 61.90},
                   {"tamanho": "4/6/8/10", "valor": 71.90}],
    },
    {
        "codigo": "1264161",
        "descricao": "",
        "pagina": 1,
        "pontos": [[0.85, 0.88], [0.4, 0.5]],
        "precos": [{"tamanho": "", "valor": 97.90}],
    },
    {  # sem preço: não deve entrar no site
        "codigo": "9999",
        "descricao": "SEM PRECO",
        "pagina": 0,
        "pontos": [[0.5, 0.5]],
        "precos": [],
    },
]


# ------------------------------------------------------------ whatsapp
@pytest.mark.parametrize(
    "entrada, esperado",
    [
        ("31 99999-8888", "5531999998888"),
        ("(31) 9 9999-8888", "5531999998888"),
        ("5531999998888", "5531999998888"),
        ("3132221111", "553132221111"),  # fixo com DDD
        ("999998888", ""),  # sem DDD: inválido
        ("abc", ""),
        ("", ""),
    ],
)
def test_limpar_whatsapp(entrada, esperado):
    assert limpar_whatsapp(entrada) == esperado


# ------------------------------------------------------------ site
def _abrir_site(**kwargs):
    padrao = dict(
        titulo="UP BABY Verão 26/27",
        whatsapp="31 99999-8888",
        paginas_jpg=[JPG_FALSO, JPG_FALSO],
        itens=ITENS,
        cor_tema="#5B3A5E",
    )
    padrao.update(kwargs)
    zip_bytes = gerar_site(**padrao)
    z = zipfile.ZipFile(io.BytesIO(zip_bytes))
    return z, z.read("index.html").decode("utf-8")


def test_zip_contem_html_e_paginas():
    z, html = _abrir_site()
    nomes = set(z.namelist())
    assert "index.html" in nomes
    assert "paginas/pagina-01.jpg" in nomes
    assert "paginas/pagina-02.jpg" in nomes
    assert "LEIA-ME.txt" in nomes
    assert z.read("paginas/pagina-01.jpg") == JPG_FALSO


def test_html_tem_dados_e_whatsapp():
    _z, html = _abrir_site()
    m = re.search(r"const DADOS = (\{.*?\});\n", html, re.S)
    assert m, "JSON de dados não encontrado no HTML"
    dados = json.loads(m.group(1))
    assert dados["whatsapp"] == "5531999998888"
    assert dados["titulo"] == "UP BABY Verão 26/27"
    assert len(dados["paginas"]) == 2
    codigos = {i["codigo"] for i in dados["itens"]}
    assert codigos == {"1264062", "1264161"}  # o item sem preço ficou de fora
    assert dados["itens"][0]["precos"][0] == {"tamanho": "1/2/3", "valor": 61.90}


def test_html_e_nao_indexavel_e_usa_cor():
    _z, html = _abrir_site()
    assert 'name="robots" content="noindex' in html
    assert "#5B3A5E" in html
    assert "__DADOS__" not in html and "__TITULO__" not in html


def test_whatsapp_invalido_da_erro():
    with pytest.raises(ValueError, match="WhatsApp"):
        _abrir_site(whatsapp="123")


def test_sem_paginas_da_erro():
    with pytest.raises(ValueError, match="páginas"):
        _abrir_site(paginas_jpg=[])
