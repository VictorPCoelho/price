
class ModuloEncargos:
    """
    2- MÓDULO ENCARGOS
    Objetivo: Transformações no formato da taxa de juros, sobretaxa ou indexador.
    """

    # ==========================================
    # 2.1 TAXAS DO ATIVO
    # ==========================================
    
    @staticmethod
    def taxa_padrao_f1070(TX_k: float) -> float:
        """Taxa Padrão (Default) - F1070"""
        return TX_k

    @staticmethod
    def taxa_efetiva_f1071(TN_k: float, n: float, ND: float, NC: float) -> float:
        """Taxa Efetiva - F1071"""
        base = 1 + (TN_k / (n * 100))
        expoente = ND / NC
        return ((base ** expoente) - 1) * 100

    @staticmethod
    def taxas_equivalentes_f1072(TC: float, ND: float, NC: float) -> float:
        """Taxas Equivalentes - F1072"""
        base = 1 + (TC / 100)
        expoente = ND / NC
        return ((base ** expoente) - 1) * 100

    @staticmethod
    def taxas_proporcionais_f1073(TC_b_k: float, b: float, g: float) -> float:
        """Taxas Proporcionais - F1073"""
        return TC_b_k / (b / g)

    @staticmethod
    def taxa_nominal_desconto_f1074(ie_p_k: float, DCT: float, P: float) -> float:
        """Taxa Nominal de Desconto - F1074"""
        fator = (1 + (ie_p_k / 100)) ** (DCT / P)
        return ((fator - 1) / fator) * 100

    @staticmethod
    def taxa_efetiva_desconto_f1075(TN_k: float, DCT: float, P: float) -> float:
        """Taxa Efetiva de Desconto - F1075"""
        numerador = 1 + ((TN_k / 100) * (DCT / 30))
        denominador = 1 - ((TN_k / 100) * (DCT / 30))
        fator = numerador / denominador
        return ((fator ** (P / DCT)) - 1) * 100

    @staticmethod
    def taxa_efetiva_desconto_z405(i_d: float, DCT: float) -> float:
        """Fórmula Adicional - Z405"""
        return i_d / (1 - ((i_d * DCT) / 3000))

    @staticmethod
    def taxa_composta_ativo_f1076(ind_t_k: float, i_q: float, i_k: float) -> float:
        """Taxa Composta do Ativo - F1076"""
        return ind_t_k + i_q + i_k

    @staticmethod
    def taxa_desconto_internacional_f1194(TN_k: float, DCT: float, P: float, TDESC: int) -> float:
        """Taxa de Desconto Internacional - F1194"""
        if TDESC == 1:
            return TN_k
        elif TDESC == 0:
            fator = 1 - ((TN_k / 100) * (DCT / 360))
            return ((1 / fator) - 1) * (P / DCT) * 100
        return 0.0

    @staticmethod
    def taxa_efetiva_anual_desconto_f1207(I_d: float, DCT: float) -> float:
        """Taxa Efetiva Anual (Desconto) Base 365 - F1207"""
        fator = 1 - ((I_d * DCT) / 3000)
        return (((1 / fator) ** (365 / DCT)) - 1) * 100

    @staticmethod
    def taxa_efetiva_anual_desconto_f1208(I_d: float, DCT: float, DAC: float) -> float:
        """Taxa Efetiva Anual (Desconto) Base DAC - F1208"""
        fator = 1 - ((I_d * DCT) / 3000)
        return (((1 / fator) ** (DAC / DCT)) - 1) * 100

    @staticmethod
    def taxa_libor_a_termo_f1210(INDEX_T_k: float, DCT: float, INDEX_t_linha_k: float, dc_t_linha: float) -> float:
        """Taxa Libor a Termo - F1210"""
        numerador = ((INDEX_T_k / 100) * DCT) - ((INDEX_t_linha_k / 100) * dc_t_linha)
        denominador = DCT - dc_t_linha
        return (numerador / denominador) * 100

    @staticmethod
    def taxa_desconto_internacional_f1211(TN: float, LT: float, DCT: float, dc_t_linha: float, t: int, TDESC: int) -> float:
        """Taxa de Desconto Internacional - F1211"""
        if t == 0 and TDESC == 0:
            fator = 1 - (((TN + LT) / 100) * ((DCT - dc_t_linha) / 360))
            return ((((1 / fator) - 1) * (360 / (DCT - dc_t_linha))) * 100) - LT
        elif t == 0 and TDESC == 1:
            ST = TN - LT
            return ST
        return 0.0

    # ==========================================
    # 2.2 TAXAS DO PASSIVO
    # ==========================================
    
    @staticmethod
    def taxa_padrao_passivo_f1077(TX_q: float) -> float:
        """Taxa Padrão (Default) - F1077"""
        return TX_q

    @staticmethod
    def taxa_efetiva_passivo_f1078(TN_q: float, n: float, ND: float, NC: float) -> float:
        """Taxa Efetiva - F1078"""
        base = 1 + (TN_q / (n * 100))
        expoente = ND / NC
        return ((base ** expoente) - 1) * 100

    @staticmethod
    def taxas_equivalentes_passivo_f1079(TC: float, ND: float, NC: float) -> float:
        """Taxas Equivalentes - F1079"""
        base = 1 + (TC / 100)
        expoente = ND / NC
        return ((base ** expoente) - 1) * 100

    @staticmethod
    def taxas_proporcionais_passivo_f1080(TC_b_q: float, b: float, g: float) -> float:
        """Taxas Proporcionais - F1080"""
        return TC_b_q / (b / g)

    @staticmethod
    def taxa_composta_passivo_f1081(ind_t_q: float, i_q: float) -> float:
        """Taxa Composta do Passivo - F1081"""
        return ind_t_q + i_q

    @staticmethod
    def taxa_da_poupanca_f1102(TX_q: float, CVCC_t: float) -> float:
        """Taxa da Poupança - F1102"""
        if CVCC_t > 8.50:
            return TX_q
        else:
            return (70 / 100) * CVCC_t

    # ==========================================
    # 2.3 INDEXADORES DO ATIVO
    # ==========================================
    
    @staticmethod
    def indexador_padrao_ativo_f1082(INDEX_t_k: float) -> float:
        """Indexador Padrão (Default) - F1082"""
        return INDEX_t_k

    @staticmethod
    def taxas_a_termo_ativo_f1083(t: int, T: int, INDEX_1_k: float, INDEX_t_k: float, INDEX_t_1_k: float, du_t: float, du_t_1: float) -> float:
        """Taxas a Termo - F1083"""
        if t == 0:
            return 0.0
        elif t == 1:
            return INDEX_1_k
        elif 1 < t <= T:
            numerador = (1 + (INDEX_t_k / 100)) ** (du_t / 252)
            denominador = (1 + (INDEX_t_1_k / 100)) ** (du_t_1 / 252)
            fator = numerador / denominador
            expoente = 252 / (du_t - du_t_1)
            return ((fator ** expoente) - 1) * 100
        return 0.0

    @staticmethod
    def taxas_a_termo_ao_mes_ativo_f1090(t: int, T: int, INDEX_1_k: float, INDEX_t_k: float, INDEX_t_1_k: float, du_1: float, du_t: float, du_t_1: float) -> float:
        """Taxas a Termo ao Mês - F1090"""
        if t == 0:
            return 0.0
        elif t == 1:
            return (((1 + (INDEX_1_k / 100)) ** (du_1 / 252)) - 1) * 100
        elif 1 < t <= T:
            numerador = (1 + (INDEX_t_k / 100)) ** (du_t / 252)
            denominador = (1 + (INDEX_t_1_k / 100)) ** (du_t_1 / 252)
            return ((numerador / denominador) - 1) * 100
        return 0.0

    @staticmethod
    def taxas_a_termo_int_1_ativo_f1197(t: int, T: int, INDEX_1_k: float, INDEX_t_k: float, INDEX_t_1_k: float, dct_t: float, dct_t_1: float) -> float:
        """Taxas a Termo (Área Internacional 1) - F1197"""
        if t == 0:
            return 0.0
        elif t == 1:
            return INDEX_1_k
        elif 1 < t <= T:
            numerador = 1 + ((INDEX_t_k / 100) * (dct_t / 360))
            denominador = 1 + ((INDEX_t_1_k / 100) * (dct_t_1 / 360))
            fator = numerador / denominador
            return (fator - 1) * (360 / (dct_t - dct_t_1)) * 100
        return 0.0

    @staticmethod
    def taxas_a_termo_int_2_ativo_f1198(t: int, T: int, INDEX_1_k: float, INDEX_t_k: float, INDEX_t_1_k: float, DCT_t: float, DCT_t_1: float) -> float:
        """Taxas a Termo (Área Internacional 2) - F1198"""
        if t == 0:
            return 0.0
        elif t == 1:
            return INDEX_1_k
        elif 1 < t <= T:
            numerador = ((INDEX_t_k / 100) * DCT_t) - ((INDEX_t_1_k / 100) * DCT_t_1)
            denominador = DCT_t - DCT_t_1
            return (numerador / denominador) * 100
        return 0.0

    # ==========================================
    # 2.4 INDEXADORES DO PASSIVO
    # ==========================================
    
    @staticmethod
    def indexador_padrao_passivo_f1087(INDEX_t_q: float) -> float:
        """Indexador Padrão (Default) - F1087"""
        return INDEX_t_q

    @staticmethod
    def taxas_a_termo_passivo_f1088(t: int, T: int, INDEX_1_q: float, INDEX_t_q: float, INDEX_t_1_q: float, du_t: float, du_t_1: float) -> float:
        """Taxas a Termo - F1088"""
        if t == 0:
            return 0.0
        elif t == 1:
            return INDEX_1_q
        elif 1 < t <= T:
            numerador = (1 + (INDEX_t_q / 100)) ** (du_t / 252)
            denominador = (1 + (INDEX_t_1_q / 100)) ** (du_t_1 / 252)
            fator = numerador / denominador
            expoente = 252 / (du_t - du_t_1)
            return ((fator ** expoente) - 1) * 100
        return 0.0

    @staticmethod
    def taxas_a_termo_ao_mes_passivo_f1091(t: int, T: int, INDEX_1_q: float, INDEX_t_q: float, INDEX_t_1_q: float, du_1: float, du_t: float, du_t_1: float) -> float:
        """Taxas a Termo ao Mês - F1091"""
        if t == 0:
            return 0.0
        elif t == 1:
            return (((1 + (INDEX_1_q / 100)) ** (du_1 / 252)) - 1) * 100
        elif 1 < t <= T:
            numerador = (1 + (INDEX_t_q / 100)) ** (du_t / 252)
            denominador = (1 + (INDEX_t_1_q / 100)) ** (du_t_1 / 252)
            return ((numerador / denominador) - 1) * 100
        return 0.0

    @staticmethod
    def taxas_a_termo_int_1_passivo_f1195(t: int, T: int, INDEX_1_q: float, INDEX_t_q: float, INDEX_t_1_q: float, dct_t: float, dct_t_1: float) -> float:
        """Taxas a Termo (Área Internacional 1) - F1195"""
        if t == 0:
            return 0.0
        elif t == 1:
            return INDEX_1_q
        elif 1 < t <= T:
            numerador = 1 + ((INDEX_t_q / 100) * (dct_t / 360))
            denominador = 1 + ((INDEX_t_1_q / 100) * (dct_t_1 / 360))
            fator = numerador / denominador
            return (fator - 1) * (360 / (dct_t - dct_t_1)) * 100
        return 0.0

    @staticmethod
    def taxas_a_termo_int_2_passivo_f1196(t: int, T: int, INDEX_1_q: float, INDEX_t_q: float, INDEX_t_1_q: float, DCT_t: float, DCT_t_1: float) -> float:
        """Taxas a Termo (Área Internacional 2) - F1196"""
        if t == 0:
            return 0.0
        elif t == 1:
            return INDEX_1_q
        elif 1 < t <= T:
            numerador = ((INDEX_t_q / 100) * DCT_t) - ((INDEX_t_1_q / 100) * DCT_t_1)
            denominador = DCT_t - DCT_t_1
            return (numerador / denominador) * 100
        return 0.0
