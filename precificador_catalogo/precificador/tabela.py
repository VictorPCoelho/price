"""Leitura da tabela de códigos e preços (Excel, CSV ou PDF).

Usada no fluxo de dois arquivos: o catálogo traz as fotos com os códigos
das peças e a tabela separada traz código → preço (às vezes um preço por
faixa de tamanho, ex.: "1 a 3", "4 a 8", "10 a 12").
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass, field

import fitz  # PyMuPDF
import pandas as pd

from .extracao import _PRECO_COM_RS, _PRECO_SEM_RS, _texto_para_valor

_PRECO_QUALQUER = re.compile(
    f"(?:{_PRECO_COM_RS.pattern})|(?:{_PRECO_SEM_RS.pattern})"
)
# Código de produto: token alfanumérico (com . - / opcionais), ex.: 1023, REF-10.23
_CODIGO = re.compile(r"[A-Za-z0-9][A-Za-z0-9./-]{1,19}")


@dataclass
class PrecoTamanho:
    """Um preço da tabela, com o rótulo da coluna (faixa de tamanho)."""

    rotulo: str  # ex.: "1 a 3"; vazio quando a tabela tem preço único
    valor: float


@dataclass
class LinhaTabela:
    codigo: str
    precos: list[PrecoTamanho] = field(default_factory=list)
    descricao: str = ""


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


# ------------------------------------------------------------------ planilha
def ler_planilha(dados: bytes, nome_arquivo: str) -> pd.DataFrame:
    """Lê um Excel ou CSV como DataFrame de texto (sem converter tipos)."""
    nome = nome_arquivo.lower()
    if nome.endswith(".csv"):
        return pd.read_csv(io.BytesIO(dados), dtype=str, sep=None, engine="python")
    return pd.read_excel(io.BytesIO(dados), dtype=str)


def adivinhar_colunas(df: pd.DataFrame) -> tuple[str | None, list[str]]:
    """Chuta a coluna do código e as colunas de preço, para pré-selecionar."""
    col_codigo = None
    cols_preco: list[str] = []
    for col in df.columns:
        nome = str(col).lower()
        if col_codigo is None and any(p in nome for p in ("cod", "cód", "ref", "sku", "item")):
            col_codigo = col
        if any(p in nome for p in ("preço", "preco", "valor", "price", "r$")):
            cols_preco.append(col)
    if not cols_preco:  # colunas em que a maioria das células parece preço
        for col in df.columns:
            if col == col_codigo:
                continue
            valores = df[col].dropna()
            if len(valores) and sum(
                1 for v in valores if _para_preco(v) is not None
            ) >= max(1, len(valores) * 0.6):
                cols_preco.append(col)
    if col_codigo is None:
        candidatas = [c for c in df.columns if c not in cols_preco]
        if candidatas:
            col_codigo = candidatas[0]
    return col_codigo, cols_preco


def extrair_linhas(
    df: pd.DataFrame, col_codigo: str, cols_preco: list[str]
) -> tuple[list[LinhaTabela], list[str]]:
    """Extrai as linhas (código → preços) das colunas escolhidas."""
    linhas: list[LinhaTabela] = []
    avisos: list[str] = []
    vistos: set[str] = set()
    varias_colunas = len(cols_preco) > 1
    col_desc = next(
        (c for c in df.columns if "descri" in str(c).lower() and c != col_codigo), None
    )
    for i, row in df.iterrows():
        bruto_codigo = row.get(col_codigo)
        precos = []
        for col in cols_preco:
            v = _para_preco(row.get(col))
            if v is not None:
                precos.append(PrecoTamanho(rotulo=str(col) if varias_colunas else "", valor=v))
        codigo = normalizar_codigo(bruto_codigo) if bruto_codigo is not None else ""
        if not codigo and not precos:
            continue  # linha vazia
        if not codigo:
            avisos.append(f"Linha {i + 2}: preço sem código — ignorada.")
            continue
        if not precos:
            avisos.append(f"Linha {i + 2}: código “{bruto_codigo}” sem preço válido — ignorada.")
            continue
        if codigo in vistos:
            avisos.append(f"Código “{bruto_codigo}” aparece mais de uma vez — usando o primeiro.")
            continue
        vistos.add(codigo)
        descricao = str(row.get(col_desc) or "").strip() if col_desc else ""
        linhas.append(LinhaTabela(codigo=codigo, precos=precos, descricao=descricao))
    return linhas, avisos


# ------------------------------------------------------------------ PDF
def _agrupar_em_linhas(words: list) -> list[list]:
    """Agrupa as palavras do PDF em linhas visuais pela coordenada vertical."""
    if not words:
        return []
    ordenadas = sorted(words, key=lambda w: ((w[1] + w[3]) / 2, w[0]))
    linhas: list[list] = []
    atual: list = []
    y_atual = None
    for w in ordenadas:
        yc = (w[1] + w[3]) / 2
        altura = max(w[3] - w[1], 1.0)
        if y_atual is None or abs(yc - y_atual) <= altura * 0.6:
            atual.append(w)
            y_atual = yc if y_atual is None else (y_atual + yc) / 2
        else:
            linhas.append(sorted(atual, key=lambda x: x[0]))
            atual = [w]
            y_atual = yc
    if atual:
        linhas.append(sorted(atual, key=lambda x: x[0]))
    return linhas


def _colunas_do_cabecalho(linha: list) -> list[tuple[float, str]] | None:
    """Se a linha é um cabeçalho ("Referência ... Descrição ... 1 a 3 ..."),
    retorna as colunas de preço como (centro_x, rótulo)."""
    textos = [w[4].lower() for w in linha]
    if not any(t.startswith(("referê", "refere", "ref.", "cod", "cód")) for t in textos):
        return None
    # palavras que não são "Referência"/"Descrição" formam os rótulos das
    # colunas de preço; agrupa por proximidade horizontal
    restantes = [
        w for w in linha
        if not w[4].lower().startswith(("referê", "refere", "ref.", "cod", "cód", "descri"))
    ]
    if not restantes:
        return None
    # Rótulos de faixa de tamanho vêm como "X a Y" ("1 a 3", "RN a GG",
    # "23-24 A 31-32") ou uma palavra só ("ÚNICO"); palavras muito próximas
    # (< 6pt) também são juntadas num mesmo rótulo.
    grupos: list[list] = []
    i = 0
    while i < len(restantes):
        if i + 2 < len(restantes) and restantes[i + 1][4].lower() == "a":
            grupos.append(restantes[i:i + 3])
            i += 3
            continue
        grupo = [restantes[i]]
        i += 1
        while (
            i < len(restantes)
            and restantes[i][0] - grupo[-1][2] <= 6
            and not (i + 1 < len(restantes) and restantes[i + 1][4].lower() == "a")
        ):
            grupo.append(restantes[i])
            i += 1
        grupos.append(grupo)
    colunas = []
    for g in grupos:
        rotulo = " ".join(w[4] for w in g).strip()
        centro = (g[0][0] + g[-1][2]) / 2
        colunas.append((centro, rotulo))
    return colunas or None


def ler_tabela_pdf(dados: bytes) -> tuple[list[LinhaTabela], list[str]]:
    """Extrai código → preços de uma tabela em PDF.

    Reconstrói as linhas visuais pelas coordenadas das palavras (o texto de
    tabelas costuma vir fora de ordem) e, quando há um cabeçalho com faixas
    de tamanho (ex.: "1 a 3", "4 a 8"), associa cada preço à sua coluna.
    """
    doc = fitz.open(stream=dados, filetype="pdf")
    linhas_saida: list[LinhaTabela] = []
    avisos: list[str] = []
    vistos: set[str] = set()
    tinha_texto = False

    # o cabeçalho com as faixas de tamanho vale até aparecer outro,
    # mesmo que a tabela continue em páginas sem cabeçalho próprio
    colunas: list[tuple[float, str]] | None = None
    for page in doc:
        words = page.get_text("words")
        if words:
            tinha_texto = True
        for linha in _agrupar_em_linhas(words):
            cab = _colunas_do_cabecalho(linha)
            if cab:
                colunas = cab
                continue

            precos_w = []
            codigo = None
            desc_palavras = []
            primeiro_preco_x = None
            for w in linha:
                token = w[4].strip()
                if not token or token == "R$":
                    continue
                # busca (e não fullmatch): em tabelas apertadas o valor pode
                # vir colado no "R$" vizinho, ex.: "79,90R$"
                m_preco = _PRECO_QUALQUER.search(token)
                if m_preco:
                    try:
                        precos_w.append((w, _texto_para_valor(m_preco.group(0))))
                        if primeiro_preco_x is None:
                            primeiro_preco_x = w[0]
                    except ValueError:
                        pass
                    continue
                if codigo is None and _CODIGO.fullmatch(token):
                    codigo = normalizar_codigo(token)
                    continue
                if codigo is not None:
                    desc_palavras.append(token)

            if codigo is None or not precos_w:
                continue

            precos = []
            for w, valor in precos_w:
                rotulo = ""
                if colunas:
                    centro = (w[0] + w[2]) / 2
                    rotulo = min(colunas, key=lambda c: abs(c[0] - centro))[1]
                precos.append(PrecoTamanho(rotulo=rotulo, valor=valor))

            if codigo in vistos:
                avisos.append(f"Código “{codigo}” aparece mais de uma vez na tabela — usando o primeiro.")
                continue
            vistos.add(codigo)
            descricao = " ".join(desc_palavras).strip()
            linhas_saida.append(
                LinhaTabela(codigo=codigo, precos=precos, descricao=descricao)
            )

    doc.close()
    if not tinha_texto:
        avisos.append(
            "A tabela em PDF não tem texto legível (provavelmente é imagem "
            "escaneada). Converta para Excel/CSV ou use um PDF com texto."
        )
    return linhas_saida, avisos
