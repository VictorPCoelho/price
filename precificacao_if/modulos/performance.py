
class ModuloPerformance:
    """
    6- MÓDULO PERFORMANCE E MÉTODOS ITERATIVOS (COMPLETO E DEFINITIVO)
    Objetivo: Calcular indicadores de rentabilidade, risco e eficiência da operação.
    Estrutura rigorosa do índice do manual (6.1 a 6.16).
    """

    # ==========================================
    # 6.1 RETORNO SOBRE O PATRIMÔNIO LÍQUIDO EXIGIDO (RSPLE)
    # ==========================================
    @staticmethod
    def rsple_f1064(lambda_mg: float, FPRP: float, K_basileia: float, F: float, FCC: float) -> float:
        """F1064: RSPLE Padrão"""
        denominador = FPRP * K_basileia * (1 + (F - 1) * FCC)
        if denominador == 0: return 0.0
        return (lambda_mg / denominador) * 100

    @staticmethod
    def lambda_rsple_f1164(RSPLE: float, FPRP: float, K_basileia: float, F: float, FCC: float) -> float:
        """F1164: Engenharia Reversa (Acha Margem a partir do Retorno Alvo)"""
        return (RSPLE * FPRP * K_basileia * (1 + (F - 1) * FCC)) / 100

    @staticmethod
    def rsple_f1223_eql(lambda_mg: float, FPRP: float, K_basileia: float, FP: float, F: float, FCC: float) -> float:
        """F1223: RSPLE Com Fator de Ponderação (Equalização)"""
        denominador = FPRP * K_basileia * FP * (1 + (F - 1) * FCC)
        if denominador == 0: return 0.0
        return (lambda_mg / denominador) * 100

    # ==========================================
    # 6.2 RETORNO AJUSTADO AO RISCO (RAR)
    # ==========================================
    @staticmethod
    def rar_f1065(lambda_mg: float, CE: float) -> float:
        """F1065: RAR Base"""
        if CE == 0: return 0.0
        return (lambda_mg / CE) * 100

    @staticmethod
    def lambda_rar_f1165(RAR: float, CE: float) -> float:
        """F1165: Engenharia Reversa (Margem a partir do RAR)"""
        return (RAR * CE) / 100

    @staticmethod
    def rar_f1224_eql(lambda_mg: float, CE: float, FP: float) -> float:
        """F1224: RAR com Fator de Ponderação (Equalização)"""
        if (CE * FP) == 0: return 0.0
        return (lambda_mg / (CE * FP)) * 100

    @staticmethod
    def rarsra_f1229(phi_mga: float, Kp: float) -> float:
        """F1229: RAR Sem Receitas Adicionais (Usa MGA e Capital Ponderado)"""
        if Kp == 0: return 0.0
        return (phi_mga / Kp) * 100

    # ==========================================
    # 6.3 ÍNDICE DE EFICIÊNCIA (IE)
    # ==========================================
    @staticmethod
    def indice_eficiencia_ie_f1066(CFVTVP: float, SPVP: float) -> float:
        """F1066: IE (Custo Fixo e Variável a VP / Spread a VP)"""
        if SPVP == 0: return 0.0
        return CFVTVP / SPVP

    # ==========================================
    # 6.4 ÍNDICE DE RISCO (IR)
    # ==========================================
    @staticmethod
    def indice_risco_ir_f1067(EPEVP: float, SPVP: float) -> float:
        """F1067: Índice de Risco Padrão (Perda Esperada a VP / Spread a VP)"""
        if SPVP == 0: return 0.0
        return EPEVP / SPVP

    @staticmethod
    def indice_risco_ir_f1167(EPEVP: float, base_alternativa_vp: float) -> float:
        """F1167: Variação do Índice de Risco (Ex: Sobre Spread + Receitas Adicionais)"""
        if base_alternativa_vp == 0: return 0.0
        return EPEVP / base_alternativa_vp

    # ==========================================
    # 6.5 ÍNDICE DE RENTABILIDADE (IRE)
    # ==========================================
    @staticmethod
    def indice_rentabilidade_ire_f1068(MGVP: float, SPVP: float) -> float:
        """F1068: IRE (Margem de Ganho a VP / Spread a VP)"""
        if SPVP == 0: return 0.0
        return MGVP / SPVP

    # ==========================================
    # 6.6 ÍNDICE DE COBERTURA (IC)
    # ==========================================
    @staticmethod
    def indice_cobertura_ic_f1069(RAVP: float, CFVTVP: float) -> float:
        """F1069: IC (Receitas Adicionais a VP / Custos a VP)"""
        if CFVTVP == 0: return 0.0
        return RAVP / CFVTVP

    # ==========================================
    # 6.7 TAXA INTERNA DE RETORNO (TIR)
    # ==========================================
    @staticmethod
    def funcao_objetivo_tir_f1095(chute_tir: float, FLD_t: float, ECA_t: float, dct: int) -> float:
        """F1095: TIR Base (Método Iterativo usando Fluxo D)"""
        fator_desconto = (1 + (chute_tir / 100)) ** (dct / 360)
        return (FLD_t / fator_desconto) - ECA_t

    @staticmethod
    def funcao_objetivo_tir_sr_f1238(chute_tir: float, FLC_t: float, ECA_t: float, dct: int) -> float:
        """F1238: TIR Sem Receitas Adicionais (Método Iterativo usando Fluxo C)"""
        fator_desconto = (1 + (chute_tir / 100)) ** (dct / 360)
        return (FLC_t / fator_desconto) - ECA_t

    # ==========================================
    # 6.8 TAXA PONTO DE PARTIDA (TPP)
    # ==========================================
    @staticmethod
    def funcao_objetivo_tpp_f1096(chute_tpp: float, FLE_t: float, ECA_t: float, dct: int) -> float:
        """F1096: TPP (Método Iterativo usando Fluxo E - Passivo)"""
        fator_desconto = (1 + (chute_tpp / 100)) ** (dct / 360)
        return (FLE_t / fator_desconto) - ECA_t

    # ==========================================
    # 6.9 PERCENTUAL DO CDI (PCDI)
    # ==========================================
    @staticmethod
    def funcao_objetivo_pcdi_f1097(chute_pcdi: float, FLC_t: float, CVSC_t: float, ECA_t: float, dut: int) -> float:
        """F1097: % do CDI Base (Método Iterativo com base 252 sobre Fluxo C)"""
        fator_curva = ((1 + (CVSC_t / 100)) ** (1 / 252)) - 1
        base_desconto = (fator_curva * (chute_pcdi / 100)) + 1
        return (FLC_t / (base_desconto ** dut)) - ECA_t

    # ==========================================
    # 6.10 PERCENTUAL DO CDI ALL IN (PCDIAI)
    # ==========================================
    @staticmethod
    def funcao_objetivo_pcdiai_f1098(chute_pcdiai: float, FLD_t: float, CVSC_t: float, ECA_t: float, dut: int) -> float:
        """F1098: % do CDI All In (Método Iterativo com base 252 sobre Fluxo D)"""
        fator_curva = ((1 + (CVSC_t / 100)) ** (1 / 252)) - 1
        base_desconto = (fator_curva * (chute_pcdiai / 100)) + 1
        return (FLD_t / (base_desconto ** dut)) - ECA_t

    # ==========================================
    # 6.11 DURATION (DRT)
    # ==========================================
    @staticmethod
    def duration_drt_f1204(soma_t_PMTA_desc: float, soma_PMTA_desc: float) -> float:
        """F1204 / F1205: DRT (Soma ponderada do tempo pelo PMTA descontado)"""
        if soma_PMTA_desc == 0: return 0.0
        return soma_t_PMTA_desc / soma_PMTA_desc

    # ==========================================
    # 6.12 PRAZO MÉDIO (PM) / VIDA MÉDIA
    # ==========================================
    @staticmethod
    def prazo_medio_pm_f1206(soma_t_PMTA: float, soma_PMTA: float) -> float:
        """F1206: Prazo Médio (Soma do tempo ponderado pelas parcelas / Soma das parcelas)"""
        if soma_PMTA == 0: return 0.0
        return soma_t_PMTA / soma_PMTA

# ==========================================
    # 6.13 VALOR AGREGADO / LUGRO ECONÔMICO (EVA / VA)
    # ==========================================
    @staticmethod
    def valor_agregado_va_f1208(MGVP: float, custo_capital_vp: float) -> float:
        """F1208: Geração de Valor Econômico (Margem a VP menos o Custo de Capital a VP)"""
        return MGVP - custo_capital_vp

    @staticmethod
    def valor_agregado_sra_f1209(MGA_VP: float, custo_capital_vp: float) -> float:
        """F1209: Geração de Valor Econômico Sem Receitas Adicionais (MGA a VP - Custo de Capital a VP)"""
        return MGA_VP - custo_capital_vp

    # ==========================================
    # 6.14 e 6.15 RAR GESTÃO E RAR PRUDENCIAL
    # ==========================================
    @staticmethod
    def rar_gestao_f1183(lambda_mg: float, CEIRB: float) -> float:
        """F1183: RAR Gestão usando Capital Econômico IRB"""
        if CEIRB == 0: return 0.0
        return (lambda_mg / CEIRB) * 100

    @staticmethod
    def rar_gestao_sra_f1230(phi_mga: float, CEIRB: float) -> float:
        """F1230: RAR Gestão Sem Receitas Adicionais"""
        if CEIRB == 0: return 0.0
        return (phi_mga / CEIRB) * 100

    @staticmethod
    def capital_ponderado_kp_f1212(soma_SDA_K_FPR: float, soma_SDA: float) -> float:
        """F1212: Capital Ponderado Kp"""
        if soma_SDA == 0: return 0.0
        return soma_SDA_K_FPR / soma_SDA

    @staticmethod
    def rar_prudencial_rarp_f1213(lambda_mg: float, Kp: float) -> float:
        """F1213: RAR Prudencial"""
        if Kp == 0: return 0.0
        return (lambda_mg / Kp) * 100

    # ==========================================
    # 6.16 SPREAD EM TAXA (SPTX)
    # ==========================================
    @staticmethod
    def funcao_objetivo_sptx_f1233(chute_sptx: float, FLF_t: float, ECA_t: float, dct: int) -> float:
        """F1233: SPTX (Método Iterativo usando Fluxo F - Sem Margem de Ganho)"""
        fator_desconto = (1 + (chute_sptx / 100)) ** (dct / 360)
        return (FLF_t / fator_desconto) - ECA_t
