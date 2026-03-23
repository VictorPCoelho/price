"""
funding_faixas.py
═════════════════
Modelo de funding com faixas de clientes (ex: PF, MEI/EPP, PJ até 300M, PJ acima 300M).
Cada faixa tem: taxa IF % a.a. + taxa FS % a.a. → taxa total do mutuário.
O banco precifica com a taxa total como custo de referência do passivo dessa faixa.
"""

FAIXAS_PADRAO = [
    {"nome": "PF — renda até R$ 500 mil/ano",   "taxa_if_aa": 4.5, "taxa_fs_aa": 2.0, "participacao": 25.0},
    {"nome": "MEI / ME / EPP (LC 123/2006)",     "taxa_if_aa": 4.5, "taxa_fs_aa": 3.0, "participacao": 25.0},
    {"nome": "PJ — ROB até R$ 300 milhões/ano",  "taxa_if_aa": 4.5, "taxa_fs_aa": 4.0, "participacao": 25.0},
    {"nome": "PJ — ROB acima R$ 300 milhões/ano","taxa_if_aa": 4.5, "taxa_fs_aa": 6.0, "participacao": 25.0},
]

def taxa_total_faixa(taxa_if_aa: float, taxa_fs_aa: float) -> float:
    """Taxa total ao mutuário = IF + FS (composição simples conforme norma)."""
    return taxa_if_aa + taxa_fs_aa

def taxa_am_de_aa(taxa_aa: float) -> float:
    """Converte % a.a. para % a.m. equivalente."""
    return ((1 + taxa_aa/100)**(1/12) - 1) * 100

def wacc_faixas(faixas: list) -> dict:
    """
    Calcula o custo médio ponderado (WACC) das faixas.
    Retorna dict com WACC em % a.a. e % a.m.
    """
    soma_part = sum(f["participacao"] for f in faixas)
    if soma_part <= 0:
        return {"wacc_aa": 0.0, "wacc_am": 0.0, "soma_part": 0.0}
    
    wacc_aa = sum(
        taxa_total_faixa(f["taxa_if_aa"], f["taxa_fs_aa"]) * f["participacao"] / soma_part
        for f in faixas
    )
    return {
        "wacc_aa":    round(wacc_aa, 4),
        "wacc_am":    round(taxa_am_de_aa(wacc_aa), 6),
        "soma_part":  round(soma_part, 1),
    }

def resumo_faixas(faixas: list) -> list:
    """Retorna lista de dicts para exibição em tabela."""
    rows = []
    for f in faixas:
        tot = taxa_total_faixa(f["taxa_if_aa"], f["taxa_fs_aa"])
        rows.append({
            "Faixa":           f["nome"],
            "Taxa IF % a.a.":  f["taxa_if_aa"],
            "Taxa FS % a.a.":  f["taxa_fs_aa"],
            "Total % a.a.":    round(tot, 4),
            "Total % a.m.":    round(taxa_am_de_aa(tot), 6),
            "Participação %":  f["participacao"],
        })
    return rows
