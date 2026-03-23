"""
funding_model.py
════════════════
Modelo de passivo com múltiplos fundings e controle de exigibilidade dos juros.

Conceitos:
  FonteFunding: uma fonte de captação com indexador + spread + participação
  ExigibilidadeJuros: quando os juros se tornam exigíveis (z_J)
  PassivoCompost: soma ponderada dos fundings → custo efetivo do passivo

Integração com o engine:
  - Substitui o parâmetro simples `cdi_am` por um PassivoCompost
  - Cada período t, o custo do passivo é calculado como:
      EBP_t = Σ_q [ participação_q × SDP_{t-1} × taxa_periodo_q(DU_{t-1}, DU_t) ]
  - Se curvas DIFIN estão carregadas, usa taxa forward da curva
  - Caso contrário, usa a taxa manual (% a.m. informado pelo operador)
"""

from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from curve_parser import CurvaDIFIN


# ─────────────────────────────────────────────────────────────────────────────
# Tipos de indexador disponíveis
# ─────────────────────────────────────────────────────────────────────────────
INDEXADORES = {
    "CDI-PSC":   {"tipo_curva": 1,    "descricao": "CDI (curva PSC) — funding principal"},
    "CDI-PCC":   {"tipo_curva": 2,    "descricao": "CDI (curva PCC) — crédito privado"},
    "TR":        {"tipo_curva": 3,    "descricao": "TR — Taxa Referencial"},
    "TJLP":      {"tipo_curva": 4,    "descricao": "TJLP — Taxa Juros Longo Prazo"},
    "IPCA":      {"tipo_curva": 9,    "descricao": "IPCA — inflação"},
    "PREFIXADO": {"tipo_curva": None, "descricao": "Prefixado — taxa fixa independente de curva"},
}

# ─────────────────────────────────────────────────────────────────────────────
# Exigibilidade dos juros (quando EJA / EJP vira exigível)
# ─────────────────────────────────────────────────────────────────────────────
OPCOES_EXIGIBILIDADE = {
    "mensal":        {"z_J": 1,   "descricao": "Integral mensal — juros pagos todo período (padrão CDC)"},
    "bimestral":     {"z_J": 2,   "descricao": "Bimestral — acumula 2 períodos e paga"},
    "trimestral":    {"z_J": 3,   "descricao": "Trimestral — acumula 3 períodos e paga"},
    "semestral":     {"z_J": 6,   "descricao": "Semestral — acumula 6 períodos e paga"},
    "anual":         {"z_J": 12,  "descricao": "Anual — acumula 12 períodos e paga"},
    "bullet":        {"z_J": None,"descricao": "Bullet — juros só exigíveis no vencimento T"},
    "proporcional":  {"z_J": -1,  "descricao": "Proporcional à amortização — paga junto com o capital"},
}


@dataclass
class FonteFunding:
    """Uma fonte de captação do passivo."""
    nome:           str
    indexador:      str        # chave de INDEXADORES
    spread_pp_am:   float      # spread adicional em pp a.m. (ex: 0.02 = 0,02 pp a.m.)
    participacao:   float      # 0.0 a 1.0 (soma de todas deve ser 1.0)
    taxa_manual_am: float      # taxa manual % a.m. (usada se curva não disponível)
    # Exigibilidade específica desta fonte (None = usa a do produto)
    exig_override:  Optional[str] = None

    def custo_periodo(
        self,
        saldo: float,
        du_ini: int,
        du_fim: int,
        curvas: Optional[dict] = None,
    ) -> float:
        """
        Calcula EBP desta fonte para o período [du_ini, du_fim].

        Lógica:
          1. Se curva disponível para este indexador → usa taxa forward da curva
          2. Caso contrário → usa taxa_manual_am como taxa flat do período
          3. Soma o spread

        Retorna EBP (valor positivo = custo do banco).
        """
        tipo_curva = INDEXADORES[self.indexador]["tipo_curva"]
        du_delta   = du_fim - du_ini
        if du_delta <= 0:
            return 0.0

        # Tenta usar a curva
        if curvas and tipo_curva and tipo_curva in curvas:
            curva = curvas[tipo_curva]
            taxa_periodo = curva.taxa_periodo_du(du_ini, du_fim)  # decimal
        else:
            # Fallback: taxa manual flat
            taxa_periodo = (1 + self.taxa_manual_am / 100) ** (du_delta / 21) - 1

        # Adiciona spread em pp a.m. (convertido para o período)
        spread_periodo = (1 + self.spread_pp_am / 100) ** (du_delta / 21) - 1

        taxa_total = (1 + taxa_periodo) * (1 + spread_periodo) - 1
        return saldo * taxa_total


@dataclass
class PassivoComposto:
    """Conjunto de fontes de funding com exigibilidade configurável."""
    fontes:           list             # List[FonteFunding]
    exig_juros:       str = "mensal"   # chave de OPCOES_EXIGIBILIDADE
    exig_juros_ativo: str = "mensal"   # exigibilidade dos juros do ativo (EJA)

    def validar(self) -> list:
        """Retorna lista de erros de validação."""
        erros = []
        total_part = sum(f.participacao for f in self.fontes)
        if abs(total_part - 1.0) > 0.001:
            erros.append(f"Soma das participações = {total_part:.4f} (deve ser 1,0)")
        for f in self.fontes:
            if f.indexador not in INDEXADORES:
                erros.append(f"Indexador '{f.indexador}' inválido em '{f.nome}'")
            if not (0 < f.participacao <= 1.0):
                erros.append(f"Participação inválida em '{f.nome}': {f.participacao}")
        return erros

    def ebp_total(
        self,
        saldo: float,
        du_ini: int,
        du_fim: int,
        curvas: Optional[dict] = None,
    ) -> float:
        """EBP total = soma ponderada dos custos de cada fonte."""
        return sum(
            f.custo_periodo(saldo * f.participacao, du_ini, du_fim, curvas)
            for f in self.fontes
        )

    def taxa_efetiva_am(
        self,
        du_ini: int = 0,
        du_fim: int = 21,
        curvas: Optional[dict] = None,
        saldo_ref: float = 100.0,
    ) -> float:
        """Taxa efetiva mensal do passivo composto (% a.m.) para referência."""
        ebp = self.ebp_total(saldo_ref, du_ini, du_fim, curvas)
        return ebp / saldo_ref * 100

    def z_J(self) -> Optional[int]:
        """Retorna o z_J (periodicidade de exigibilidade) configurado."""
        return OPCOES_EXIGIBILIDADE[self.exig_juros]["z_J"]

    def z_J_ativo(self) -> Optional[int]:
        """Retorna z_J para o ativo (EJA)."""
        return OPCOES_EXIGIBILIDADE[self.exig_juros_ativo]["z_J"]

    def resumo(self, curvas: Optional[dict] = None) -> dict:
        """Resumo das fontes e custo efetivo."""
        return {
            "fontes": [
                {
                    "nome":       f.nome,
                    "indexador":  f.indexador,
                    "spread_am":  f.spread_pp_am,
                    "participacao": f.participacao,
                    "custo_am":   f.custo_periodo(100.0 * f.participacao, 0, 21, curvas),
                }
                for f in self.fontes
            ],
            "exig_juros":  self.exig_juros,
            "exig_ativo":  self.exig_juros_ativo,
            "taxa_efetiva_am": self.taxa_efetiva_am(curvas=curvas),
        }


# ─────────────────────────────────────────────────────────────────────────────
# Helpers de construção rápida
# ─────────────────────────────────────────────────────────────────────────────

def passivo_simples(cdi_am: float, exig: str = "mensal") -> PassivoComposto:
    """Passivo com fonte única CDI-PSC (simplificado, sem curvas)."""
    return PassivoComposto(
        fontes=[FonteFunding(
            nome="CDI-PSC (100%)",
            indexador="CDI-PSC",
            spread_pp_am=0.0,
            participacao=1.0,
            taxa_manual_am=cdi_am,
        )],
        exig_juros=exig,
    )


def passivo_mix_exemplo() -> PassivoComposto:
    """Exemplo de mix: 60% CDI-PSC + 25% CDI-PCC + 15% TJLP."""
    return PassivoComposto(
        fontes=[
            FonteFunding("CDB 100% CDI",     "CDI-PSC",  0.0,  0.60, 1.08),
            FonteFunding("LCA 90% CDI",      "CDI-PSC", -0.108*0.10, 0.25, 0.972),
            FonteFunding("TJLP + 0pp",       "TJLP",     0.0,  0.15, 0.544),
        ],
        exig_juros="mensal",
    )


# ─── Teste ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    p = passivo_simples(1.08)
    print("Passivo simples CDI 1,08% a.m.:")
    print(f"  EBP (R$100, DU0→21) = {p.ebp_total(100, 0, 21):.6f}")
    print(f"  Taxa efetiva a.m.   = {p.taxa_efetiva_am():.6f}%")
    print()

    mix = passivo_mix_exemplo()
    erros = mix.validar()
    print("Passivo mix (60%CDB + 25%LCA + 15%TJLP):")
    print(f"  Validação: {'OK' if not erros else erros}")
    for f in mix.fontes:
        ebp = f.custo_periodo(100 * f.participacao, 0, 21)
        print(f"  {f.nome:<25} part={f.participacao:.0%}  EBP={ebp:.6f}  custo_am={ebp/(100*f.participacao)*100:.6f}%")
    print(f"  Taxa WACC efetiva:  {mix.taxa_efetiva_am():.6f}% a.m.")

    print()
    print("Opções de exigibilidade disponíveis:")
    for k, v in OPCOES_EXIGIBILIDADE.items():
        print(f"  {k:<14}  z_J={str(v['z_J']):<5}  {v['descricao']}")
