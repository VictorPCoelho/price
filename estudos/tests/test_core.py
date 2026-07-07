from datetime import date

from app.core import ciclo, edital, estatisticas, prioridade, revisao


# ---------------------------------------------------------------- edital
def test_parse_topicos_quebra_por_linha_e_ponto_e_virgula():
    texto = (
        "1. Atos administrativos: conceito; requisitos; atributos\n"
        "2. Poderes da administração\n"
        "\n"
        "3. Licitações (Lei 14.133/2021)"
    )
    topicos = edital.parse_topicos(texto)
    assert topicos == [
        "1. Atos administrativos: conceito",
        "requisitos",
        "atributos",
        "2. Poderes da administração",
        "3. Licitações (Lei 14.133/2021)",
    ]


def test_parse_topicos_ignora_vazios_e_duplicados():
    assert edital.parse_topicos("Atos;;Atos\n  \n- Atos") == ["Atos"]


def test_parse_topicos_texto_vazio():
    assert edital.parse_topicos("") == []


# ---------------------------------------------------------------- ciclo
def test_ciclo_circular():
    assert ciclo.indice_bloco_atual(3, 0) == 0
    assert ciclo.indice_bloco_atual(3, 5) == 2
    assert ciclo.avancar(3, 2) == 0
    assert ciclo.avancar(3, 0) == 1


def test_ciclo_vazio():
    assert ciclo.indice_bloco_atual(0, 4) is None
    assert ciclo.avancar(0, 4) == 0


# ---------------------------------------------------------------- revisão
def test_agendar_revisoes_1_7_30():
    base = date(2026, 7, 1)
    assert revisao.agendar(base) == [
        (1, date(2026, 7, 2)),
        (7, date(2026, 7, 8)),
        (30, date(2026, 7, 31)),
    ]


def test_reagendamento_por_resultado():
    hoje = date(2026, 7, 10)
    assert revisao.reagendamento(7, "esqueci", hoje) == (7, date(2026, 7, 11))
    assert revisao.reagendamento(7, "parcial", hoje) == (7, date(2026, 7, 13))
    assert revisao.reagendamento(7, "lembrei", hoje) is None


# ---------------------------------------------------------------- prioridade
def test_proficiencia_exige_amostra_minima():
    assert prioridade.proficiencia(3, 3) == 0.0
    assert prioridade.proficiencia(10, 8) == 0.8


def test_urgencia_cresce_perto_da_prova():
    assert prioridade.urgencia(None) == 1.0
    assert prioridade.urgencia(200) == 1.0
    assert prioridade.urgencia(0) == 2.0
    assert 1.0 < prioridade.urgencia(45) < 2.0


def test_ordenar_topicos_prioriza_fraco_e_pesado():
    fraco_pesado = prioridade.TopicoInfo(
        1, "Atos", peso_relativo=0.3, questoes_feitas=10, questoes_acertadas=3
    )
    forte_pesado = prioridade.TopicoInfo(
        2, "Poderes", peso_relativo=0.3, questoes_feitas=10, questoes_acertadas=9
    )
    fraco_leve = prioridade.TopicoInfo(
        3, "Regimento", peso_relativo=0.05, questoes_feitas=10, questoes_acertadas=3
    )
    ordenados = prioridade.ordenar_topicos(
        [forte_pesado, fraco_leve, fraco_pesado], dias_para_prova=None
    )
    # fraco+pesado dispara na frente; o quase-dominado cai para o fim mesmo pesado
    assert ordenados[0].id == 1
    assert ordenados[-1].id == 2
    assert ordenados[0].score > 5 * ordenados[-1].score


def test_topico_dominado_sai_da_frente():
    dominado = prioridade.TopicoInfo(1, "A", status="dominado")
    novo = prioridade.TopicoInfo(2, "B", status="nao_visto")
    ordenados = prioridade.ordenar_topicos([dominado, novo], None)
    assert ordenados[0].id == 2


def test_novo_status_progressao():
    assert prioridade.novo_status("teoria_vista", 0, 0) == "teoria_vista"
    assert prioridade.novo_status("teoria_vista", 6, 3) == "exercitado"
    assert prioridade.novo_status("exercitado", 12, 10) == "dominado"
    # regressão: dominado que passa a errar volta a exercitado
    assert prioridade.novo_status("dominado", 20, 12) == "exercitado"
    # questões sem teoria vista não mudam o status
    assert prioridade.novo_status("nao_visto", 6, 3) == "nao_visto"


# ---------------------------------------------------------------- estatísticas
def test_streak_conta_dias_consecutivos():
    hoje = date(2026, 7, 10)
    dias = {date(2026, 7, 10), date(2026, 7, 9), date(2026, 7, 8), date(2026, 7, 5)}
    assert estatisticas.streak(dias, hoje) == 3


def test_streak_nao_quebra_se_hoje_ainda_nao_estudou():
    hoje = date(2026, 7, 10)
    dias = {date(2026, 7, 9), date(2026, 7, 8)}
    assert estatisticas.streak(dias, hoje) == 2


def test_streak_zerado():
    assert estatisticas.streak({date(2026, 7, 1)}, date(2026, 7, 10)) == 0
    assert estatisticas.streak(set(), date(2026, 7, 10)) == 0


def test_minutos_por_semana():
    hoje = date(2026, 7, 8)  # quarta; segunda = 6/jul
    sessoes = [
        (date(2026, 7, 7), 60),
        (date(2026, 7, 6), 30),
        (date(2026, 6, 30), 45),  # semana de 29/jun
        (date(2026, 1, 1), 999),  # fora da janela
    ]
    resultado = estatisticas.minutos_por_semana(sessoes, hoje, semanas=4)
    assert list(resultado.values()) == [0, 0, 45, 90]
    assert list(resultado.keys())[-1] == date(2026, 7, 6)


def test_cobertura_e_percentual():
    status = ["nao_visto", "teoria_vista", "dominado", "nao_visto"]
    assert estatisticas.cobertura(status) == {
        "nao_visto": 2,
        "teoria_vista": 1,
        "exercitado": 0,
        "dominado": 1,
    }
    assert estatisticas.percentual_visto(status) == 50.0
    assert estatisticas.percentual_visto([]) == 0.0


def test_taxa_acerto():
    assert estatisticas.taxa_acerto(0, 0) is None
    assert estatisticas.taxa_acerto(10, 7) == 70.0
