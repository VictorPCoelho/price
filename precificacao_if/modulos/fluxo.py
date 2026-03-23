
class ModuloFluxo:
    """
    5- MÓDULO FLUXO (COMPLETO E DEFINITIVO)
    Abertura total de fórmulas Z, F, Custos com Condicionais, Risco de Crédito,
    Custo de Provisão (5.6), Bases Fiscais (BFA a BFX) e Tributação explícita (5.7).
    INCLUI INTEGRAÇÃO FINAL (Z452, Z465, Z466, Z493 e FVP F1178 a F1237).
    """

    # ==========================================
    # 5.1 SPREAD (SP)
    # ==========================================
    @staticmethod
    def sp_z175(PMTA_t: float, PMTP_t: float) -> float: return PMTA_t - PMTP_t
    @staticmethod
    def sp_z176(PMTA_t: float, PMTP_t: float, EEQL_t: float) -> float: return PMTA_t - PMTP_t + EEQL_t
    @staticmethod
    def sp_z177(soma_PMTA_k: float, soma_PMTP_q: float) -> float: return soma_PMTA_k - soma_PMTP_q
    @staticmethod
    def sp_z178(soma_PMTA_k: float, soma_PMTP_q: float, soma_EEQL_k: float) -> float: return soma_PMTA_k - soma_PMTP_q + soma_EEQL_k
    @staticmethod
    def sp_z179(soma_PMTA_k: float, soma_PMTRP_q: float) -> float: return soma_PMTA_k - soma_PMTRP_q

    # ==========================================
    # 5.2 MARGENS (MG, MGA e MC)
    # ==========================================
    @staticmethod
    def mg_z180(base: float, lamb: float, DU_t: int, t: int, T: int) -> float:
        return base * (((1 + (lamb / 100)) ** (DU_t / 252)) - 1) if 0 < t <= T else 0.0
    @staticmethod
    def mg_z181(base: float, lamb: float, DC_t: int, t: int, T: int) -> float:
        return base * (((1 + (lamb / 100)) ** (DC_t / 360)) - 1) if 0 < t <= T else 0.0
    @staticmethod
    def mg_z182(soma_base: float, lamb: float, n: float, t: int, T: int) -> float:
        return soma_base * (((1 + (lamb / 100)) ** (1 / n)) - 1) if 0 < t <= T else 0.0
    @staticmethod
    def mg_z183(soma_base: float, lamb: float, DU_t: int, t: int, T: int) -> float:
        return soma_base * (((1 + (lamb / 100)) ** (DU_t / 252)) - 1) if 0 < t <= T else 0.0
    @staticmethod
    def mg_z184(soma_base: float, lamb: float, DC_t: int, t: int, T: int) -> float:
        return soma_base * (((1 + (lamb / 100)) ** (DC_t / 360)) - 1) if 0 < t <= T else 0.0
    @staticmethod
    def mg_z185(soma_base: float, lamb: float, DC_t: int, t: int, T: int) -> float:
        return soma_base * (((1 + (lamb / 100)) ** (DC_t / 365)) - 1) if 0 < t <= T else 0.0
    @staticmethod
    def mg_z186(SDA_t_1: float, JA_t: float, lamb: float, DU_t: int, DU_t_mais_1: int, t: int, T: int) -> float:
        if 0 < t < T: return (SDA_t_1 + JA_t) * (((1 + (lamb / 100)) ** (DU_t / 252)) - 1)
        if t == T: return (SDA_t_1 + JA_t) * (((1 + (lamb / 100)) ** (DU_t_mais_1 / 252)) - 1)
        return 0.0
    @staticmethod
    def mg_z393(SDA_t_1: float, JA_t: float, lamb: float, DU_t: int, t: int, T: int) -> float:
        return (SDA_t_1 + JA_t) * (((1 + (lamb / 100)) ** (DU_t / 252)) - 1) if 0 < t <= T else 0.0
    @staticmethod
    def mg_z441(base: float, lamb: float, t: int, T: int) -> float:
        return base * (((1 + (lamb / 100)) ** (1 / 12)) - 1) if 0 < t <= T else 0.0
    @staticmethod
    def mg_z485(soma_base: float, lamb: float, DC_t: int, t: int, T: int) -> float:
        return soma_base * lamb * (DC_t / 36000) if 0 < t <= T else 0.0
    @staticmethod
    def mg_z560(soma_base: float, lamb: float, DC_t: int, DAC: int, t: int, T: int) -> float:
        return soma_base * (((1 + (lamb / 100)) ** (DC_t / DAC)) - 1) if 0 < t <= T else 0.0

    # MGA
    @staticmethod
    def mga_z601(base: float, phi: float, DU_t: int, t: int, T: int) -> float:
        return base * (((1 + (phi / 100)) ** (DU_t / 252)) - 1) if 0 < t <= T else 0.0
    @staticmethod
    def mga_z619(base: float, phi: float, DC_t: int, t: int, T: int) -> float:
        return base * (phi / 100) * (DC_t / 360) if 0 < t <= T else 0.0
    @staticmethod
    def mga_z634(base: float, phi: float, DC_t: int, DAC: int, t: int, T: int) -> float:
        return base * (phi * DC_t) / (DAC * 100) if 0 < t <= T else 0.0

    # MC
    @staticmethod
    def mc_z187(base: float, theta: float, n: float, t: int, T: int) -> float:
        return base * (((1 + (theta / 100)) ** (1 / n)) - 1) if 0 < t <= T else 0.0
    @staticmethod
    def mc_z188(base: float, theta: float, DU_t: int, t: int, T: int) -> float:
        return base * (((1 + (theta / 100)) ** (DU_t / 252)) - 1) if 0 < t <= T else 0.0
    @staticmethod
    def mc_z189(base: float, theta: float, DC_t: int, t: int, T: int) -> float:
        return base * (((1 + (theta / 100)) ** (DC_t / 360)) - 1) if 0 < t <= T else 0.0
    @staticmethod
    def mc_z190(base: float, theta: float, DC_t: int, t: int, T: int) -> float:
        return base * (((1 + (theta / 100)) ** (DC_t / 365)) - 1) if 0 < t <= T else 0.0
    @staticmethod
    def mc_z191(soma_base: float, theta: float, n: float, t: int, T: int) -> float:
        return soma_base * (((1 + (theta / 100)) ** (1 / n)) - 1) if 0 < t <= T else 0.0
    @staticmethod
    def mc_z192(soma_base: float, theta: float, DU_t: int, t: int, T: int) -> float:
        return soma_base * (((1 + (theta / 100)) ** (DU_t / 252)) - 1) if 0 < t <= T else 0.0
    @staticmethod
    def mc_z193(soma_base: float, theta: float, DC_t: int, t: int, T: int) -> float:
        return soma_base * (((1 + (theta / 100)) ** (DC_t / 360)) - 1) if 0 < t <= T else 0.0
    @staticmethod
    def mc_z194(soma_base: float, theta: float, DC_t: int, t: int, T: int) -> float:
        return soma_base * (((1 + (theta / 100)) ** (DC_t / 365)) - 1) if 0 < t <= T else 0.0
    @staticmethod
    def mc_z195(SDA_t_1: float, JA_t: float, theta: float, DU_t: int, DU_t_mais_1: int, t: int, T: int) -> float:
        if 0 < t < T: return (SDA_t_1 + JA_t) * (((1 + (theta / 100)) ** (DU_t / 252)) - 1)
        if t == T: return (SDA_t_1 + JA_t) * (((1 + (theta / 100)) ** (DU_t_mais_1 / 252)) - 1)
        return 0.0
    @staticmethod
    def mc_z196(SP_t: float, PASEP_t: float, COFINS_t: float, CP_t: float, EPE_t: float, t: int, T: int) -> float:
        return SP_t - PASEP_t + COFINS_t + CP_t + EPE_t if 0 < t <= T else 0.0
    @staticmethod
    def mc_z392(SDA_t_1: float, JA_t: float, theta: float, DU_t: int, t: int, T: int) -> float:
        return (SDA_t_1 + JA_t) * (((1 + (theta / 100)) ** (DU_t / 252)) - 1) if 0 < t <= T else 0.0
    @staticmethod
    def mc_z442(base: float, theta: float, t: int, T: int) -> float:
        return base * (((1 + (theta / 100)) ** (1 / 12)) - 1) if 0 < t <= T else 0.0
    @staticmethod
    def mc_z486(soma_base: float, theta: float, DC_t: int, t: int, T: int) -> float:
        return soma_base * theta * (DC_t / 36000) if 0 < t <= T else 0.0
    @staticmethod
    def mc_z561(soma_base: float, theta: float, DC_t: int, DAC: int, t: int, T: int) -> float:
        return soma_base * (((1 + (theta / 100)) ** (DC_t / DAC)) - 1) if 0 < t <= T else 0.0

    # ==========================================
    # 5.3 RECEITAS ADICIONAIS (RA)
    # ==========================================
    @staticmethod
    def ra_total_f1043(*args) -> float: return sum(args)
    @staticmethod
    def rtac_f1084(rTAC: float, t: int) -> float: return rTAC if t == 0 else 0.0
    @staticmethod
    def rtam_z197(rTAM: float, t: int, T: int) -> float: return rTAM if 0 < t <= T else 0.0
    @staticmethod
    def rtam_z198(rTAM: float, FINDTAM_t: float, t: int, T: int) -> float: return (rTAM / 100) * FINDTAM_t if 0 < t <= T else 0.0
    @staticmethod
    def rfa_z199(rFA: float, t: int) -> float: return rFA if t == 0 else 0.0
    @staticmethod
    def rfa_z200(rFA: float, t: int, T: int) -> float: return rFA if 0 < t <= T else 0.0
    @staticmethod
    def rfa_z201(rFA: float, C: float, t: int) -> float: return (rFA / 100) * C if t == 0 else 0.0
    @staticmethod
    def rfa_z202(rFA: float, LCA_t: float, t: int) -> float: return (rFA / 100) * LCA_t if t == 0 else 0.0
    @staticmethod
    def rsmpi_f1085(rSMPI: float, SDA_t_1: float, t: int, T: int) -> float: return (rSMPI / 100) * SDA_t_1 if 0 < t <= T else 0.0
    @staticmethod
    def rsdfi_f1086(rSDFI: float, VI: float, t: int) -> float: return (rSDFI / 100) * VI if t == 0 else 0.0
    @staticmethod
    def rsgo_z204(rSGO: float, t: int) -> float: return rSGO if t == 0 else 0.0
    @staticmethod
    def rsgo_z206(rSGO: float, C: float, t: int) -> float: return (rSGO / 100) * C if t == 0 else 0.0
    @staticmethod
    def rsgo_z208(rSGO: float, SDA_t_1: float, t: int, T: int) -> float: return (rSGO / 100) * SDA_t_1 if 0 < t <= T else 0.0
    @staticmethod
    def rcm_z209(rCM: float, t: int) -> float: return rCM if t == 0 else 0.0
    @staticmethod
    def rcm_z211(rCM: float, C: float, t: int) -> float: return (rCM / 100) * C if t == 0 else 0.0
    @staticmethod
    def rcm_z213(rCM: float, SDA_t_1: float, t: int, T: int) -> float: return (rCM / 100) * SDA_t_1 if 0 < t <= T else 0.0
    @staticmethod
    def rtaa_z214(rTAA: float, t: int) -> float: return rTAA if t == 0 else 0.0
    @staticmethod
    def rtaa_z216(rTAA: float, C: float, t: int) -> float: return (rTAA / 100) * C if t == 0 else 0.0
    @staticmethod
    def rtaa_z218(rTAA: float, SDA_t_1: float, t: int, T: int) -> float: return (rTAA / 100) * SDA_t_1 if 0 < t <= T else 0.0
    @staticmethod
    def rcom_z219(SDA_t: float, rCOM: float, ind: float, DUT: int, t: int) -> float:
        return SDA_t * (rCOM / 100) * (((1 + (ind / 100)) ** DUT) - 1) if t == 0 else 0.0
    @staticmethod
    def rcom_z427(SDA_t_1: float, EBA_t: float, SDA_t: float, rCOM: float, z: int, TF: int, t: int, T: int) -> float:
        if TF == 0 and 0 < t <= T and (t % z) == 0: return (SDA_t_1 + EBA_t) * (((1 + (rCOM / 100)) ** z) - 1)
        if TF == 1 and 0 <= t < T and (t % z) == 0: return SDA_t * (((1 + (rCOM / 100)) ** z) - 1)
        return 0.0

    # ==========================================
    # 5.4 CUSTOS FIXOS E VARIÁVEIS (CFVT) E ESPECÍFICOS
    # ==========================================
    @staticmethod
    def cfvt_total_f1044(*args) -> float: return sum(args)
    @staticmethod
    def cfc_z394(cFC: float, t: int) -> float: return cFC if t == 0 else 0.0
    @staticmethod
    def cfc_z395(cFC: float, DCT: int, PM: int, t: int) -> float: return cFC * (DCT / PM) if t == 0 else 0.0
    @staticmethod
    def cfc_z480(CFC: float, t: int, t_linha: int = 0, atende_condicao: bool = True) -> float:
        if t == t_linha and atende_condicao: return CFC
        return 0.0
    @staticmethod
    def cfm_z228(cFM: float, t: int, T: int) -> float: return cFM if 0 < t <= T else 0.0
    @staticmethod
    def cfag_f1046(cFAG: float, w_k: float, C: float, t: int) -> float: return (cFAG / 100) * (w_k / 100) * C if t == 0 else 0.0
    @staticmethod
    def cvrg_z240(cVRG: float, t: int) -> float: return cVRG if t == 0 else 0.0
    @staticmethod
    def cvcm_z255(cVCM: float, t: int) -> float: return cVCM if t == 0 else 0.0
    @staticmethod
    def cvot_z519(cVOT: float, base_encargos: float, t: int, tc: int, T: int, z: int) -> float:
        if tc < t <= T and (t % z) == 0: return (cVOT / 100) * base_encargos
        return 0.0

    # -> ADIÇÕES SOLICITADAS PELA REVISÃO
    @staticmethod
    def custo_z452(base: float, taxa: float, t: int, T: int) -> float:
        return base * (taxa / 100) if 0 < t <= T else 0.0
    @staticmethod
    def provisao_z465(base: float, taxa: float, t: int, T: int) -> float:
        return base * (taxa / 100) if 0 < t <= T else 0.0
    @staticmethod
    def provisao_z466(base: float, taxa: float, t: int, T: int) -> float:
        return base * (taxa / 100) if 0 < t <= T else 0.0
    @staticmethod
    def despesa_z493(base: float, taxa: float, t: int, T: int) -> float:
        return base * (taxa / 100) if 0 < t <= T else 0.0

    # ==========================================
    # 5.5 RISCO DE CRÉDITO (Perda Esperada)
    # ==========================================
    @staticmethod
    def dpe_z276(base: float, RBA: float, r: float, n: float, t: int, T: int) -> float: return base * (RBA / 100) * r * (1 / n) if 0 < t <= T else 0.0
    @staticmethod
    def dpe_z277(base: float, RBA: float, r: float, DU_t: int, t: int, T: int) -> float: return base * RBA * r * (DU_t / 2520000) if 0 < t <= T else 0.0
    @staticmethod
    def dpe_z278(base: float, RBA: float, r: float, DC_t: int, t: int, T: int) -> float: return base * RBA * r * (DC_t / 3650000) if 0 < t <= T else 0.0
    @staticmethod
    def sdpe_z280(SDPE_t_1: float, ind: float, i: float, n: float, DPE: float, EPE: float, t: int, T: int) -> float:
        return SDPE_t_1 * ((1 + (ind / 100)) ** (1 / n)) * ((1 + (i / 100)) ** (1 / n)) + DPE - EPE if 0 < t <= T else 0.0
    @staticmethod
    def epe_z289(DPE: float, SDPE_t_1: float, ind: float, i: float, DC_t: int, soma_PMTA: float, soma_base: float) -> float:
        if soma_PMTA <= 0: return 0.0
        return DPE + SDPE_t_1 * ((1 + (ind / 100)) ** (DC_t / 360)) * ((1 + (i / 100)) ** (DC_t / 360)) * (soma_PMTA / soma_base)

    # ==========================================
    # 5.6 CUSTO DE OPORTUNIDADE SOBRE PROVISÃO (CP)
    # ==========================================
    @staticmethod
    def cp_z301(base: float, PCLD: float, K: float, RSPLE: float, FPR: float, F: float, FCC: float, n: float, t: int, T: int) -> float:
        return base * (PCLD * (1 / (K - 1)) * (1 + RSPLE * K * FPR * ((1 + F) - 1) * FCC)) * ((1 / n) - 1) if 0 < t <= T else 0.0
    @staticmethod
    def cp_z302(base: float, PCLD: float, K: float, RSPLE: float, FPR: float, F: float, FCC: float, DU_t: int, t: int, T: int) -> float:
        return base * (PCLD * (1 / (K - 1)) * (1 + RSPLE * K * FPR * ((1 + F) - 1) * FCC)) * ((DU_t / 252) - 1) if 0 < t <= T else 0.0
    @staticmethod
    def cp_z303(base: float, PCLD: float, K: float, RSPLE: float, FPR: float, F: float, FCC: float, DC_t: int, t: int, T: int) -> float:
        return base * (PCLD * (1 / (K - 1)) * (1 + RSPLE * K * FPR * ((1 + F) - 1) * FCC)) * ((DC_t / 365) - 1) if 0 < t <= T else 0.0
    @staticmethod
    def cp_z304(base: float, PCLD: float, K: float, RSPLE: float, FPR: float, F: float, FCC: float, DC_t: int, DAC: int, t: int, T: int) -> float:
        return base * (PCLD * (1 / (K - 1)) * (1 + RSPLE * K * FPR * ((1 + F) - 1) * FCC)) * ((DC_t / DAC) - 1) if 0 < t <= T else 0.0
    @staticmethod
    def cp_z305(base: float, PCLD: float, K: float, RSPLE: float, FPR: float, F: float, FCC: float, DC_t: int, t: int, T: int) -> float:
        return base * (PCLD * (1 / (K - 1)) * (1 + RSPLE * K * FPR * ((1 + F) - 1) * FCC)) * ((DC_t / 360) - 1) if 0 < t <= T else 0.0

    # ==========================================
    # 5.7 TRIBUTAÇÃO (Bases Fiscais BFA a BFX)
    # ==========================================
    @staticmethod
    def bfa_f1047(rec: float, desp: float, RA: float) -> float: return rec - desp + RA
    @staticmethod
    def bfb_f1048(BFA: float, CFVT: float, EPE: float, PASEP: float, COF: float, ISS: float, ISSL: float) -> float: return BFA - CFVT - EPE - PASEP - COF - ISS - ISSL
    @staticmethod
    def bfc_f1049(RA: float) -> float: return RA
    @staticmethod
    def bfd_f1050(COA: float, DPR: float, JP: float, EBP: float, RA: float, CFVT: float, EPE: float, ISS: float, ISSL: float, PASEP: float, COF: float, RV: float) -> float: return COA - DPR - JP - EBP + RA - CFVT - EPE - ISS - ISSL - PASEP - COF + max(RV, 0)
    @staticmethod
    def bfe_f1051(COA: float, DPR: float, EBP: float, EBPC: float, JP: float, JPC: float, RA: float, CFVT: float, EPE: float, ISS: float, ISSL: float, PASEP: float, COF: float, RV: float) -> float: return COA - DPR - EBP - EBPC - JP - JPC + RA - CFVT - EPE - ISS - ISSL - PASEP - COF + max(RV, 0)
    @staticmethod
    def bff_f1052(COA: float, DPR: float, EBRP: float, JRP: float, RA: float, CFVT: float, EPE: float, ISS: float, ISSL: float, PASEP: float, COF: float, RV: float) -> float: return COA - DPR - EBRP - JRP + RA - CFVT - EPE - ISS - ISSL - PASEP - COF + max(RV, 0)
    @staticmethod
    def bfg_f1053(RVT: float, TAP: float, T: int, t: int) -> float: return RVT / TAP if (RVT < 0 and TAP > 0 and T < t <= (T + TAP)) else 0.0
    @staticmethod
    def bfh_f1054(rec: float, desp: float, RA: float, CFVT: float) -> float: return rec - desp + RA - CFVT
    @staticmethod
    def bfi_f1055(COA: float, DPR: float, JP: float, EBP: float, RA: float) -> float: return COA - DPR - JP - EBP + RA
    @staticmethod
    def bfj_f1056(COA: float, DPR: float, EBP: float, EBPC: float, JP: float, JPC: float, RA: float) -> float: return COA - DPR - EBP - EBPC - JP - JPC + RA
    @staticmethod
    def bfk_f1057(COA: float, DPR: float, EBRP: float, JRP: float, RA: float) -> float: return COA - DPR - EBRP - JRP + RA
    @staticmethod
    def bfl_f1092(RA: float, CFVT: float, EPE: float, PASEP: float, COF: float) -> float: return RA - CFVT - EPE - PASEP - COF
    @staticmethod
    def bfm_f1058(RA: float, CFVT: float) -> float: return RA - CFVT
    @staticmethod
    def bfn_f1185(rec: float, desp: float, RA: float, CFVT: float, EPE: float) -> float: return rec - desp + RA - CFVT - EPE
    @staticmethod
    def bfo_f1186(BFI: float, CFVT: float, EPE: float) -> float: return BFI - CFVT - EPE
    @staticmethod
    def bfp_f1187(BFJ: float, CFVT: float, EPE: float) -> float: return BFJ - CFVT - EPE
    @staticmethod
    def bfq_f1188(RA: float, CFVT: float, EPE: float, PASEP: float, COF: float, ISS: float) -> float: return RA - CFVT - EPE - PASEP - COF - ISS
    @staticmethod
    def bfr_f1221(BFK: float, CFVT: float, EPE: float) -> float: return BFK - CFVT - EPE
    @staticmethod
    def bfs_z454(RA: float, CFVT: float, EPE: float) -> float: return RA - CFVT - EPE
    @staticmethod
    def bft_f1225(rec: float, desp: float) -> float: return rec - desp
    @staticmethod
    def bfu_f1226(BFT: float, CFVT: float, EPE: float, PASEP: float, COF: float) -> float: return BFT - CFVT - EPE - PASEP - COF
    @staticmethod
    def bfv_f1246(BFT: float, CFVT: float, EPE: float) -> float: return BFT - CFVT - EPE
    @staticmethod
    def bfw_f1247(BFT: float, CFVT: float, EPE: float, PASEP: float, COF: float, ISS: float, ISSL: float) -> float: return BFT - CFVT - EPE - PASEP - COF - ISS - ISSL
    @staticmethod
    def bfx_f1248(BFT: float, CFVT: float) -> float: return BFT - CFVT

    # ==========================================
    # 5.7 TRIBUTAÇÃO (Fórmulas Explícitas Z306 a Z455)
    # ==========================================
    @staticmethod
    def pasep_z306(base_fiscal: float, alfa: float, t: int, T: int) -> float: return base_fiscal * (alfa / 100) if 0 < t <= T else 0.0
    @staticmethod
    def pasep_z307(base_fiscal: float, alfa: float, t: int) -> float: return base_fiscal * (alfa / 100) if t == 0 else 0.0

    @staticmethod
    def cofins_z311(base_fiscal: float, alfa: float, t: int, T: int) -> float: return base_fiscal * (alfa / 100) if 0 < t <= T else 0.0
    @staticmethod
    def cofins_z312(base_fiscal: float, alfa: float, t: int) -> float: return base_fiscal * (alfa / 100) if t == 0 else 0.0

    @staticmethod
    def iss_z316(base_fiscal: float, alfa: float, t: int, T: int) -> float: return base_fiscal * (alfa / 100) if 0 < t <= T else 0.0
    @staticmethod
    def iss_z317(base_fiscal: float, alfa: float, t: int) -> float: return base_fiscal * (alfa / 100) if t == 0 else 0.0

    @staticmethod
    def issl_z320(base_fiscal: float, alfa: float, t: int, T: int) -> float: return base_fiscal * (alfa / 100) if 0 < t <= T else 0.0

    @staticmethod
    def irpj_z321(base_fiscal: float, alfa: float, t: int, T: int) -> float: return base_fiscal * (alfa / 100) if 0 < t <= T else 0.0
    @staticmethod
    def irpj_z322(base_fiscal: float, alfa: float, t: int) -> float: return base_fiscal * (alfa / 100) if t == 0 else 0.0

    @staticmethod
    def irdpj_z325(base_fiscal: float, alfa: float, limite: float, t: int, T: int) -> float:
        return (base_fiscal - limite) * (alfa / 100) if (0 < t <= T and base_fiscal > limite) else 0.0

    @staticmethod
    def csll_z326(base_fiscal: float, alfa: float, t: int, T: int) -> float: return base_fiscal * (alfa / 100) if 0 < t <= T else 0.0
    @staticmethod
    def csll_z327(base_fiscal: float, alfa: float, t: int) -> float: return base_fiscal * (alfa / 100) if t == 0 else 0.0

    @staticmethod
    def fgc_f1059(SDP_t_1: float, alfa: float, t: int, T: int) -> float: return (alfa / 100) * SDP_t_1 if 0 < t <= T else 0.0
    @staticmethod
    def fgc_z400(SDP_t_1: float, EBP: float, JP: float, alfa: float, DC_t: int, t: int, T: int) -> float:
        return (alfa / 100) * (DC_t / 30) * ((SDP_t_1 + (SDP_t_1 + EBP + JP)) / 2) if 0 < t <= T else 0.0

    @staticmethod
    def isr_z455(BFS: float, alfa_ISR: float) -> float:
        return BFS * (alfa_ISR / 100)

    # ==========================================
    # 5.8 FLUXOS DE CAIXA (FLA a FLH)
    # ==========================================
    @staticmethod
    def fla_f1060(SP: float, RA: float, CFVT: float, EPE: float, FGC: float, PASEP: float, COF: float, ISS: float, ISSL: float, IRPJ: float, IRDPJ: float, CSLL: float, CP: float, MG: float) -> float:
        return SP + RA - CFVT - EPE - FGC - PASEP - COF - ISS - ISSL - IRPJ - IRDPJ - CSLL - CP - MG

    @staticmethod
    def flb_f1061(SP: float, RA: float, EPE: float, FGC: float, PASEP: float, COF: float, ISS: float, ISSL: float, CP: float, MC: float) -> float:
        return SP + RA - EPE - FGC - PASEP - COF - ISS - ISSL - CP - MC

    @staticmethod
    def flc_f1099(PMTA: float) -> float: return PMTA
    @staticmethod
    def fld_f1100(PMTA: float, RA: float) -> float: return PMTA + RA
    @staticmethod
    def fle_f1101(PMTP: float) -> float: return PMTP

    @staticmethod
    def flf_f1231(SP: float, RA: float, CFVT: float, EPE: float, FGC: float, PASEP: float, COF: float, ISS: float, ISSL: float, IRPJ: float, IRDPJ: float, CSLL: float, CP: float) -> float:
        return SP + RA - CFVT - EPE - FGC - PASEP - COF - ISS - ISSL - IRPJ - IRDPJ - CSLL - CP

    @staticmethod
    def flg_f1227(SP: float, CFVT: float, EPE: float, FGC: float, PASEP: float, COF: float, IRPJ: float, CSLL: float, CP: float, MGA: float) -> float:
        return SP - CFVT - EPE - FGC - PASEP - COF - IRPJ - CSLL - CP - MGA

    @staticmethod
    def flh_f1228(SP: float, CFVT: float, EPE: float, FGC: float, PASEP: float, COF: float, CP: float, MGA: float) -> float:
        return SP - CFVT - EPE - FGC - PASEP - COF - CP - MGA

    # ==========================================
    # VALOR PRESENTE DOS FLUXOS (FVPA a FVPH) E TOTALIZADORES
    # ==========================================
    @staticmethod
    def fvpa_f1062(FLA: float, CVCC: float, DU_t: int) -> float: return FLA / ((1 + (CVCC / 100)) ** (DU_t / 252)) if DU_t > 0 else FLA
    @staticmethod
    def fvpb_f1063(FLB: float, CVCC: float, DU_t: int) -> float: return FLB / ((1 + (CVCC / 100)) ** (DU_t / 252)) if DU_t > 0 else FLB
    @staticmethod
    def fvpc_f1103(FLC: float, CVCC: float, DU_t: int) -> float: return FLC / ((1 + (CVCC / 100)) ** (DU_t / 252)) if DU_t > 0 else FLC
    @staticmethod
    def fvpd_f1104(FLD: float, CVCC: float, DU_t: int) -> float: return FLD / ((1 + (CVCC / 100)) ** (DU_t / 252)) if DU_t > 0 else FLD
    @staticmethod
    def fvpe_f1105(FLE: float, CVCC: float, DU_t: int) -> float: return FLE / ((1 + (CVCC / 100)) ** (DU_t / 252)) if DU_t > 0 else FLE
    @staticmethod
    def fvpf_f1232(FLF: float, CVCC: float, DU_t: int) -> float: return FLF / ((1 + (CVCC / 100)) ** (DU_t / 252)) if DU_t > 0 else FLF
    @staticmethod
    def fvpg_f1234(FLG: float, CVCC: float, DU_t: int) -> float: return FLG / ((1 + (CVCC / 100)) ** (DU_t / 252)) if DU_t > 0 else FLG
    @staticmethod
    def fvph_f1235(FLH: float, CVCC: float, DU_t: int) -> float: return FLH / ((1 + (CVCC / 100)) ** (DU_t / 252)) if DU_t > 0 else FLH

    # -> ADIÇÕES SOLICITADAS PELA REVISÃO (Totalizadores de Custos/Margens VP)
    @staticmethod
    def vp_f1178(valor_t: float, CVSC_t: float, DU_t: int) -> float: return valor_t / ((1 + (CVSC_t / 100)) ** (DU_t / 252)) if DU_t > 0 else valor_t
    @staticmethod
    def vp_f1190(valor_t: float, CVSC_t: float, DU_t: int) -> float: return valor_t / ((1 + (CVSC_t / 100)) ** (DU_t / 252)) if DU_t > 0 else valor_t
    @staticmethod
    def vp_f1191(valor_t: float, CVSC_t: float, DU_t: int) -> float: return valor_t / ((1 + (CVSC_t / 100)) ** (DU_t / 252)) if DU_t > 0 else valor_t
    @staticmethod
    def vp_f1192(valor_t: float, CVSC_t: float, DU_t: int) -> float: return valor_t / ((1 + (CVSC_t / 100)) ** (DU_t / 252)) if DU_t > 0 else valor_t
    @staticmethod
    def vp_f1193(valor_t: float, CVSC_t: float, DU_t: int) -> float: return valor_t / ((1 + (CVSC_t / 100)) ** (DU_t / 252)) if DU_t > 0 else valor_t
    @staticmethod
    def vp_f1202(valor_t: float, CVSC_t: float, DU_t: int) -> float: return valor_t / ((1 + (CVSC_t / 100)) ** (DU_t / 252)) if DU_t > 0 else valor_t
    @staticmethod
    def vp_f1203(valor_t: float, CVSC_t: float, DU_t: int) -> float: return valor_t / ((1 + (CVSC_t / 100)) ** (DU_t / 252)) if DU_t > 0 else valor_t
    @staticmethod
    def vp_f1219(valor_t: float, CVSC_t: float, DU_t: int) -> float: return valor_t / ((1 + (CVSC_t / 100)) ** (DU_t / 252)) if DU_t > 0 else valor_t
    @staticmethod
    def vp_f1237(valor_t: float, CVSC_t: float, DU_t: int) -> float: return valor_t / ((1 + (CVSC_t / 100)) ** (DU_t / 252)) if DU_t > 0 else valor_t
