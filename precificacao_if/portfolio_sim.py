"""
portfolio_sim.py
════════════════
Simulação de portfolio por faixa de rating.

Lógica:
  Para cada classe de rating, executa o engine com:
    - Mesmos parâmetros de operação (ticket, prazo, carência, etc.)
    - Perda esperada específica da classe (PE_am como fase1_am do IPP)
    - Mesmas fórmulas Z selecionadas

  Produz tabela comparativa e identifica o "fronteira de viabilidade":
  último rating que atende os critérios mínimos (RAR_G, RSPLE, FLA VP).
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from recipe import carregar, clonar
from engine_core import executar
from rating_model import (
    build_tabela, CriteriosViabilidade,
    taxa_de_pct_cdi, pct_cdi_de_taxa,
    RATINGS_ORDEM, CORES_RATING,
)


def simular_portfolio(
    receita_base: dict,
    tabela_rating: dict,         # {codigo: ClasseRating}
    criterios: CriteriosViabilidade,
    ratings_selecionados: list = None,  # None = todos
) -> dict:
    """
    Executa o engine para cada rating e retorna análise completa.

    Retorna:
      "linhas":    list[dict] — resultado por rating
      "fronteira": str        — último rating viável
      "tabela_df": DataFrame  — para exibição
    """
    import pandas as pd

    selecionados = ratings_selecionados or RATINGS_ORDEM
    linhas = []

    for cod in selecionados:
        if cod not in tabela_rating:
            continue

        cls = tabela_rating[cod]

        # Clona a receita e injeta a PE do rating como fase1_am
        rc = clonar(receita_base["nome"] if isinstance(receita_base, dict) and "nome" in receita_base
                    else list(receita_base.keys())[0] if isinstance(receita_base, dict) else "CDC_PPS",
                    {
                        "params_risco.fase1_am": cls.pe_am,
                        "params_op.PMTA_fixo": None,
                    }) if not isinstance(receita_base, dict) or "slots" in receita_base else \
               _clone_direto(receita_base, cls.pe_am)

        try:
            res = executar(rc)
            rs  = res["resumo"]
            av  = criterios.avaliar(rs)

            linhas.append({
                "Rating":     cod,
                "Letra":      cls.letra,
                "PD % a.a.":  cls.pd_aa,
                "PE % a.m.":  round(cls.pe_am, 6),
                "PMTA":       round(rs.get("PMTA Price", 0) or 0, 2),
                "Total SP":   round(rs.get("Total SP", 0) or 0, 2),
                "Total MG":   round(rs.get("Total MG", 0) or 0, 2),
                "Total EPE":  round(rs.get("Total EPE", 0) or 0, 2),
                "FLA VP":     round(rs.get("FLA VP (Σ) → 0", 0) or 0, 4),
                "RSPLE %":    round(rs.get("RSPLE %", 0) or 0, 4),
                "RAR_G %":    round(rs.get("RAR_G % (gestão, F1183)", 0) or 0, 4),
                "SDA final":  round(rs.get("SDA final", 0) or 0, 2),
                "Viável":     av["viavel"],
                "RAR ok":     av["rar_ok"],
                "RSPLE ok":   av["rsple_ok"],
                "FLA ok":     av["fla_ok"],
                "_resumo":    rs,
            })
        except Exception as e:
            linhas.append({
                "Rating": cod, "Letra": cls.letra,
                "PD % a.a.": cls.pd_aa, "Viável": False,
                "Erro": str(e),
            })

    # Fronteira: último rating viável em ordem A01 → G
    fronteira = None
    for linha in linhas:
        if linha.get("Viável"):
            fronteira = linha["Rating"]

    return {
        "linhas": linhas,
        "fronteira": fronteira,
        "n_viaveis": sum(1 for l in linhas if l.get("Viável")),
        "n_total":   len(linhas),
    }


def _clone_direto(receita: dict, pe_am: float) -> dict:
    """Clona receita dict diretamente sem passar por clonar()."""
    import copy
    rc = copy.deepcopy(receita)
    rc["params_risco"]["fase1_am"] = pe_am
    rc["params_op"]["PMTA_fixo"]   = None
    return rc


def simular_portfolio_v2(
    receita_base: dict,
    tabela_rating: dict,
    criterios,
    ratings_selecionados: list = None,
    taxas_por_rating: dict = None,   # {cod: taxa_am}  — None = usa a da receita
    delta_por_rating: dict = None,   # {cod: delta_pp}  — alternativa ao anterior
) -> dict:
    """
    Versão v2: suporta taxa ativa diferente por rating.
    taxas_por_rating: dict {codigo_rating: taxa_am_pct}
    delta_por_rating: dict {codigo_rating: delta_pp_am} — soma à taxa base da receita
    """
    import pandas as pd, copy as _cp

    selecionados = ratings_selecionados or list(tabela_rating.keys())
    taxa_base = receita_base["params_op"]["i_am"]
    linhas = []

    for cod in selecionados:
        if cod not in tabela_rating:
            continue
        cls = tabela_rating[cod]

        # Define taxa ativa para este rating
        if taxas_por_rating and cod in taxas_por_rating:
            taxa_rating = taxas_por_rating[cod]
        elif delta_por_rating and cod in delta_por_rating:
            taxa_rating = taxa_base + delta_por_rating[cod]
        else:
            taxa_rating = taxa_base

        rc = _clone_direto(receita_base, cls.pe_am)
        rc["params_op"]["i_am"] = taxa_rating
        rc["params_op"]["PMTA_fixo"] = None

        try:
            res = executar(rc)
            rs  = res["resumo"]
            av  = criterios.avaliar(rs)
            linhas.append({
                "Rating":     cod,
                "Letra":      cls.letra,
                "Taxa % a.m.": round(taxa_rating, 4),
                "PD % a.a.":  cls.pd_aa,
                "PE % a.m.":  round(cls.pe_am, 6),
                "PMTA":       round(rs.get("PMTA Price",0) or 0, 2),
                "Total SP":   round(rs.get("Total SP",0) or 0, 2),
                "Total MG":   round(rs.get("Total MG",0) or 0, 2),
                "Total EPE":  round(rs.get("Total EPE",0) or 0, 2),
                "FLA VP":     round(rs.get("FLA VP (Σ) → 0",0) or 0, 4),
                "RSPLE %":    round(rs.get("RSPLE %",0) or 0, 4),
                "RAR_G %":    round(rs.get("RAR_G % (gestão, F1183)",0) or 0, 4),
                "SDA final":  round(rs.get("SDA final",0) or 0, 2),
                "Viável":     av["viavel"],
                "_resumo":    rs,
            })
        except Exception as e:
            linhas.append({"Rating":cod,"Letra":cls.letra,"Taxa % a.m.":round(taxa_rating,4),
                           "PD % a.a.":cls.pd_aa,"Viável":False,"Erro":str(e)})

    fronteira = None
    for linha in linhas:
        if linha.get("Viável"):
            fronteira = linha["Rating"]

    return {
        "linhas":    linhas,
        "fronteira": fronteira,
        "n_viaveis": sum(1 for l in linhas if l.get("Viável")),
        "n_total":   len(linhas),
    }
