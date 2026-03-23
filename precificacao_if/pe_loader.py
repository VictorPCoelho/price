"""
pe_loader.py
════════════
Carrega tabela de PD/PE por rating a partir de arquivo Excel ou CSV.

Formato esperado (colunas obrigatórias):
  Rating  |  PD % a.a.
  --------|------------
  A01     |  0.10
  A02     |  0.20
  ...     |  ...
  G       |  50.0

Colunas opcionais que também serão lidas se presentes:
  LGD %  |  PE % a.a.  |  PE % a.m.

Se LGD não estiver no arquivo, usa o valor padrão (60%).
Se PE % a.a. não estiver, calcula como PD × LGD / 100.
"""

import io
import pandas as pd
from rating_model import RATINGS_ORDEM, LGD_DEFAULT, build_tabela


def carregar_pe_arquivo(conteudo_bytes: bytes, nome_arquivo: str) -> dict:
    """
    Lê o arquivo (xlsx ou csv) e retorna dict {codigo: pd_pct_aa}.

    Aceita:
      - xlsx: lê a primeira aba
      - csv:  separador ; ou , detectado automaticamente

    Raises ValueError se o arquivo não tiver a coluna Rating ou PD % a.a.
    """
    nome = nome_arquivo.lower()

    if nome.endswith(".xlsx") or nome.endswith(".xls"):
        df = pd.read_excel(io.BytesIO(conteudo_bytes))
    elif nome.endswith(".csv"):
        # Tenta detectar separador
        amostra = conteudo_bytes[:1024].decode("utf-8", errors="ignore")
        sep = ";" if amostra.count(";") > amostra.count(",") else ","
        df = pd.read_csv(io.BytesIO(conteudo_bytes), sep=sep, decimal=",")
    else:
        raise ValueError(f"Formato não suportado: {nome}. Use .xlsx ou .csv")

    # Normaliza nomes de coluna
    df.columns = [str(c).strip() for c in df.columns]

    # Encontra coluna de Rating (aceita variações)
    col_rating = _find_col(df, ["Rating","rating","RATING","Código","codigo","cod"])
    col_pd     = _find_col(df, ["PD % a.a.","PD%aa","PD_aa","PD","pd_aa","Perda %","PD%"])
    col_lgd    = _find_col(df, ["LGD %","LGD","lgd"], required=False)

    if not col_rating:
        raise ValueError("Coluna 'Rating' não encontrada. Colunas disponíveis: " + str(list(df.columns)))
    if not col_pd:
        raise ValueError("Coluna 'PD % a.a.' não encontrada. Colunas disponíveis: " + str(list(df.columns)))

    resultado = {}
    avisos    = []

    for _, row in df.iterrows():
        cod = str(row[col_rating]).strip().upper()
        if cod not in RATINGS_ORDEM:
            continue  # ignora linhas desconhecidas

        try:
            pd_val = float(str(row[col_pd]).replace(",", "."))
        except (ValueError, TypeError):
            avisos.append(f"Valor inválido para {cod}: {row[col_pd]}")
            continue

        resultado[cod] = pd_val

    # Ratings faltando → usa defaults
    faltando = [r for r in RATINGS_ORDEM if r not in resultado]
    if faltando:
        from rating_model import PD_DEFAULTS_AA
        for r in faltando:
            resultado[r] = PD_DEFAULTS_AA[r]
        avisos.append(f"Ratings não encontrados no arquivo, usando defaults: {faltando[:5]}{'...' if len(faltando)>5 else ''}")

    return resultado, avisos


def _find_col(df: pd.DataFrame, candidatos: list, required: bool = True):
    """Encontra a primeira coluna do DataFrame que bate com algum dos candidatos."""
    for c in candidatos:
        if c in df.columns:
            return c
    # Tenta match parcial
    for c in df.columns:
        for cand in candidatos:
            if cand.lower() in c.lower():
                return c
    if required:
        return None
    return None


def gerar_csv_template() -> bytes:
    """Gera CSV template para download."""
    from rating_model import PD_DEFAULTS_AA, build_tabela
    tab = build_tabela()
    linhas = ["Rating;Letra;PD % a.a.;LGD %;PE % a.a.;PE % a.m."]
    for cod in RATINGS_ORDEM:
        cls = tab[cod]
        linhas.append(
            f"{cod};{cls.letra};{cls.pd_aa:.2f};{cls.lgd:.1f};"
            f"{cls.pe_aa:.4f};{cls.pe_am:.6f}"
        )
    return "\n".join(linhas).encode("utf-8")
