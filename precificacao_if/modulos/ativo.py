
import math

class ModuloAtivo:
    """
    3- MÓDULO ATIVO (COMPLETO E DEFINITIVO)
    Objetivo: Apurar a receita financeira, movimentação de capital, exigibilidades e saldos.
    Reúne as fórmulas do Ativo (Z) e os Totalizadores de Valor Presente (F1026 a F1217).
    """

    # ==========================================
    # 3.1 EBA: Débito de Encargos Básicos
    # ==========================================
    @staticmethod
    def eba_z1(SDA_t_1_k: float, ind_t_k: float, t: int, tc: int, T: int) -> float:
        if tc < t <= T: return SDA_t_1_k * (ind_t_k / 100)
        return 0.0

    @staticmethod
    def eba_z2(SDA_t_1_k: float, ind_t_k: float, n: float, t: int, tc: int, T: int) -> float:
        if tc < t <= T: return SDA_t_1_k * (((1 + (ind_t_k / 100)) ** (1 / n)) - 1)
        return 0.0

    @staticmethod
    def eba_z3(SDA_t_1_k: float, ind_t_k: float, DU_t: int, t: int, T: int) -> float:
        if 0 < t <= T: return SDA_t_1_k * (((1 + (ind_t_k / 100)) ** (DU_t / 252)) - 1)
        return 0.0

    # ==========================================
    # 3.2 JA: Juros do Ativo
    # ==========================================
    @staticmethod
    def ja_z15(SDA_t_1: float, i: float, n: float, t: int, tc: int, T: int) -> float:
        if tc < t <= T: return SDA_t_1 * (((1 + (i / 100)) ** (1 / n)) - 1)
        return 0.0

    @staticmethod
    def ja_z16(SDA_t_1: float, i: float, DU_t: int, t: int, T: int) -> float:
        if 0 < t <= T: return SDA_t_1 * (((1 + (i / 100)) ** (DU_t / 252)) - 1)
        return 0.0

    @staticmethod
    def ja_z17(SDA_t_1: float, i: float, DC_t: int, t: int, T: int) -> float:
        if 0 < t <= T: return SDA_t_1 * (((1 + (i / 100)) ** (DC_t / 360)) - 1)
        return 0.0

    # ==========================================
    # 3.3 PMTA: Prestação do Ativo
    # ==========================================
    @staticmethod
    def pmta_z30(SDA_t_1: float, EBA_t: float, JA_t: float, t: int, T: int) -> float:
        if 0 < t < T: return 0.0
        if t == T: return SDA_t_1 + EBA_t + JA_t
        return 0.0

    @staticmethod
    def pmta_z31(SDA_t_1: float, EBA_t: float, JA_t: float, t: int, z: int, T: int) -> float:
        if 0 < t <= T and (t % z) == 0: return SDA_t_1 + EBA_t + JA_t
        return 0.0

    @staticmethod
    def pmta_z32(SDA_0: float, EBA_t: float, JA_t: float, n: float, t: int, T: int) -> float:
        if 0 < t <= T: return (SDA_0 / n) + EBA_t + JA_t
        return 0.0

    # ==========================================
    # 3.4 SDA: Saldo Devedor do Ativo
    # ==========================================
    @staticmethod
    def sda_z45(SDA_t_1: float, EBA_t: float, JA_t: float, PMTA_t: float, t: int, T: int) -> float:
        if 0 < t <= T: return SDA_t_1 + EBA_t + JA_t - PMTA_t
        return 0.0

    @staticmethod
    def sda_z46(SDA_t_1: float, EBA_t: float, PMTA_t: float, t: int, T: int) -> float:
        if 0 < t <= T: return SDA_t_1 + EBA_t - PMTA_t
        return 0.0

    # ==========================================
    # 3.5 DESPESA DE PROVISÃO E AMORTIZAÇÃO
    # ==========================================
    @staticmethod
    def dpro_z93(VB: float, DPRO_t_1: float, DPR_t: float, t: int, T: int) -> float:
        if t == 0: return VB
        elif 0 < t <= T: return DPRO_t_1 - DPR_t
        return 0.0

    @staticmethod
    def daa_z94(DPR_t: float, DAA_t_1: float, t: int, T: int) -> float:
        if 0 < t <= T: return DAA_t_1 + DPR_t
        return 0.0

    # ==========================================
    # 3.7 OPERAÇÕES DE DESCONTO
    # ==========================================
    @staticmethod
    def vd_z96(VN: float, fator_d: float, t: int) -> float:
        if t == 0: return VN * fator_d
        return 0.0

    @staticmethod
    def vd_z97(VN: float, T_desp: float, fator_d: float, t: int) -> float:
        if t == 0: return (VN - T_desp) * fator_d
        return 0.0

    @staticmethod
    def vd_z98(VN: float, fator_d: float, T_desp: float, t: int) -> float:
        if t == 0: return (VN * fator_d) - T_desp
        return 0.0

    # ============================================================================
    # MÓDULO F: TOTALIZADORES E VALOR PRESENTE (INCLUSÃO DAS FÓRMULAS AUSENTES)
    # Trazem os fluxos do ativo para o momento zero (t=0) usando a Curva de Desconto
    # ============================================================================

    @staticmethod
    def vp_pmta_f1026(PMTA_t: float, CVSC_t: float, DU_t: int) -> float:
        """F1026: Valor Presente da Prestação do Ativo (PMTA)"""
        if DU_t == 0: return PMTA_t
        return PMTA_t / ((1 + (CVSC_t / 100)) ** (DU_t / 252))

    @staticmethod
    def vp_eba_f1027(EBA_t: float, CVSC_t: float, DU_t: int) -> float:
        """F1027: Valor Presente do Encargo Básico do Ativo (EBA)"""
        if DU_t == 0: return EBA_t
        return EBA_t / ((1 + (CVSC_t / 100)) ** (DU_t / 252))

    @staticmethod
    def vp_ja_f1030(JA_t: float, CVSC_t: float, DU_t: int) -> float:
        """F1030: Valor Presente dos Juros do Ativo (JA)"""
        if DU_t == 0: return JA_t
        return JA_t / ((1 + (CVSC_t / 100)) ** (DU_t / 252))

    @staticmethod
    def vp_sda_f1031(SDA_t: float, CVSC_t: float, DU_t: int) -> float:
        """F1031: Valor Presente do Saldo Devedor do Ativo (SDA)"""
        if DU_t == 0: return SDA_t
        return SDA_t / ((1 + (CVSC_t / 100)) ** (DU_t / 252))

    @staticmethod
    def vp_tac_f1033(TAC_t: float, CVSC_t: float, DU_t: int) -> float:
        """F1033: Valor Presente das Tarifas (TAC)"""
        if DU_t == 0: return TAC_t
        return TAC_t / ((1 + (CVSC_t / 100)) ** (DU_t / 252))

    @staticmethod
    def vp_seg_f1034(SEG_t: float, CVSC_t: float, DU_t: int) -> float:
        """F1034: Valor Presente dos Seguros Financeiros (SEG)"""
        if DU_t == 0: return SEG_t
        return SEG_t / ((1 + (CVSC_t / 100)) ** (DU_t / 252))

    @staticmethod
    def vp_iof_f1035(IOF_t: float, CVSC_t: float, DU_t: int) -> float:
        """F1035: Valor Presente do IOF Retido/Financiado"""
        if DU_t == 0: return IOF_t
        return IOF_t / ((1 + (CVSC_t / 100)) ** (DU_t / 252))

    @staticmethod
    def vp_dpr_f1199(DPR_t: float, CVSC_t: float, DU_t: int) -> float:
        """F1199: Valor Presente da Despesa de Provisão de Risco"""
        if DU_t == 0: return DPR_t
        return DPR_t / ((1 + (CVSC_t / 100)) ** (DU_t / 252))

    @staticmethod
    def vp_subv_f1216(SUBV_t: float, CVSC_t: float, DU_t: int) -> float:
        """F1216: Valor Presente de Subvenções Governamentais/Especiais"""
        if DU_t == 0: return SUBV_t
        return SUBV_t / ((1 + (CVSC_t / 100)) ** (DU_t / 252))

    @staticmethod
    def vp_eql_f1217(EQL_t: float, CVSC_t: float, DU_t: int) -> float:
        """F1217: Valor Presente da Equalização de Taxas"""
        if DU_t == 0: return EQL_t
        return EQL_t / ((1 + (CVSC_t / 100)) ** (DU_t / 252))
