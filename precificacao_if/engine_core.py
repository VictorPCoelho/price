"""
engine_core.py
══════════════
Motor de precificação dinâmico.

Lê uma receita, despacha a fórmula Z/F correta por slot em cada período
t = 0..T e devolve o fluxo completo + indicadores de performance.

Fluxo de execução por período:
  ① EBA / EBP  → encargos básicos do indexador
  ② JA  / JP   → juros ativo/passivo
  ③ PMTA/ECA/SDA → prestação e saldo do ativo
  ④ ECP / SCP / PMTP / SDP → passivo
  ⑤ SP         → spread
  ⑥ Provisão IPP/PE (2 fases)
  ⑦ MG / MC    → margens
  ⑧ Tarifas + ISS
  ⑨ PASEP / COFINS / BFB / IR+CSLL
  ⑩ FLA / FLA_VP
  ⑪ Totalizadores VP → indicadores iterativos (TIR, TPP, SPTX)
  ⑫ Performance (RSPLE, RAR, RAR_G, IE, IR, IRE, Duration)
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "modulos"))

import pandas as pd
from formula_registry import get_fn, REGISTRY
from metodos_iterativos import ModuloMetodosIterativos as Solver
from performance        import ModuloPerformance      as Perf


# ─── Utilitários ─────────────────────────────────────────────────────────────

def _vp(val: float, t: int, CVSC: float, DU: int) -> float:
    if t == 0: return val
    return val / (1 + CVSC) ** (t * DU / 252)

def _pmta_price(C: float, i: float, T: int, PE_valor: float = 0.0) -> float:
    """PMT Price ajustada para balloon PE."""
    if i <= 0: return C / T
    pv_pe = PE_valor / (1 + i) ** T if PE_valor else 0.0
    return (C - pv_pe) * i / (1 - (1 + i) ** -T)

def _pmta_sac(C: float, T: int) -> float:
    """Amortização constante (gerada pelo engine a cada período)."""
    return C / T


# ─── Engine principal ─────────────────────────────────────────────────────────

def executar(receita: dict) -> dict:
    """
    Executa o fluxo financeiro completo a partir de uma receita.

    Retorna:
      "fluxo":       DataFrame (linha = período, coluna = variável Z)
      "resumo":      dict com totais e indicadores
      "receita":     receita usada (para rastreabilidade)
    """
    op   = receita["params_op"]
    cst  = receita["params_custo"]
    rsc  = receita["params_risco"]
    mgm  = receita["params_margem"]
    slts = receita["slots"]

    # ── Parâmetros operacionais ───────────────────────────────────────────────
    C       = op["C"];       T    = op["T"];     tc   = op.get("tc", 0)
    i       = op["i_am"] / 100
    cdi     = op["cdi_am"] / 100
    DU      = op.get("DU", 21)
    DC      = op.get("DC", 30)
    CVSC    = op["CVSC_aa"] / 100
    n       = 12.0
    pe_parc = op.get("pe_parcela")
    PE_val  = C * op.get("pe_pct", 0.0) if pe_parc else 0.0
    ind_am  = op.get("ind_am", 0.0) / 100   # indexador (IPCA etc.)

    # PMTA Price pré-calculada (B15)
    PMTA_fixo = op.get("PMTA_fixo")
    if PMTA_fixo is not None:
        PMTA_price = abs(PMTA_fixo)
    elif slts.get("ativo.PMTA") == "price":
        PMTA_price = _pmta_price(C, i, T, PE_val)
    else:
        PMTA_price = None   # SAC ou bullet calculam no loop

    # ── Parâmetros de risco / capital ─────────────────────────────────────────
    FPR      = rsc["FPR"]   / 100
    K        = rsc["K"]     / 100
    Kp       = rsc["Kp"]    / 100
    F        = rsc["F"]
    FCC      = rsc["FCC"]   / 100
    fase1_am = rsc["fase1_am"] / 100
    usa_f2   = rsc.get("usa_fase2", False)
    fase2_pct= rsc.get("fase2_pct", 0.0) / 100
    atu_ipp  = rsc.get("atu_ipp", "oportunidade")
    CE       = C * FPR * K
    CEIRB    = C * FPR * Kp
    lamb     = mgm["lamb_am"] / 100

    # ── Custos ────────────────────────────────────────────────────────────────
    alfa_pc    = cst["alfa_pc"]    / 100
    alfa_iss   = cst["alfa_iss"]   / 100
    alfa_ir_cs = cst["alfa_ir_cs"] / 100
    custo_cont = cst.get("custo_cont", 0.0)
    custo_mnt  = cst.get("custo_manut", 0.0)
    custo_ag   = cst.get("custo_ag_pct", 0.0) / 100 * C
    custo_proc = cst.get("custo_proc_pct", 0.0) / 100
    tarifa_per = cst.get("tarifa_per", 0.0)
    tarifa_cont= cst.get("tarifa_cont", 0.0)

    # ── Provisão Fase 2 (flat em t=0) ────────────────────────────────────────
    fase2_t0_abs = C * fase2_pct if usa_f2 else 0.0

    # ── Estado entre períodos ─────────────────────────────────────────────────
    SDA_prev = C;  SJA_prev = 0.0;  SCA_prev = C
    SEBP_prev= 0.0; SCP_prev= C;   SDP_prev = C
    SIPP_prev= 0.0; MG_prev = 0.0

    linhas = []

    for t in range(0, T + 1):

        # ─── ATIVO ────────────────────────────────────────────────────────────

        LCA  = C if t == 0 else 0.0

        # EBA (indexador ativo) — z2, z3
        slot_eba = slts.get("ativo.EBA", "z2")
        if t == 0 or (t <= tc):
            EBA = 0.0
        else:
            if slot_eba == "z2":
                EBA = SDA_prev * (((1 + ind_am) ** (1/n)) - 1)
            elif slot_eba == "z3":
                EBA = SDA_prev * ((1 + ind_am) ** (DU / 252) - 1)
            else:
                EBA = SDA_prev * (ind_am / 100)

        # JA (juros ativo) — z15, z16, z17
        slot_ja = slts.get("ativo.JA", "z15")
        if t == 0:
            JA = 0.0
        else:
            if slot_ja == "z036":          # flat mensal (planilha CDC PPS)
                JA = SDA_prev * i          # JA = SDA * i_mensal (z036)
            elif slot_ja == "z15":         # equivalente — converte taxa de período
                JA = SDA_prev * ((1 + i) ** (1/n) - 1)
            elif slot_ja == "z16":         # pro-rata DU/252
                JA = SDA_prev * ((1 + i) ** (DU / 252) - 1)
            elif slot_ja == "z17":         # pro-rata DC/360
                JA = SDA_prev * ((1 + i) ** (DC / 360) - 1)
            else:
                JA = SDA_prev * i

        # EJA — exigibilidade dos juros do ativo
        # pagar_carencia: True=juros exigíveis durante carência | False=capitaliza (padrão)
        # z_J: 1=mensal | None=bullet | -1=proporcional | Z=periódico cada Z meses
        pagar_car = op.get("pagar_juros_carencia", False)
        z_J       = op.get("z_J_ativo", 1)

        if t == 0:
            EJA = 0.0
        elif t <= tc:
            EJA = (-JA) if pagar_car else 0.0          # carência: paga corrente ou capitaliza
        elif z_J is None:                               # bullet
            EJA = (-JA - SJA_prev) if t == T else 0.0
        elif z_J == -1:                                 # proporcional
            EJA = -JA - SJA_prev
        elif z_J >= 1 and t % z_J == 0:               # periódico
            EJA = -JA - SJA_prev
        else:
            EJA = -JA - SJA_prev                       # mensal (default)

        SJA = 0.0 if t == 0 else SJA_prev + JA + EJA

        # PMTA (prestação) — price, sac, bullet
        PE_t = -PE_val if (pe_parc and t == pe_parc) else 0.0
        slot_pmta = slts.get("ativo.PMTA", "price")
        if t == 0 or t <= tc:
            PMTA_base = 0.0
        elif slot_pmta == "price" and PMTA_price:
            PMTA_base = -PMTA_price
        elif slot_pmta == "sac":
            PMTA_base = -(C / T) - JA - EBA
        elif slot_pmta == "bullet":
            PMTA_base = -(SDA_prev + JA + EBA) if t == T else 0.0
        else:
            PMTA_base = -PMTA_price if PMTA_price else -(C * i / (1-(1+i)**-T))
        PMTA = PMTA_base + PE_t

        # ECA e SDA
        ECA = 0.0 if (t == 0 or t <= tc) else (PMTA - EJA)
        SCA = LCA if t == 0 else SCA_prev + ECA + LCA
        SDA = LCA if t == 0 else SDA_prev + LCA + JA + PMTA

        # ─── PASSIVO ──────────────────────────────────────────────────────────

        LCP = C if t == 0 else 0.0

        # EBP (encargo básico passivo) — ebp_z2, ebp_z3, ebp_z4
        slot_ebp = slts.get("passivo.EBP", "ebp_z3")
        if t == 0:
            EBP = 0.0
        elif slot_ebp == "ebp_z2":
            EBP = SDP_prev * ((1 + cdi) ** (1/n) - 1)
        elif slot_ebp == "ebp_z3":
            EBP = SDP_prev * ((1 + cdi) ** (DU / 252) - 1)
        elif slot_ebp == "ebp_z4":
            EBP = SDP_prev * ((1 + cdi) ** (DC / 360) - 1)
        else:
            EBP = SDP_prev * cdi

        EEBP = 0.0 if (t == 0 or t <= tc) else (-SEBP_prev - EBP)
        SEBP = 0.0 if t == 0 else SEBP_prev + EBP + EEBP

        # ECP (exigibilidade capital passivo)
        slot_ecp = slts.get("passivo.ECP", "z407")
        if t == 0:
            ECP = 0.0
        elif slot_ecp == "z407":
            ECP = PMTA - EJA        # funding matched
        elif slot_ecp == "ecp_z65":
            n_rest = max((T - t) / 1 + 1, 1)
            ECP = SCP_prev / n_rest
        elif slot_ecp == "ecp_z68":
            ECP = SCP_prev if t == T else 0.0
        else:
            ECP = PMTA - EJA

        SCP  = LCP if t == 0 else SCP_prev - ECP + LCA
        PMTP = 0.0 if t == 0 else (EEBP + ECP)
        SDP  = LCP if t == 0 else SDP_prev + LCP + EBP + PMTP

        # ─── SPREAD ───────────────────────────────────────────────────────────

        slot_sp = slts.get("fluxo.SP", "z175")
        SP = 0.0 if t == 0 else (-PMTA + PMTP)

        # ─── PROVISÃO IPP/PE ──────────────────────────────────────────────────

        slot_dpe = slts.get("fluxo.DPE", "ipp")
        DPE  = -fase2_t0_abs if t == 0 else 0.0
        IPP1 = 0.0 if t == 0 else -(SDA_prev * fase1_am)

        SDA_base = SDA_prev + JA if t > 0 else C
        if t > 0 and SDA_base != 0:
            saldo_ipp = fase2_t0_abs + SIPP_prev
            if atu_ipp == "oportunidade":
                saldo_upd = saldo_ipp * (1 + cdi) ** (DU / 252)
            elif atu_ipp == "ativo":
                saldo_upd = saldo_ipp * (1 + i)
            else:
                saldo_upd = saldo_ipp
            EPE = -(saldo_upd * abs(PMTA) / SDA_base)
        else:
            EPE = 0.0
        SIPP = (fase2_t0_abs if t == 0 else SIPP_prev) + abs(IPP1)

        # ─── MARGENS ──────────────────────────────────────────────────────────

        slot_mg = slts.get("fluxo.MG", "z182")
        if t == 0:
            MG = 0.0
        else:
            base_mg = SDA_prev + JA
            if slot_mg == "z182":
                MG = base_mg * ((1 + lamb) ** (1/n) - 1)
            elif slot_mg == "z180":
                MG = base_mg * ((1 + lamb) ** (DU / 252) - 1)
            elif slot_mg == "z181":
                MG = base_mg * ((1 + lamb) ** (DC / 360) - 1)
            elif slot_mg == "z393":
                MG = base_mg * ((1 + lamb) ** (DU / 252) - 1)
            elif slot_mg == "z441":
                MG = base_mg * ((1 + lamb) ** (1/12) - 1)
            else:
                MG = base_mg * ((1 + lamb) ** (1/n) - 1)

        MG_fla = MG_prev   # MG deslocada (AH no FLA original)

        # MC (margem de contribuição)
        MC = 0.0 if t == 0 else (SP + EPE + IPP1)

        # ─── TARIFAS E TRIBUTAÇÃO ─────────────────────────────────────────────

        tarifa_t = tarifa_per if (t > 0 and t <= T) else 0.0

        BFA         = 0.0 if t == 0 else (JA - EBP)
        pasep_cof   = 0.0 if t == 0 else (-BFA * alfa_pc)
        iss_t       = 0.0 if t == 0 else (-tarifa_t * alfa_iss)

        # Custos fixos e variáveis
        z394  = -custo_cont  if t == 0 else 0.0
        z230  = -custo_mnt   if t > 0 else 0.0
        f1046 = -custo_ag    if t == 0 else 0.0
        z236  = PMTA * custo_proc if t > 0 else 0.0
        f1044 = z394 + z230 + f1046 + z236

        # Base fiscal B
        BFB = 0.0 if t == 0 else (
            JA - EBP + tarifa_t + f1044 + EPE + IPP1 + pasep_cof + iss_t
        )
        ir_cs = 0.0 if t == 0 else (-BFB * alfa_ir_cs)

        # ─── FLUXO DE CAIXA ───────────────────────────────────────────────────

        if t == 0:
            FLA = z394 + f1046 + DPE
        else:
            FLA = SP + tarifa_t + f1044 + EPE + IPP1 + pasep_cof + iss_t + ir_cs - MG_fla

        FLA_VP = _vp(FLA, t, CVSC, DU)
        FLC    = PMTA  if t > 0 else 0.0
        FLE    = PMTP  if t > 0 else 0.0

        # ─── Salva linha ──────────────────────────────────────────────────────
        linhas.append({
            "t":t, "LCA":LCA, "JA":JA, "EJA":EJA, "SJA":SJA,
            "EBA":EBA, "ECA":ECA, "SCA":SCA, "PMTA":PMTA, "PE":PE_t, "SDA":SDA,
            "LCP":LCP, "EBP":EBP, "EEBP":EEBP, "SEBP":SEBP,
            "ECP":ECP, "SCP":SCP, "PMTP":PMTP, "SDP":SDP,
            "SP":SP, "tarifa":tarifa_t,
            "BFA":BFA, "pasep_cof":pasep_cof, "iss":iss_t,
            "DPE":DPE, "IPP1":IPP1, "EPE":EPE, "SIPP":SIPP,
            "MG":MG, "MG_fla":MG_fla, "MC":MC,
            "z394":z394, "z230":z230, "f1046":f1046, "z236":z236, "f1044":f1044,
            "BFB":BFB, "ir_cs":ir_cs, "FLA":FLA, "FLA_VP":FLA_VP, "FLC":FLC, "FLE":FLE,
        })

        # Atualiza estado
        SDA_prev=SDA; SJA_prev=SJA; SCA_prev=SCA
        SEBP_prev=SEBP; SCP_prev=SCP; SDP_prev=SDP
        SIPP_prev=SIPP; MG_prev=MG

    df = pd.DataFrame(linhas)
    rows = df[df.t > 0]

    # ─── Totalizadores VP ─────────────────────────────────────────────────────
    def sv(col):
        return sum(_vp(r[col], r["t"], CVSC, DU) for _, r in rows.iterrows())

    SPVP = sv("SP"); MGVP = sv("MG"); EPEVP = sv("EPE")
    CFVP = sv("f1044")
    FLA_VP_soma = round(df["FLA_VP"].sum(), 6)

    # ─── Métodos iterativos ───────────────────────────────────────────────────
    ECA_tot = C
    FLC_tot = rows["FLC"].abs().sum()
    FLE_tot = rows["FLE"].abs().sum()
    dct_tot = T * 30

    def _solve(fn_obj, fl_key, fl_val, chute="chute_tir"):
        try:
            return Solver.solver_secante(
                fn_obj, {fl_key: fl_val, "ECA_t": ECA_tot, "dct": dct_tot},
                chute, 0.1, 5.0,
            )
        except Exception:
            return None

    tir  = _solve(Perf.funcao_objetivo_tir_f1095, "FLD_t", FLC_tot, "chute_tir")
    tpp  = _solve(Perf.funcao_objetivo_tpp_f1096, "FLE_t", FLE_tot, "chute_tpp")

    # ─── Performance ──────────────────────────────────────────────────────────
    lamb_aa = (1 + lamb) ** 12 - 1

    # RSPLE e RAR_G usam λ como TAXA ANUAL (não R$)
    denom_rsple = FPR * K  * (1 + (F - 1) * FCC)
    denom_rarg  = FPR * Kp * (1 + (F - 1) * FCC)
    RSPLE = lamb_aa / denom_rsple * 100 if denom_rsple else 0
    RAR_G = lamb_aa / denom_rarg  * 100 if denom_rarg  else 0

    # RAR base: MGVP / CE
    RAR   = MGVP / CE * 100 if CE else 0

    # Outros índices
    IE    = Perf.indice_eficiencia_ie_f1066(abs(CFVP), SPVP) if SPVP else 0
    IR_r  = Perf.indice_risco_ir_f1067(EPEVP, SPVP) if SPVP else 0
    IRE   = Perf.indice_rentabilidade_ire_f1068(MGVP, SPVP) if SPVP else 0

    dur_n = sum(df.loc[df.t>0,"t"] * df.loc[df.t>0,"FLA_VP"])
    dur_d = df.loc[df.t>0,"FLA_VP"].abs().sum()
    DRT   = Perf.duration_drt_f1204(dur_n, dur_d) if dur_d else 0

    def aa(taxa_am_pct):
        if taxa_am_pct is None: return None
        return round(((1 + taxa_am_pct/100)**(360/30) - 1)*100, 4)

    resumo = {
        # Operação
        "receita":                 receita["nome"],
        "produto":                 receita["produto"],
        "Capital (C)":             C,
        "Prazo (T)":               T,
        "Taxa ativa % a.m.":       round(i*100, 4),
        "CDI % a.m.":              round(cdi*100, 4),
        "λ Margem % a.m.":         round(lamb*100, 4),
        "λ Margem % a.a.":         round(lamb_aa*100, 4),
        "PMTA Price":              round(PMTA_price, 4) if PMTA_price else None,
        # Capital / risco
        "FPR":                     f"{FPR*100:.0f}%",
        "K regulatório":           f"{K*100:.2f}%",
        "K prudencial (Kp)":       f"{Kp*100:.2f}%",
        "F / FCC":                 f"{F} / {FCC*100:.0f}%",
        "CE regulatório":          round(CE, 2),
        "CEIRB (gestão)":          round(CEIRB, 2),
        # Fórmulas usadas
        "fórmula EBA":             slts.get("ativo.EBA"),
        "fórmula JA":              slts.get("ativo.JA"),
        "fórmula PMTA":            slts.get("ativo.PMTA"),
        "fórmula EBP":             slts.get("passivo.EBP"),
        "fórmula ECP":             slts.get("passivo.ECP"),
        "fórmula MG":              slts.get("fluxo.MG"),
        # Fluxo acumulado
        "Total PMTA":              round(rows["PMTA"].abs().sum(), 2),
        "Total JA":                round(rows["JA"].sum(), 2),
        "SDA final":               round(df.loc[df.t==T,"SDA"].values[0], 2),
        "Total EBP (CDI)":         round(rows["EBP"].sum(), 2),
        "SDP final":               round(df.loc[df.t==T,"SDP"].values[0], 2),
        "Total SP":                round(rows["SP"].sum(), 2),
        "Total MG":                round(rows["MG"].sum(), 2),
        "Total IPP Fase1":         round(rows["IPP1"].abs().sum(), 2),
        "Total EPE":               round(rows["EPE"].abs().sum(), 2),
        "Total PASEP+COF":         round(rows["pasep_cof"].abs().sum(), 2),
        "Total ISS":               round(rows["iss"].abs().sum(), 2),
        "Total IR/CS":             round(rows["ir_cs"].abs().sum(), 2),
        "Total Custos":            round(rows["f1044"].abs().sum(), 2),
        "FLA VP (Σ) → 0":          round(FLA_VP_soma, 4),
        # Performance
        "MG % a.m.":               round(lamb*100, 4),
        "MG % a.a.":               round(lamb_aa*100, 4),
        "RSPLE %":                 round(RSPLE, 4),
        "RAR_G % (gestão, F1183)": round(RAR_G, 4),
        "RAR % (base)":            round(RAR, 4),
        "IE (eficiência)":         round(IE, 4),
        "IR (risco)":              round(IR_r, 4),
        "IRE (rentabilidade)":     round(IRE, 4),
        "Duration (meses)":        round(DRT, 2),
        "TIR % a.a.":              aa(tir),
        "Resultado PPS % a.m.":    round(tpp, 4) if tpp else None,
        "SPVP":                    round(SPVP, 2),
        "MGVP (λ_mg)":             round(MGVP, 2),
        "EPEVP":                   round(EPEVP, 2),
    }

    return {"fluxo": df, "resumo": resumo, "receita": receita}


# ─────────────────────────────────────────────────────────────────────────────
# executar_v2: engine com PassivoComposto + curvas DIFIN + exigibilidade
# ─────────────────────────────────────────────────────────────────────────────

def executar_v2(receita: dict,
                passivo_composto=None,
                curvas: dict = None) -> dict:
    """
    Versão estendida do engine com:
      - PassivoComposto: múltiplos fundings com indexadores e exigibilidade
      - curvas DIFIN: taxa forward por período (EBP, EBA, CVSC)
      - exigibilidade dos juros (z_J): mensal, semestral, bullet etc.

    Se passivo_composto=None, delega para executar() (comportamento original).
    """
    if passivo_composto is None:
        return executar(receita)

    from funding_model import PassivoComposto, OPCOES_EXIGIBILIDADE

    op   = receita["params_op"]
    cst  = receita["params_custo"]
    rsc  = receita["params_risco"]
    mgm  = receita["params_margem"]
    slts = receita["slots"]

    C    = op["C"];    T    = op["T"];  tc = op.get("tc", 0)
    i    = op["i_am"] / 100
    DU   = op.get("DU", 21)
    DC   = op.get("DC", 30)
    CVSC = op["CVSC_aa"] / 100
    n    = 12.0
    pe_parc = op.get("pe_parcela")
    PE_val  = C * op.get("pe_pct", 0.0) if pe_parc else 0.0
    ind_am  = op.get("ind_am", 0.0) / 100

    # PMTA Price
    PMTA_fixo = op.get("PMTA_fixo")
    if PMTA_fixo:
        PMTA_price = abs(PMTA_fixo)
    elif i > 0:
        pv_pe = PE_val / (1+i)**T if PE_val else 0.0
        PMTA_price = (C - pv_pe) * i / (1 - (1+i)**-T)
    else:
        PMTA_price = C / T

    FPR  = rsc["FPR"] / 100;  K = rsc["K"] / 100;  Kp = rsc["Kp"] / 100
    F    = rsc["F"];   FCC = rsc["FCC"] / 100
    CE   = C * FPR * K;       CEIRB = C * FPR * Kp
    lamb = mgm["lamb_am"] / 100

    alfa_pc   = cst["alfa_pc"]    / 100
    alfa_iss  = cst["alfa_iss"]   / 100
    alfa_ir   = cst["alfa_ir_cs"] / 100
    custo_cont= cst.get("custo_cont", 0.0)
    custo_mnt = cst.get("custo_manut", 0.0)
    custo_ag  = cst.get("custo_ag_pct", 0.0) / 100 * C
    custo_proc= cst.get("custo_proc_pct", 0.0) / 100
    tarifa_per= cst.get("tarifa_per", 0.0)

    fase1_am = rsc["fase1_am"] / 100
    usa_f2   = rsc.get("usa_fase2", False)
    fase2_pct= rsc.get("fase2_pct", 0.0) / 100
    atu_ipp  = rsc.get("atu_ipp", "oportunidade")
    fase2_t0 = C * fase2_pct if usa_f2 else 0.0

    # z_J (exigibilidade dos juros do passivo)
    z_J_passivo = passivo_composto.z_J()
    z_J_ativo   = passivo_composto.z_J_ativo()

    # CVSC por período: usa curva CDI-PSC se disponível
    def cvsc_periodo(du_ini, du_fim):
        if curvas and 1 in curvas:
            r_fim = curvas[1].taxa_para_du(du_fim) / 100
            return r_fim  # zero-coupon anual para descontar
        return CVSC

    def vp(val, t):
        if t == 0: return val
        du_t = t * DU
        cvsc_t = cvsc_periodo(0, du_t)
        return val / (1 + cvsc_t) ** (du_t / 252)

    # Estado
    SDA_prev = C;  SJA_prev = 0.0;  SCA_prev = C
    SEBP_prev= 0.0; SCP_prev = C;   SDP_prev = C
    SIPP_prev= 0.0; MG_prev  = 0.0
    SJP_prev = 0.0   # saldo acumulado de juros do passivo (exig. não-mensal)

    linhas = []

    for t in range(0, T + 1):
        du_ini = (t - 1) * DU
        du_fim = t * DU

        # ── ATIVO ─────────────────────────────────────────────────────────────
        LCA  = C if t == 0 else 0.0

        # EBA — indexador do ativo (curva se disponível)
        if t == 0 or t <= tc:
            EBA = 0.0
        else:
            slot_eba = slts.get("ativo.EBA", "z2")
            if slot_eba == "z3" and curvas and op.get("tipo_curva_ativo"):
                tc_ativo = op["tipo_curva_ativo"]
                if tc_ativo in curvas:
                    EBA = SDA_prev * curvas[tc_ativo].taxa_periodo_du(du_ini, du_fim)
                else:
                    EBA = SDA_prev * ((1 + ind_am) ** (DU / 252) - 1)
            else:
                EBA = SDA_prev * (((1 + ind_am) ** (1/n)) - 1)

        # JA
        slot_ja = slts.get("ativo.JA", "z036")
        JA = 0.0 if t == 0 else (SDA_prev * i if slot_ja == "z036" else
                                   SDA_prev * ((1+i)**(1/n)-1) if slot_ja == "z15" else
                                   SDA_prev * ((1+i)**(DU/252)-1) if slot_ja == "z16" else
                                   SDA_prev * i)

        # EJA (exigibilidade dos juros do ativo)
        if t == 0 or t <= tc:
            EJA = 0.0
        elif z_J_ativo is None:          # bullet
            EJA = -(JA + SJA_prev) if t == T else 0.0
        elif z_J_ativo == -1:            # proporcional
            EJA = -(JA + SJA_prev)
        elif t % z_J_ativo == 0:         # periódico
            EJA = -(JA + SJA_prev)
        else:
            EJA = 0.0

        SJA = 0.0 if t == 0 else SJA_prev + JA + EJA

        PE_t      = -PE_val if (pe_parc and t == pe_parc) else 0.0
        PMTA_base = -PMTA_price if (t > tc and t <= T and slts.get("ativo.PMTA","price") == "price") else \
                    (-(C/T) - JA - EBA if slts.get("ativo.PMTA") == "sac" and t > tc and t <= T else 0.0)
        PMTA = PMTA_base + PE_t

        ECA = 0.0 if (t == 0 or t <= tc) else (PMTA - EJA)
        SCA = LCA if t == 0 else SCA_prev + ECA + LCA
        SDA = LCA if t == 0 else SDA_prev + LCA + JA + PMTA

        # ── PASSIVO (múltiplos fundings) ──────────────────────────────────────
        LCP = C if t == 0 else 0.0

        if t == 0:
            EBP = 0.0
        else:
            # Custo total do passivo com todos os fundings
            EBP = passivo_composto.ebp_total(SDP_prev, du_ini, du_fim, curvas)

        # EEBP (exigibilidade com z_J)
        if t == 0 or t <= tc:
            EEBP = 0.0
        elif z_J_passivo is None:        # bullet
            EEBP = -(SEBP_prev + EBP) if t == T else 0.0
        elif z_J_passivo == -1:          # proporcional
            EEBP = -(SEBP_prev + EBP)
        elif t % z_J_passivo == 0:
            EEBP = -(SEBP_prev + EBP)
        else:
            EEBP = 0.0

        SEBP = 0.0 if t == 0 else SEBP_prev + EBP + EEBP

        ECP  = 0.0 if t == 0 else (PMTA - EJA)
        SCP  = LCP if t == 0 else SCP_prev - ECP + LCA
        PMTP = 0.0 if t == 0 else (EEBP + ECP)
        SDP  = LCP if t == 0 else SDP_prev + LCP + EBP + PMTP

        # ── FLUXO ─────────────────────────────────────────────────────────────
        SP     = 0.0 if t == 0 else (-PMTA + PMTP)
        tarifa_t = tarifa_per if (t > 0 and t <= T) else 0.0
        BFA    = 0.0 if t == 0 else (JA - EBP)
        pc     = 0.0 if t == 0 else (-BFA * alfa_pc)
        iss_t  = 0.0 if t == 0 else (-tarifa_t * alfa_iss)

        # Provisão IPP
        DPE  = -fase2_t0 if t == 0 else 0.0
        IPP1 = 0.0 if t == 0 else -(SDA_prev * fase1_am)
        cdi_t = passivo_composto.taxa_efetiva_am(du_ini, du_fim, curvas) / 100
        SDA_base = SDA_prev + JA
        if t > 0 and SDA_base != 0:
            saldo_ipp = fase2_t0 + SIPP_prev
            saldo_upd = saldo_ipp * (1 + cdi_t) if atu_ipp == "oportunidade" else saldo_ipp * (1+i)
            EPE = -(saldo_upd * abs(PMTA) / SDA_base)
        else:
            EPE = 0.0
        SIPP = (fase2_t0 if t == 0 else SIPP_prev) + abs(IPP1)

        # MG
        slot_mg = slts.get("fluxo.MG", "z182")
        if t == 0:
            MG = 0.0
        else:
            bm = SDA_prev + JA
            MG = (bm * ((1+lamb)**(1/n)-1) if slot_mg in ("z182","z393") else
                  bm * ((1+lamb)**(DU/252)-1) if slot_mg == "z180" else
                  bm * ((1+lamb)**(DC/360)-1) if slot_mg == "z181" else
                  bm * ((1+lamb)**(1/12)-1))
        MG_fla = MG_prev
        MC = 0.0 if t == 0 else (SP + EPE + IPP1)

        # Custos
        z394   = -custo_cont  if t == 0 else 0.0
        z230   = -custo_mnt   if t > 0 else 0.0
        f1046  = -custo_ag    if t == 0 else 0.0
        z236   = PMTA * custo_proc if t > 0 else 0.0
        f1044  = z394 + z230 + f1046 + z236

        BFB    = 0.0 if t == 0 else (JA - EBP + tarifa_t + f1044 + EPE + IPP1 + pc + iss_t)
        ir_cs  = 0.0 if t == 0 else (-BFB * alfa_ir)

        FLA    = (z394 + f1046 + DPE) if t == 0 else (SP + tarifa_t + f1044 + EPE + IPP1 + pc + iss_t + ir_cs - MG_fla)
        FLA_VP = vp(FLA, t)
        FLC    = PMTA if t > 0 else 0.0
        FLE    = PMTP if t > 0 else 0.0

        linhas.append({
            "t":t, "LCA":LCA, "JA":JA, "EJA":EJA, "SJA":SJA,
            "EBA":EBA, "ECA":ECA, "SCA":SCA, "PMTA":PMTA, "PE":PE_t, "SDA":SDA,
            "LCP":LCP, "EBP":EBP, "EEBP":EEBP, "SEBP":SEBP,
            "ECP":ECP, "SCP":SCP, "PMTP":PMTP, "SDP":SDP,
            "SP":SP, "tarifa":tarifa_t, "BFA":BFA, "pasep_cof":pc, "iss":iss_t,
            "DPE":DPE, "IPP1":IPP1, "EPE":EPE, "SIPP":SIPP,
            "MG":MG, "MG_fla":MG_fla, "MC":MC,
            "z394":z394, "z230":z230, "f1046":f1046, "z236":z236, "f1044":f1044,
            "BFB":BFB, "ir_cs":ir_cs, "FLA":FLA, "FLA_VP":FLA_VP, "FLC":FLC, "FLE":FLE,
        })

        SDA_prev=SDA; SJA_prev=SJA; SCA_prev=SCA
        SEBP_prev=SEBP; SCP_prev=SCP; SDP_prev=SDP
        SIPP_prev=SIPP; MG_prev=MG

    import pandas as pd
    df = pd.DataFrame(linhas)
    rows = df[df.t > 0]

    def sv(col): return sum(vp(r[col], r["t"]) for _, r in rows.iterrows())
    SPVP = sv("SP"); MGVP = sv("MG"); EPEVP = sv("EPE"); CFVP = sv("f1044")
    FLA_VP_soma = round(df["FLA_VP"].sum(), 6)

    ECA_tot = C; FLC_tot = rows["FLC"].abs().sum(); FLE_tot = rows["FLE"].abs().sum()
    dct_tot = T * 30

    def _solve(fn, fl_k, fl_v, chute):
        try:
            return Solver.solver_secante(fn, {fl_k: fl_v, "ECA_t": ECA_tot, "dct": dct_tot}, chute, 0.1, 5.0)
        except: return None

    tir = _solve(Perf.funcao_objetivo_tir_f1095, "FLD_t", FLC_tot, "chute_tir")
    tpp = _solve(Perf.funcao_objetivo_tpp_f1096, "FLE_t", FLE_tot, "chute_tpp")
    lamb_aa = (1 + lamb) ** 12 - 1
    denom_r = FPR * K  * (1 + (F-1)*FCC); denom_g = FPR * Kp * (1+(F-1)*FCC)
    RSPLE = lamb_aa / denom_r * 100 if denom_r else 0
    RAR_G = lamb_aa / denom_g * 100 if denom_g else 0
    IE    = Perf.indice_eficiencia_ie_f1066(abs(CFVP), SPVP) if SPVP else 0
    IR_r  = Perf.indice_risco_ir_f1067(EPEVP, SPVP) if SPVP else 0
    dur_n = sum(df.loc[df.t>0,"t"]*df.loc[df.t>0,"FLA_VP"]); dur_d = df.loc[df.t>0,"FLA_VP"].abs().sum()
    DRT   = Perf.duration_drt_f1204(dur_n,dur_d) if dur_d else 0

    # Resumo do passivo composto
    resumo_passivo = passivo_composto.resumo(curvas)

    def aa(v):
        return round(((1+v/100)**(360/30)-1)*100, 4) if v else None

    resumo = {
        "receita": receita["nome"], "produto": receita["produto"],
        "Capital (C)": C, "Prazo (T)": T,
        "Taxa ativa % a.m.": round(i*100,4), "λ Margem % a.m.": round(lamb*100,4),
        "λ Margem % a.a.": round(lamb_aa*100,4),
        "PMTA Price": round(PMTA_price,4),
        "FPR": f"{FPR*100:.0f}%", "K regulatório": f"{K*100:.2f}%",
        "K prudencial (Kp)": f"{Kp*100:.2f}%", "F / FCC": f"{F} / {FCC*100:.0f}%",
        "CE regulatório": round(CE,2), "CEIRB (gestão)": round(CEIRB,2),
        "fórmula JA": slts.get("ativo.JA"),
        "fórmula EBP": "composto",
        "fórmula PMTA": slts.get("ativo.PMTA"),
        "fórmula MG": slts.get("fluxo.MG"),
        "Exig. juros passivo": passivo_composto.exig_juros,
        "Exig. juros ativo":   passivo_composto.exig_juros_ativo,
        "WACC passivo % a.m.": round(resumo_passivo["taxa_efetiva_am"],4),
        "N fundings": len(passivo_composto.fontes),
        "Curvas carregadas": list(curvas.keys()) if curvas else [],
        "Total PMTA": round(rows["PMTA"].abs().sum(),2),
        "Total JA":   round(rows["JA"].sum(),2),
        "SDA final":  round(df.loc[df.t==T,"SDA"].values[0],2),
        "Total EBP (CDI)": round(rows["EBP"].sum(),2),
        "SDP final":  round(df.loc[df.t==T,"SDP"].values[0],2),
        "Total SP":   round(rows["SP"].sum(),2),
        "Total MG":   round(rows["MG"].sum(),2),
        "Total IPP Fase1": round(rows["IPP1"].abs().sum(),2),
        "Total EPE":  round(rows["EPE"].abs().sum(),2),
        "Total PASEP+COF": round(rows["pasep_cof"].abs().sum(),2),
        "Total ISS":  round(rows["iss"].abs().sum(),2),
        "Total IR/CS": round(rows["ir_cs"].abs().sum(),2),
        "Total Custos": round(rows["f1044"].abs().sum(),2),
        "FLA VP (Σ) → 0": round(FLA_VP_soma,4),
        "MG % a.m.": round(lamb*100,4), "MG % a.a.": round(lamb_aa*100,4),
        "RSPLE %": round(RSPLE,4), "RAR_G % (gestão, F1183)": round(RAR_G,4),
        "RAR % (base)": round(MGVP/CE*100,4) if CE else 0,
        "IE (eficiência)": round(IE,4), "IR (risco)": round(IR_r,4),
        "Duration (meses)": round(DRT,2),
        "TIR % a.a.": aa(tir), "Resultado PPS % a.m.": round(tpp,4) if tpp else None,
        "SPVP": round(SPVP,2), "MGVP (λ_mg)": round(MGVP,2), "EPEVP": round(EPEVP,2),
    }

    return {"fluxo": df, "resumo": resumo, "receita": receita,
            "passivo_resumo": resumo_passivo, "curvas": curvas}
