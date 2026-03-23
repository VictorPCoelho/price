
class ModuloMetodosIterativos:
    """
    7- MÓDULO MÉTODOS ITERATIVOS (SOLVER)
    Objetivo: Encontrar as taxas implícitas (TIR, TPP, PCDI, SPTX) através de algoritmos
    de busca numérica (Método da Secante), zerando as funções objetivo do Módulo 6.
    """

    @staticmethod
    def solver_secante(funcao_objetivo, kwargs_funcao: dict, nome_variavel_alvo: str, chute_0: float = 0.1, chute_1: float = 5.0, tol: float = 1e-6, max_iter: int = 100) -> float:
        """
        Algoritmo numérico da Secante para encontrar a raiz de uma função (onde resultado = 0).
        
        :param funcao_objetivo: A função matemática do Módulo 6 (ex: funcao_objetivo_tir_f1095).
        :param kwargs_funcao: Dicionário com os argumentos da função (ex: {'FLD_t': 1000, 'ECA_t': 900, 'dct': 30}).
        :param nome_variavel_alvo: O nome do parâmetro da taxa que o motor vai alterar (ex: 'chute_tir').
        :param chute_0: Primeira estimativa de taxa (ex: 0.1%).
        :param chute_1: Segunda estimativa de taxa (ex: 5.0%).
        :param tol: Tolerância de erro (precisão exigida, ex: 0.000001).
        :param max_iter: Limite de repetições de segurança para evitar loop infinito.
        :return: A taxa exata em % que zera a função.
        """
        x0 = chute_0
        x1 = chute_1

        for iteracao in range(max_iter):
            # Injeta o Chute 0 na função e calcula
            kwargs_0 = kwargs_funcao.copy()
            kwargs_0[nome_variavel_alvo] = x0
            f0 = funcao_objetivo(**kwargs_0)

            # Injeta o Chute 1 na função e calcula
            kwargs_1 = kwargs_funcao.copy()
            kwargs_1[nome_variavel_alvo] = x1
            f1 = funcao_objetivo(**kwargs_1)

            # Trava de segurança: se a função for flat (f1 == f0), evita divisão por zero
            if f1 - f0 == 0:
                return x1

            # Fórmula Matemática da Secante para encontrar o próximo chute (x2)
            # Aproxima-se da raiz usando a inclinação da reta entre os dois últimos pontos
            x2 = x1 - f1 * ((x1 - x0) / (f1 - f0))

            # Verifica se atingimos a precisão exigida pelo banco (tolerância)
            if abs(x2 - x1) < tol:
                return x2

            # Atualiza os chutes para a próxima iteração
            x0 = x1
            x1 = x2

        # Se ultrapassar o limite de iterações sem encontrar o zero, levanta um erro claro
        raise ValueError(f"Erro no Motor: A taxa iterativa não convergiu após {max_iter} tentativas. Verifique se os fluxos de caixa e o ECA possuem sinais opostos.")

    # ==========================================
    # FACILITADORES DE EXECUÇÃO
    # (Funções prontas para chamar o Solver para as principais taxas)
    # ==========================================

    @classmethod
    def encontrar_tir(cls, funcao_tir_modulo6, FLD_t: float, ECA_t: float, dct: int) -> float:
        """Encontra a TIR iterativamente."""
        kwargs = {'FLD_t': FLD_t, 'ECA_t': ECA_t, 'dct': dct}
        return cls.solver_secante(funcao_tir_modulo6, kwargs, 'chute_tir')

    @classmethod
    def encontrar_tpp(cls, funcao_tpp_modulo6, FLE_t: float, ECA_t: float, dct: int) -> float:
        """Encontra a Taxa Ponto de Partida (TPP) iterativamente."""
        kwargs = {'FLE_t': FLE_t, 'ECA_t': ECA_t, 'dct': dct}
        return cls.solver_secante(funcao_tpp_modulo6, kwargs, 'chute_tpp')

    @classmethod
    def encontrar_sptx(cls, funcao_sptx_modulo6, FLF_t: float, ECA_t: float, dct: int) -> float:
        """Encontra o Spread em Taxa (SPTX) iterativamente."""
        kwargs = {'FLF_t': FLF_t, 'ECA_t': ECA_t, 'dct': dct}
        return cls.solver_secante(funcao_sptx_modulo6, kwargs, 'chute_sptx')
