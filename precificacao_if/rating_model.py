"""
rating_model.py
═══════════════
Modelo de rating de crédito para precificação por segmento de risco.

Estrutura:
  31 classes: A01-A05, B01-B05, C01-C05, D01-D05, E01-E05, F01-F05, G

Para cada classe:
  - PD  (Probability of Default)  % a.a. — probabilidade de inadimplência
  - LGD (Loss Given Default)       %     — perda dado o default (padrão: 60%)
  - PE  = PD × LGD                 % a.a. — perda esperada anual
  - PE_am = PE convertida para a.m.

O operador edita a tabela de PD por classe via interface ou carrega defaults.
A tabela é passada como dict {rating: pd_pct_aa} para o motor de simulação.
"""

from dataclasses import dataclass, field
from typing import Optional

# ─── Defaults de PD por letra (aproximação mercado BB/BACEN) ─────────────────
# Baseado na Resolução 2.682/99 e práticas de mercado
PD_DEFAULTS_AA = {
    "A01": 0.10, "A02": 0.20, "A03": 0.30, "A04": 0.40, "A05": 0.50,
    "B01": 0.80, "B02": 1.00, "B03": 1.20, "B04": 1.40, "B05": 1.60,
    "C01": 2.00, "C02": 2.50, "C03": 3.00, "C04": 3.50, "C05": 4.00,
    "D01": 5.00, "D02": 6.00, "D03": 7.00, "D04": 8.00, "D05": 9.00,
    "E01": 10.0, "E02": 12.0, "E03": 14.0, "E04": 16.0, "E05": 18.0,
    "F01": 20.0, "F02": 25.0, "F03": 30.0, "F04": 35.0, "F05": 40.0,
    "G":   50.0,
}

LGD_DEFAULT = 60.0  # % — loss given default padrão para PF/PJ sem garantia

# Ordem das classes para exibição
RATINGS_ORDEM = [
    "A01","A02","A03","A04","A05",
    "B01","B02","B03","B04","B05",
    "C01","C02","C03","C04","C05",
    "D01","D02","D03","D04","D05",
    "E01","E02","E03","E04","E05",
    "F01","F02","F03","F04","F05",
    "G",
]

# Cores por letra (para a interface)
CORES_RATING = {
    "A": "#1A5C3A", "B": "#2E5FAB", "C": "#4A1080",
    "D": "#C75B00", "E": "#A31515", "F": "#6B1A1A", "G": "#2C0A0A",
}

BACKCORES_RATING = {
    "A": "#E8F5ED", "B": "#EEF2FA", "C": "#F3EFFE",
    "D": "#FFF3E0", "E": "#FFF0F0", "F": "#FFE8E8", "G": "#FFD9D9",
}


@dataclass
class ClasseRating:
    codigo:  str
    pd_aa:   float       # PD % a.a.
    lgd:     float       # LGD %
    pe_aa:   float = 0.0 # calculado: PD × LGD / 100
    pe_am:   float = 0.0 # PE convertida para a.m.

    def __post_init__(self):
        self.pe_aa = self.pd_aa * self.lgd / 100
        # PE mensal equivalente: (1+PE_aa/100)^(1/12) - 1
        self.pe_am = ((1 + self.pe_aa / 100) ** (1/12) - 1) * 100

    @property
    def letra(self) -> str:
        return self.codigo[0]

    @property
    def cor(self) -> str:
        return CORES_RATING.get(self.letra, "#333333")

    @property
    def bgcor(self) -> str:
        return BACKCORES_RATING.get(self.letra, "#F5F5F5")


def build_tabela(
    pd_dict: dict = None,
    lgd_pct: float = LGD_DEFAULT,
) -> dict:
    """
    Constrói a tabela completa de ratings.

    pd_dict: {codigo: pd_pct_aa} — se None usa defaults
    lgd_pct: LGD uniforme (ou pode ser dict por rating futuramente)

    Retorna: {codigo: ClasseRating}
    """
    base = pd_dict or PD_DEFAULTS_AA
    return {
        cod: ClasseRating(cod, base.get(cod, PD_DEFAULTS_AA[cod]), lgd_pct)
        for cod in RATINGS_ORDEM
    }


# ─── Critérios de viabilidade ─────────────────────────────────────────────────

@dataclass
class CriteriosViabilidade:
    rar_g_min:   float = 8.0    # RAR_G mínimo aceitável (%)
    rsple_min:   float = 6.0    # RSPLE mínimo aceitável (%)
    fla_vp_min:  float = 0.0    # FLA VP deve ser ≥ este valor
    spread_min:  float = 0.0    # Spread total mínimo (R$, opcional)

    def avaliar(self, rs: dict) -> dict:
        """
        Avalia se um resultado de precificação atinge os critérios.
        Retorna dict com cada critério: True/False + status geral.
        """
        rar_ok  = (rs.get("RAR_G % (gestão, F1183)", 0) or 0) >= self.rar_g_min
        rsp_ok  = (rs.get("RSPLE %", 0) or 0) >= self.rsple_min
        fla_ok  = (rs.get("FLA VP (Σ) → 0", -1) or -1) >= self.fla_vp_min
        spr_ok  = (rs.get("Total SP", 0) or 0) >= self.spread_min

        return {
            "rar_ok":  rar_ok,
            "rsple_ok": rsp_ok,
            "fla_ok":  fla_ok,
            "spread_ok": spr_ok,
            "viavel":  rar_ok and rsp_ok and fla_ok and spr_ok,
        }


# ─── Conversão taxa % CDI ─────────────────────────────────────────────────────

def taxa_de_pct_cdi(pct_cdi: float, cdi_am: float) -> float:
    """
    Converte taxa expressa em % do CDI para taxa fixa % a.m.

    Exemplo: 120% CDI com CDI=1,08% a.m. → 1,296% a.m.
    """
    return (pct_cdi / 100) * cdi_am


def pct_cdi_de_taxa(taxa_am: float, cdi_am: float) -> float:
    """
    Converte taxa fixa % a.m. para % do CDI.
    Exemplo: 1,296% a.m. com CDI=1,08% → 120% CDI
    """
    if cdi_am <= 0:
        return 0.0
    return (taxa_am / cdi_am) * 100


# ─── Teste ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    tab = build_tabela()
    print(f"{'Rating':<6}  {'PD % a.a.':>10}  {'PE % a.a.':>10}  {'PE % a.m.':>10}")
    print("─" * 44)
    for cod, cls in tab.items():
        print(f"{cod:<6}  {cls.pd_aa:>10.2f}  {cls.pe_aa:>10.4f}  {cls.pe_am:>10.6f}")

    print()
    print("Conversão % CDI:")
    for pct in [100, 110, 120, 130, 150]:
        tx = taxa_de_pct_cdi(pct, 1.08)
        print(f"  {pct}% CDI (CDI=1,08%) → {tx:.4f}% a.m.")
