
import math

class ModuloPassivo:
    """
    4- MÓDULO PASSIVO (COMPLETO)
    Objetivo: Apurar o custo de captação (funding), exigibilidades e saldos a pagar.
    Espelho matemático do Módulo Ativo, adaptado para as variáveis do Passivo (q).
    """

    # ==========================================
    # 4.1 EBP: Débito de Encargos Básicos do Passivo
    # ==========================================

    @staticmethod
    def ebp_z1(SDP_t_1_q: float, ind_t_q: float, t: int, tc: int, T: int) -> float:
        if tc < t <= T: return SDP_t_1_q * (ind_t_q / 100)
        return 0.0

    @staticmethod
    def ebp_z2(SDP_t_1_q: float, ind_t_q: float, n: float, t: int, tc: int, T: int) -> float:
        if tc < t <= T: return SDP_t_1_q * (((1 + (ind_t_q / 100)) ** (1 / n)) - 1)
        return 0.0

    @staticmethod
    def ebp_z3(SDP_t_1_q: float, ind_t_q: float, DU_t: int, t: int, T: int) -> float:
        if 0 < t <= T: return SDP_t_1_q * (((1 + (ind_t_q / 100)) ** (DU_t / 252)) - 1)
        return 0.0

    @staticmethod
    def ebp_z4(SDP_t_1_q: float, ind_t_q: float, DC_t: int, t: int, T: int) -> float:
        if 0 < t <= T: return SDP_t_1_q * (((1 + (ind_t_q / 100)) ** (DC_t / 360)) - 1)
        return 0.0

    @staticmethod
    def ebp_z5(SDP_t_1_q: float, ind_t_q: float, DC_t: int, t: int, T: int) -> float:
        if 0 < t <= T: return SDP_t_1_q * (((1 + (ind_t_q / 100)) ** (DC_t / 365)) - 1)
        return 0.0

    # ==========================================
    # EEBP: Exigibilidade de Encargos Básicos do Passivo
    # ==========================================

    @staticmethod
    def eebp_z9(EBP_t_q: float, SEBP_t_1_q: float, t: int, tc: int, T: int, z_EB: int) -> float:
        if tc < t <= T and (t % z_EB) == (tc % z_EB): return EBP_t_q + SEBP_t_1_q
        return 0.0

    @staticmethod
    def eebp_z10(EBP_t_q: float, SEBP_t_1_q: float, ECP_t_q: float, SCP_t_1_q: float, t: int, tc: int, T: int, z_EB: int) -> float:
        if tc < t <= T and (t % z_EB) == (tc % z_EB) and SCP_t_1_q > 0:
            return (EBP_t_q + SEBP_t_1_q) * (ECP_t_q / SCP_t_1_q)
        return 0.0

    @staticmethod
    def eebp_z12(EBP_t_q: float, SEBP_t_1_q: float, t: int, T: int) -> float:
        if t == T: return SEBP_t_1_q + EBP_t_q
        return 0.0

    # ==========================================
    # SEBP: Saldo de Encargos Básicos do Passivo
    # ==========================================

    @staticmethod
    def sebp_f1021(SEBP_t_1_q: float, EBP_t_q: float, EEBP_t_q: float, t: int, T: int) -> float:
        if 0 < t <= T: return SEBP_t_1_q + EBP_t_q - EEBP_t_q
        return 0.0

    # ==========================================
    # EBPC: Débito de Encargos Básicos na Carência do Passivo
    # ==========================================

    @staticmethod
    def ebpc_z13(SDP_t_1_q: float, ind_t_q: float, t: int, tc: int) -> float:
        if 0 < t <= tc: return SDP_t_1_q * (ind_t_q / 100)
        return 0.0

    @staticmethod
    def ebpc_z15(SDP_t_1_q: float, ind_t_q: float, DU_t: int, t: int, tc: int) -> float:
        if 0 < t <= tc: return SDP_t_1_q * (((1 + (ind_t_q / 100)) ** (DU_t / 252)) - 1)
        return 0.0

    # ==========================================
    # EEBPC: Exigibilidade de Encargos Básicos na Carência do Passivo
    # ==========================================

    @staticmethod
    def eebpc_z22(EBPC_t_q: float, SEBPC_t_1_q: float, t: int, tc: int, z_EBC: int) -> float:
        if 0 < t <= tc and (t % z_EBC) == 0: return EBPC_t_q + SEBPC_t_1_q
        return 0.0

    @staticmethod
    def eebpc_z23(EBPC_t_q: float, SEBPC_t_1_q: float, ECP_t_q: float, SCP_t_1_q: float, t: int, tc: int, T: int, z_EBC: int) -> float:
        if tc < t <= T and (t % z_EBC) == (tc % z_EBC) and SCP_t_1_q > 0:
            return (EBPC_t_q + SEBPC_t_1_q) * (ECP_t_q / SCP_t_1_q)
        return 0.0

    # ==========================================
    # SEBPC: Saldo de Encargos Básicos na Carência do Passivo
    # ==========================================

    @staticmethod
    def sebpc_f1022(SEBPC_t_1_q: float, EBPC_t_q: float, EEBPC_t_q: float, t: int, T: int) -> float:
        if 0 < t <= T: return SEBPC_t_1_q + EBPC_t_q - EEBPC_t_q
        return 0.0

    # ==========================================
    # 4.2 JP: Débito de Juros do Passivo
    # ==========================================

    @staticmethod
    def jp_z24(SDP_t_1_q: float, EBP_t_q: float, i_q: float, n: float, t: int, tc: int, T: int) -> float:
        if tc < t <= T: return (SDP_t_1_q + EBP_t_q) * (((1 + (i_q / 100)) ** (1 / n)) - 1)
        return 0.0

    @staticmethod
    def jp_z25(SDP_t_1_q: float, EBP_t_q: float, i_q: float, DU_t: int, t: int, T: int) -> float:
        if 0 < t <= T: return (SDP_t_1_q + EBP_t_q) * (((1 + (i_q / 100)) ** (DU_t / 252)) - 1)
        return 0.0

    @staticmethod
    def jp_z26(SDP_t_1_q: float, EBP_t_q: float, i_q: float, DC_t: int, t: int, T: int) -> float:
        if 0 < t <= T: return (SDP_t_1_q + EBP_t_q) * (((1 + (i_q / 100)) ** (DC_t / 360)) - 1)
        return 0.0

    @staticmethod
    def jp_z30(SDP_t_1_q: float, EBP_t_q: float, i_q: float, DC_t: int, t: int, T: int) -> float:
        if 0 < t <= T: return (SDP_t_1_q + EBP_t_q) * (i_q / 36000) * DC_t
        return 0.0

    # ==========================================
    # EJP: Exigibilidade de Juros do Passivo
    # ==========================================

    @staticmethod
    def ejp_z43(JP_t_q: float, SJP_t_1_q: float, t: int, tc: int, T: int, z_J: int) -> float:
        if tc < t <= T and (t % z_J) == (tc % z_J): return JP_t_q + SJP_t_1_q
        return 0.0

    @staticmethod
    def ejp_z44(JP_t_q: float, SJP_t_1_q: float, ECP_t_q: float, SCP_t_1_q: float, t: int, tc: int, T: int, z_J: int) -> float:
        if tc < t <= T and (t % z_J) == (tc % z_J) and SCP_t_1_q > 0:
            return (JP_t_q + SJP_t_1_q) * (ECP_t_q / SCP_t_1_q)
        return 0.0

    @staticmethod
    def ejp_z45(JP_t_q: float, SJP_t_1_q: float, PMTP_t_q: float, t: int, tc: int, T: int, z_J: int) -> float:
        if tc < t <= T and (t % z_J) == (tc % z_J):
            return PMTP_t_q if (JP_t_q + SJP_t_1_q) >= PMTP_t_q else (JP_t_q + SJP_t_1_q)
        return 0.0

    @staticmethod
    def ejp_z46(JP_t_q: float, SJP_t_1_q: float, t: int, T: int) -> float:
        if t == T: return SJP_t_1_q + JP_t_q
        return 0.0

    # ==========================================
    # SJP: Saldo de Juros do Passivo
    # ==========================================

    @staticmethod
    def sjp_f1023(SJP_t_1_q: float, JP_t_q: float, EJP_t_q: float, t: int, T: int) -> float:
        if 0 < t <= T: return SJP_t_1_q + JP_t_q - EJP_t_q
        return 0.0

    # ==========================================
    # JPC: Débito de Juros na Carência do Passivo
    # ==========================================

    @staticmethod
    def jpc_z47(SDP_t_1_q: float, EBPC_t_q: float, i_q: float, n: float, t: int, tc: int) -> float:
        if 0 < t <= tc: return (SDP_t_1_q + EBPC_t_q) * (((1 + (i_q / 100)) ** (1 / n)) - 1)
        return 0.0

    @staticmethod
    def jpc_z48(SDP_t_1_q: float, EBPC_t_q: float, i_q: float, DU_t: int, t: int, tc: int) -> float:
        if 0 < t <= tc: return (SDP_t_1_q + EBPC_t_q) * (((1 + (i_q / 100)) ** (DU_t / 252)) - 1)
        return 0.0

    @staticmethod
    def jpc_z49(SDP_t_1_q: float, EBPC_t_q: float, i_q: float, DC_t: int, t: int, tc: int) -> float:
        if 0 < t <= tc: return (SDP_t_1_q + EBPC_t_q) * (((1 + (i_q / 100)) ** (DC_t / 360)) - 1)
        return 0.0

    # ==========================================
    # EJPC: Exigibilidade de Juros na Carência do Passivo
    # ==========================================

    @staticmethod
    def ejpc_z56(PMTP_t_q: float, EJP_t_q: float, SJPC_t_1_q: float, t: int, tc: int, T: int, z_JC: int) -> float:
        if tc < t <= T and (t % z_JC) == (tc % z_JC):
            limite = PMTP_t_q - EJP_t_q
            return limite if SJPC_t_1_q >= limite else SJPC_t_1_q
        return 0.0

    @staticmethod
    def ejpc_z57(JPC_t_q: float, SJPC_t_1_q: float, t: int, tc: int, z_JC: int) -> float:
        if 0 < t <= tc and (t % z_JC) == 0: return JPC_t_q + SJPC_t_1_q
        return 0.0

    # ==========================================
    # SJPC: Saldo de Juros na Carência do Passivo
    # ==========================================

    @staticmethod
    def sjpc_f1024(SJPC_t_1_q: float, JPC_t_q: float, EJPC_t_q: float, t: int, T: int) -> float:
        if 0 < t <= T: return SJPC_t_1_q + JPC_t_q - EJPC_t_q
        return 0.0

    # ==========================================
    # 4.3 CAPITAL (LCP, SCP, ECP)
    # ==========================================

    @staticmethod
    def lcp_z61(w_q: float, C: float, t: int) -> float:
        """Liberação de Capital do Passivo"""
        if t == 0: return (w_q / 100) * C
        return 0.0

    @staticmethod
    def scp_z63(LCP_t_q: float, SCP_t_1_q: float, ECP_t_q: float, t: int, T: int) -> float:
        """Saldo de Capital do Passivo"""
        if t == 0: return LCP_t_q
        elif 0 < t <= T: return SCP_t_1_q - ECP_t_q + LCP_t_q
        return 0.0

    @staticmethod
    def ecp_z65(SCP_t_1_q: float, t: int, tc: int, T: int, z_c: int) -> float:
        """Exigibilidade de Capital do Passivo (SAC)"""
        if tc < t <= T and (t % z_c) == (tc % z_c): return SCP_t_1_q / (((T - t) / z_c) + 1)
        return 0.0

    @staticmethod
    def ecp_z67(PMTP_t_q: float, EJP_t_q: float, EJPC_t_q: float, t: int, tc: int, T: int, z_c: int) -> float:
        """Exigibilidade de Capital do Passivo (Price)"""
        if tc < t <= T and (t % z_c) == (tc % z_c): return PMTP_t_q - EJP_t_q - EJPC_t_q
        return 0.0

    @staticmethod
    def ecp_z68(SCP_t_1_q: float, t: int, T: int) -> float:
        """Exigibilidade no vencimento (Bullet)"""
        if t == T: return SCP_t_1_q
        return 0.0

    # ==========================================
    # 4.4 PRESTAÇÃO (PMTP e PMTRP)
    # ==========================================

    @staticmethod
    def pmtp_z70(EEBP_t_q: float, EEBPC_t_q: float, EJP_t_q: float, EJPC_t_q: float, ECP_t_q: float) -> float:
        """Soma das exigibilidades do Passivo"""
        return EEBP_t_q + EEBPC_t_q + EJP_t_q + EJPC_t_q + ECP_t_q

    @staticmethod
    def pmtp_z71(PMTRP_q: float, fator_ind_DU: float, t: int, tc: int, T: int, z: int) -> float:
        if tc < t <= T and (t % z) == (tc % z): return PMTRP_q * fator_ind_DU
        return 0.0

    @staticmethod
    def pmtrp_z74(w_q: float, C: float, i_q: float, n: float, T: int, t: int, tc: int, z: int) -> float:
        """Prestação Referencial (Sistema Price) do Passivo"""
        if tc < t <= T and (t % z) == (tc % z):
            f_n = (1 + (i_q / 100)) ** (1 / n)
            return (w_q / 100) * C * (((f_n ** T) * (f_n - 1)) / ((f_n ** T) - 1))
        return 0.0

    @staticmethod
    def custo_passivo_z440(SDP_t_1_q: float, taxa_q: float, t: int, T: int) -> float:
        """Z440: Custo de Captação Específico / Remuneração do Passivo"""
        if 0 < t <= T: return SDP_t_1_q * (taxa_q / 100)
        return 0.0

    # ==========================================
    # 4.5 SALDO DEVEDOR (SDP)
    # ==========================================

    @staticmethod
    def sdp_z80(LCP_t_q: float, SDP_t_1_q: float, EBP_t_q: float, EBPC_t_q: float, JP_t_q: float, JPC_t_q: float, PMTP_t_q: float, t: int, T: int) -> float:
        """Saldo Devedor Convencional do Passivo"""
        if t == 0: return LCP_t_q
        elif 0 < t <= T: return SDP_t_1_q + LCP_t_q + EBP_t_q + EBPC_t_q + JP_t_q + JPC_t_q - PMTP_t_q
        return 0.0

    @staticmethod
    def sdp_z81(LCP_t_q: float, SCP_t_q: float, SJP_t_q: float, SJPC_t_q: float, SEBP_t_q: float, SEBPC_t_q: float, t: int, T: int) -> float:
        """Saldo Devedor por Soma de Saldos do Passivo"""
        if t == 0: return LCP_t_q
        elif 0 < t <= T: return SCP_t_q + SJP_t_q + SJPC_t_q + SEBP_t_q + SEBPC_t_q
        return 0.0

    # ============================================================================
    # MÓDULO F: TOTALIZADORES E VALOR PRESENTE DO PASSIVO
    # ============================================================================
    
    @staticmethod
    def vp_pmtp_f1036(PMTP_t_q: float, CVSC_t: float, DU_t: int) -> float:
        """F1036: Valor Presente da Prestação do Passivo (PMTP)"""
        if DU_t == 0: return PMTP_t_q
        return PMTP_t_q / ((1 + (CVSC_t / 100)) ** (DU_t / 252))

    @staticmethod
    def vp_ebp_f1039(EBP_t_q: float, CVSC_t: float, DU_t: int) -> float:
        """F1039: Valor Presente do Encargo Básico do Passivo (EBP)"""
        if DU_t == 0: return EBP_t_q
        return EBP_t_q / ((1 + (CVSC_t / 100)) ** (DU_t / 252))

    @staticmethod
    def vp_jp_f1042(JP_t_q: float, CVSC_t: float, DU_t: int) -> float:
        """F1042: Valor Presente dos Juros do Passivo (JP)"""
        if DU_t == 0: return JP_t_q
        return JP_t_q / ((1 + (CVSC_t / 100)) ** (DU_t / 252))
