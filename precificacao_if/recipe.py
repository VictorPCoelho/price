"""
recipe.py
═════════
Templates de produto (receitas).  
Cada receita define QUAL fórmula usar em cada slot e os parâmetros globais.

Para adicionar um produto novo:
  1. Copie um template existente como base.
  2. Troque os campos necessários (fórmulas e/ou parâmetros).
  3. Registre em RECEITAS_DISPONIVEIS.
  4. Execute: python main.py --receita NOME_DO_PRODUTO

Estrutura de uma receita:
  {
    "nome":     str,              # identificador único
    "descricao":str,              # texto livre
    "produto":  str,              # família: CDC | CONSIGNADO | IPCA | LEASING
    "params_op":{                 # DADOS DA OPERAÇÃO (B8:B15 da planilha)
        "C":       float,         # Capital financiado
        "T":       int,           # Prazo (períodos)
        "tc":      int,           # Carência
        "i_am":    float,         # Taxa ativa % a.m.
        "PMTA_fixo":float|None,   # Prestação pré-calculada (None = calcular)
        "DU":      int,           # Dias úteis por período
        "cdi_am":  float,         # CDI % a.m.
        "CVSC_aa": float,         # Curva de desconto % a.a.
        "pe_parcela":int|None,    # Parcela da PE (None = sem PE)
        "pe_pct":  float,         # % do capital para PE
    },
    "params_custo":{              # CUSTO DA OPERAÇÃO
        "tarifa_per":  float,     # Tarifa por período
        "tarifa_cont": float,     # Tarifa de contratação (t=0)
        "custo_cont":  float,     # Custo contratação
        "custo_manut": float,     # Custo manutenção/período
        "custo_ag_pct":float,     # Agente de crédito % do capital
        "custo_proc_pct":float,   # Processamento % da PMTA
        "alfa_pc":     float,     # PASEP+COFINS %
        "alfa_iss":    float,     # ISS %
        "alfa_ir_cs":  float,     # IR+CSLL %
    },
    "params_risco":{              # PROVISÃO DE RISCO
        "FPR":         float,     # % ponderação de risco
        "K":           float,     # Capital regulatório %
        "Kp":          float,     # Capital prudencial %
        "F":           float,     # Fator de alavancagem
        "FCC":         float,     # Fator de conversão crédito %
        "fase1_am":    float,     # IPP Fase1 % a.m.
        "usa_fase2":   bool,      # Ativa provisão Fase2
        "fase2_pct":   float,     # Fase2 % capital
        "atu_ipp":     str,       # "oportunidade"|"ativo"|"flat"
    },
    "params_margem":{             # MARGENS
        "lamb_am": float,         # λ margem de ganho % a.m.
    },
    "slots":{                     # FÓRMULAS POR SLOT (modulo.slot → codigo)
        "ativo.EBA":   "z2",
        "ativo.JA":    "z15",     # ← para trocar: "z16" (DU/252) ou "z17" (DC/360)
        "ativo.PMTA":  "price",   # "price" = Price pré-calculada (B15)
        "ativo.SDA":   "z45",
        "passivo.EBP": "ebp_z3",  # CDI pro-rata DU/252
        "passivo.ECP": "z407",    # funding matched
        "fluxo.SP":    "z175",
        "fluxo.MG":    "z182",
        "fluxo.DPE":   "ipp",     # "ipp" = provisão em 2 fases (planilha real)
        "fluxo.PASEP": "z306",
        "fluxo.COFINS":"z311",
        "fluxo.ISS":   "iss_tarifa",
        "fluxo.IR_CS": "z355",
        "iterativo.TIR":  "f1095",
        "iterativo.TPP":  "f1096",
        "iterativo.SPTX": "f1233",
        "performance.RSPLE": "f1064",
        "performance.RAR":   "f1065",
        "performance.RAR_G": "f1183",
    },
  }
"""
import copy


# ─────────────────────────────────────────────────────────────────────────────
# RECEITA 1 — CDC PPS (planilha real)
# ─────────────────────────────────────────────────────────────────────────────
CDC_PPS = {
    "nome":      "CDC_PPS",
    "descricao": "CDC tabela Price com PE e Tarifa — fórmulas z036/z043/z103/z407",
    "produto":   "CDC",
    "params_op": dict(
        C=160_000, T=42, tc=0, i_am=1.43,
        PMTA_fixo=5_094.05, DU=21, cdi_am=1.08, CVSC_aa=13.0,
        pe_parcela=None, pe_pct=0.0,
    ),
    "params_custo": dict(
        tarifa_per=0.0, tarifa_cont=0.0,
        custo_cont=7_512.0, custo_manut=9.0,
        custo_ag_pct=0.0, custo_proc_pct=0.0,
        alfa_pc=4.65, alfa_iss=5.0, alfa_ir_cs=45.0,
    ),
    "params_risco": dict(
        FPR=75.0, K=11.0, Kp=9.75,
        F=10.950, FCC=20.0,
        fase1_am=0.175, usa_fase2=True, fase2_pct=1.5,
        atu_ipp="oportunidade",
    ),
    "params_margem": dict(lamb_am=0.16),
    "slots": {
        "ativo.EBA":       "z2",         # mensal, sem indexador
        "ativo.JA":        "z036",      # flat mensal (z036 planilha)
        "ativo.PMTA":      "price",      # fixo = B15
        "ativo.SDA":       "z45",        # z082
        "passivo.EBP":     "ebp_z3",     # CDI DU/252 (z103)
        "passivo.ECP":     "z407",       # funding matched
        "fluxo.SP":        "z175",
        "fluxo.MG":        "z182",
        "fluxo.DPE":       "ipp",        # 2 fases
        "fluxo.ISS":       "iss_tarifa",
        "fluxo.PASEP":     "z306",
        "fluxo.COFINS":    "z311",
        "fluxo.IR_CS":     "z355",
        "iterativo.TIR":   "f1095",
        "iterativo.TPP":   "f1096",
        "iterativo.SPTX":  "f1233",
        "performance.RSPLE":"f1064",
        "performance.RAR": "f1065",
        "performance.RAR_G":"f1183",
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# RECEITA 2 — Consignado SAC
# ─────────────────────────────────────────────────────────────────────────────
CONSIGNADO_SAC = {
    "nome":      "CONSIGNADO_SAC",
    "descricao": "Crédito consignado SAC. FPR 75%. Sem PE, sem tarifa periódica.",
    "produto":   "CONSIGNADO",
    "params_op": dict(
        C=50_000, T=60, tc=0, i_am=1.45,
        PMTA_fixo=None, DU=21, cdi_am=1.08, CVSC_aa=13.0,
        pe_parcela=None, pe_pct=0.0,
    ),
    "params_custo": dict(
        tarifa_per=0.0, tarifa_cont=0.0,
        custo_cont=0.0, custo_manut=5.0,
        custo_ag_pct=0.0, custo_proc_pct=0.0,
        alfa_pc=4.65, alfa_iss=0.0, alfa_ir_cs=45.0,
    ),
    "params_risco": dict(
        FPR=75.0, K=11.0, Kp=9.75,
        F=10.950, FCC=20.0,
        fase1_am=0.10, usa_fase2=False, fase2_pct=0.0,
        atu_ipp="oportunidade",
    ),
    "params_margem": dict(lamb_am=0.20),
    "slots": {
        "ativo.EBA":       "z2",
        "ativo.JA":        "z15",
        "ativo.PMTA":      "sac",        # SAC = amortização constante
        "ativo.SDA":       "z45",
        "passivo.EBP":     "ebp_z3",
        "passivo.ECP":     "z407",
        "fluxo.SP":        "z175",
        "fluxo.MG":        "z182",
        "fluxo.DPE":       "ipp",
        "fluxo.ISS":       "iss_tarifa",
        "fluxo.PASEP":     "z306",
        "fluxo.COFINS":    "z311",
        "fluxo.IR_CS":     "z355",
        "iterativo.TIR":   "f1095",
        "iterativo.TPP":   "f1096",
        "iterativo.SPTX":  "f1233",
        "performance.RSPLE":"f1064",
        "performance.RAR": "f1065",
        "performance.RAR_G":"f1183",
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# RECEITA 3 — IPCA+ (indexado)
# ─────────────────────────────────────────────────────────────────────────────
IPCA_MAIS = {
    "nome":      "IPCA_MAIS",
    "descricao": "Operação indexada IPCA + spread prefixado. Base DC/360.",
    "produto":   "IPCA",
    "params_op": dict(
        C=200_000, T=24, tc=0, i_am=8.0,   # spread 8% a.a.
        PMTA_fixo=None, DU=21, cdi_am=1.08, CVSC_aa=13.0,
        pe_parcela=None, pe_pct=0.0,
        ind_am=4.5,   # IPCA % a.a. (extra — indexador)
    ),
    "params_custo": dict(
        tarifa_per=0.0, tarifa_cont=500.0,
        custo_cont=0.0, custo_manut=10.0,
        custo_ag_pct=0.0, custo_proc_pct=0.0,
        alfa_pc=4.65, alfa_iss=0.0, alfa_ir_cs=45.0,
    ),
    "params_risco": dict(
        FPR=100.0, K=11.0, Kp=9.75,
        F=10.950, FCC=20.0,
        fase1_am=0.15, usa_fase2=False, fase2_pct=0.0,
        atu_ipp="oportunidade",
    ),
    "params_margem": dict(lamb_am=0.30),
    "slots": {
        "ativo.EBA":       "z3",          # indexador DU/252 (IPCA)
        "ativo.JA":        "z17",         # spread DC/360
        "ativo.PMTA":      "sac",
        "ativo.SDA":       "z45",
        "passivo.EBP":     "ebp_z4",      # passivo DC/360
        "passivo.ECP":     "z407",
        "fluxo.SP":        "z175",
        "fluxo.MG":        "z181",        # MG DC/360
        "fluxo.DPE":       "ipp",
        "fluxo.ISS":       "iss_tarifa",
        "fluxo.PASEP":     "z306",
        "fluxo.COFINS":    "z311",
        "fluxo.IR_CS":     "z355",
        "iterativo.TIR":   "f1095",
        "iterativo.TPP":   "f1096",
        "iterativo.SPTX":  "f1233",
        "performance.RSPLE":"f1064",
        "performance.RAR": "f1065",
        "performance.RAR_G":"f1183",
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# Catálogo de receitas
# ─────────────────────────────────────────────────────────────────────────────
RECEITAS = {
    "CDC_PPS":        CDC_PPS,
    "CONSIGNADO_SAC": CONSIGNADO_SAC,
    "IPCA_MAIS":      IPCA_MAIS,
}


def carregar(nome: str) -> dict:
    if nome not in RECEITAS:
        raise KeyError(f"Receita '{nome}' não existe. Disponíveis: {list(RECEITAS)}")
    return copy.deepcopy(RECEITAS[nome])


def clonar(base: str, alteracoes: dict, novo_nome: str = None) -> dict:
    """
    Clona uma receita e aplica alterações pontuais via dot-notation.

    Exemplos:
        # Troca apenas a fórmula de JA para pro-rata DU/252
        r = clonar("CDC_PPS", {"slots.ativo.JA": "z16"})

        # Ajusta taxa ativa e margem
        r = clonar("CDC_PPS", {
            "params_op.i_am":       1.55,
            "params_margem.lamb_am": 0.20,
        }, novo_nome="CDC_PPS_TAXA_1.55")

        # Troca FPR para consignado
        r = clonar("CDC_PPS", {"params_risco.FPR": 75.0})
    """
    receita = carregar(base)
    if novo_nome:
        receita["nome"] = novo_nome

    for caminho, valor in alteracoes.items():
        # Tenta primeiro como chave composta em "slots" (ex: "slots.ativo.JA")
        if caminho.startswith("slots."):
            chave_slot = caminho[len("slots."):]   # ex: "ativo.JA"
            receita["slots"][chave_slot] = valor
            continue
        # Dot-notation normal para demais seções (ex: "params_op.i_am")
        partes = caminho.split(".")
        obj = receita
        for p in partes[:-1]:
            obj = obj[p]
        obj[partes[-1]] = valor

    return receita


def listar() -> None:
    print("\n  RECEITAS DISPONÍVEIS:")
    print("  " + "─"*50)
    for nome, r in RECEITAS.items():
        p = r["params_op"]
        print(f"  {nome:<20}  {r['descricao'][:50]}")
        print(f"  {'':20}  C={p['C']:,.0f}  T={p['T']}x  i={p['i_am']}%a.m.")
    print()
