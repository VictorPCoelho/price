"""Leitura da tabela de códigos e preços (Excel, CSV ou PDF).

Usada no fluxo de dois arquivos: o catálogo traz as fotos com os códigos
das peças e a tabela separada traz código → preço.
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass

import fitz  # PyMuPDF
import pandas as pd

from .extracao import _PRECO_COM_RS, _PRECO_SEM_RS, _texto_para_valor

_PRECO_QUALQUER = re.compile(
    f"(?:{_PRECO_COM_RS.pattern})|(?:{_PRECO_SEM_RS.pattern})"
)
# Código de produto: token alfanumérico (com . - / opcionais), ex.: 1023, REF-10.23
_CODIGO = re.compile(r"[A-Za-z0-9][A-Za-z0-9./-]{1,19}")


@dataclass
class LinhaTabela:
    codigo: str
    preco: float


def normalizar_codigo(codigo) -> str:
    """Normaliza um código para comparação: só letras/números, maiúsculas.

    "Ref: 10.23" e "ref 1023" viram ambos "1023" / "REF1023" conforme o texto.
    """
    texto = str(codigo).strip()
    # Excel costuma transformar códigos numéricos em float: "1023.0"
    if re.fullmatch(r"\d+\.0", texto):
        texto = texto[:-2]
    return re.sub(r"[^A-Za-z0-9]", "", texto).upper()


def _para_preco(valor) -> float | None:
    """Converte célula de preço (float, "R$ 29,90", "29,90", "29.90")."""
    if valor is None:
        return None
    if isinstance(valor, (int, float)):
        v = float(valor)
        return v if v > 0 else None
    texto = str(valor).strip()
    if not texto:
        return None
    m = _PRECO_QUALQUER.search(texto)
    if m:
        try:
            return _texto_para_valor(m.group(0))
        except ValueError:
            return None
    # formato com ponto decimal (29.90) ou inteiro (30)
    limpo = texto.replace("R$", "").strip()
    try:
        v = float(limpo)
        return v if v > 0 else None
    except ValueError:
        return None


def ler_planilha(dados: bytes, nome_arquivo: str) -> pd.DataFrame:
    """Lê um Excel ou CSV como DataFrame de texto (sem converter tipos)."""
    nome = nome_arquivo.lower()
    if nome.endswith(".csv"):
        return pd.read_csv(io.BytesIO(dados), dtype=str, sep=None, engine="python")
    return pd.read_excel(io.BytesIO(dados), dtype=str)


def adivinhar_colunas(df: pd.DataFrame) -> tuple[str | None, str | None]:
    """Chuta qual coluna é o código e qual é o preço, para pré-selecionar na tela."""
    col_codigo = col_preco = None
    for col in df.columns:
        nome = str(col).lower()
        if col_codigo is None and any(p in nome for p in ("cod", "cód", "ref", "sku", "item")):
            col_codigo = col
        if col_preco is None and any(p in nome for p in ("preço", "preco", "valor", "price", "r$")):
            col_preco = col
    if col_preco is None:  # coluna com mais células que parecem preço
        melhor = 0
        for col in df.columns:
            n = sum(1 for v in df[col].dropna() if _para_preco(v) is not None)
            if n > melhor:
                melhor, col_preco = n, col
    if col_codigo is None:
        candidatas = [c for c in df.columns if c != col_preco]
        if candidatas:
            col_codigo = candidatas[0]
    return col_codigo, col_preco


def extrair_linhas(df: pd.DataFrame, col_codigo: str, col_preco: str) -> tuple[list[LinhaTabela], list[str]]:
    """Extrai (código, preço) das colunas escolhidas. Retorna (linhas, avisos)."""
    linhas: list[LinhaTabela] = []
    avisos: list[str] = []
    vistos: dict[str, float] = {}
    for i, row in df.iterrows():
        bruto_codigo = row.get(col_codigo)
        preco = _para_preco(row.get(col_preco))
        codigo = normalizar_codigo(bruto_codigo) if bruto_codigo is not None else ""
        if not codigo and preco is None:
            continue  # linha vazia
        if not codigo:
            avisos.append(f"Linha {i + 2}: preço sem código — ignorada.")
            continue
        if preco is None:
            avisos.append(f"Linha {i + 2}: código “{bruto_codigo}” sem preço válido — ignorada.")
            continue
        if codigo in vistos:
            if vistos[codigo] != preco:
                avisos.append(
                    f"Código “{bruto_codigo}” aparece mais de uma vez com preços "
                    "diferentes — usando o primeiro."
                )
            continue
        vistos[codigo] = preco
        linhas.append(LinhaTabela(codigo=codigo, preco=preco))
    return linhas, avisos


def ler_tabela_pdf(dados: bytes) -> tuple[list[LinhaTabela], list[str]]:
    """Extrai (código, preço) de uma tabela em PDF, linha a linha.

    Heurística: em cada linha de texto, o último valor monetário é o preço
    e o primeiro token alfanumérico (que não é o próprio preço) é o código.
    """
    doc = fitz.open(stream=dados, filetype="pdf")
    linhas: list[LinhaTabela] = []
    avisos: list[str] = []
    vistos: dict[str, float] = {}
    tinha_texto = False
    for page in doc:
        for linha_texto in page.get_text().splitlines():
            texto = linha_texto.strip()
            if not texto:
                continue
            tinha_texto = True
            precos = list(_PRECO_QUALQUER.finditer(texto))
            if not precos:
                continue
            m_preco = precos[-1]
            try:
                preco = _texto_para_valor(m_preco.group(0))
            except ValueError:
                continue
            codigo = None
            for m_cod in _CODIGO.finditer(texto[: m_preco.start()]):
                token = m_cod.group(0)
                if _PRECO_QUALQUER.fullmatch(token):
                    continue
                codigo = normalizar_codigo(token)
                break
            if not codigo:
                continue
            if codigo in vistos:
                if vistos[codigo] != preco:
                    avisos.append(
                        f"Código “{codigo}” aparece mais de uma vez com preços "
                        "diferentes na tabela — usando o primeiro."
                    )
                continue
            vistos[codigo] = preco
            linhas.append(LinhaTabela(codigo=codigo, preco=preco))
    doc.close()
    if not tinha_texto:
        avisos.append(
            "A tabela em PDF não tem texto legível (provavelmente é imagem "
            "escaneada). Converta para Excel/CSV ou use um PDF com texto."
        )
    return linhas, avisos
