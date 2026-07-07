"""Teste de ponta a ponta: percorre o fluxo real pelo HTTP, do zero até a revisão."""
import os
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def cliente(tmp_path, monkeypatch):
    monkeypatch.setenv("ESTUDOS_DB", str(tmp_path / "teste.db"))
    from app.web.main import criar_app

    return TestClient(criar_app(), follow_redirects=True)


def test_fluxo_completo(cliente):
    # 0. sem concurso, a raiz manda para o cadastro
    resposta = cliente.get("/")
    assert resposta.status_code == 200
    assert "Vamos começar" in resposta.text

    # 1. criar concurso → redireciona para o edital
    prova = (date.today() + timedelta(days=120)).isoformat()
    resposta = cliente.post(
        "/concursos",
        data={"nome": "TRF Teste", "banca": "FGV", "data_prova": prova},
    )
    assert resposta.status_code == 200
    assert "Edital verticalizado" in resposta.text

    # 2. disciplina + tópicos colados do edital
    resposta = cliente.post(
        "/disciplinas", data={"concurso_id": 1, "nome": "Direito Administrativo", "peso": 20}
    )
    assert "Direito Administrativo" in resposta.text
    resposta = cliente.post(
        "/disciplinas/1/topicos",
        data={"texto": "1. Atos administrativos; requisitos\n2. Poderes da administração"},
    )
    assert "Atos administrativos" in resposta.text
    assert "Poderes da administração" in resposta.text
    assert resposta.text.count("Não visto") >= 3

    # 3. montar o ciclo
    resposta = cliente.post(
        "/ciclo/blocos", data={"concurso_id": 1, "disciplina_id": 1, "duracao_min": 60}
    )
    assert "bloco atual" in resposta.text

    # 4. "estudar agora" recomenda o bloco e um tópico
    resposta = cliente.get("/estudar")
    assert "Bloco do ciclo: Direito Administrativo" in resposta.text
    assert "Tópico sugerido" in resposta.text

    # 5. sessão de teoria concluída → agenda revisões 1/7/30
    resposta = cliente.post(
        "/sessoes",
        data={
            "concurso_id": 1, "disciplina_id": 1, "topico_id": 1,
            "tipo": "teoria", "minutos": 50, "teoria_concluida": "1",
            "voltar_para": "/painel",
        },
    )
    assert resposta.status_code == 200
    painel = cliente.get("/painel").text
    assert "Próximas revisões" in painel
    edital = cliente.get("/edital").text
    assert "Teoria vista" in edital

    # 6. sessão de questões com bom desempenho → tópico progride
    cliente.post(
        "/sessoes",
        data={
            "concurso_id": 1, "disciplina_id": 1, "topico_id": 1,
            "tipo": "questoes", "minutos": 40,
            "questoes_feitas": 12, "questoes_acertadas": 11,
            "voltar_para": "/sessoes",
        },
    )
    assert "Dominado" in cliente.get("/edital").text

    # 7. concluir bloco avança o ponteiro do ciclo
    cliente.post(
        "/sessoes",
        data={
            "concurso_id": 1, "disciplina_id": 1, "topico_id": 2,
            "tipo": "teoria", "minutos": 30, "bloco_concluido": "1",
            "voltar_para": "/estudar",
        },
    )
    # (com 1 bloco só, o ponteiro volta para ele mesmo — não pode quebrar)
    assert cliente.get("/ciclo").status_code == 200

    # 8. histórico e painel refletem as sessões
    historico = cliente.get("/sessoes").text
    assert "11/12" in historico
    painel = cliente.get("/painel").text
    assert "2h00" in painel  # 50 + 40 + 30 = 120 min na semana
    assert "🔥 1" in painel  # streak de 1 dia


def test_revisao_vencida_aparece_e_conclui(cliente, monkeypatch):
    import sqlite3

    cliente.post("/concursos", data={"nome": "X", "banca": "", "data_prova": ""})
    cliente.post("/disciplinas", data={"concurso_id": 1, "nome": "Português", "peso": 10})
    cliente.post("/disciplinas/1/topicos", data={"texto": "Crase"})

    # marca teoria vista manualmente → agenda revisões; força a de 1d para ontem
    cliente.post("/topicos/1/status", data={"status": "teoria_vista"})
    caminho = os.environ["ESTUDOS_DB"]
    conn = sqlite3.connect(caminho)
    ontem = (date.today() - timedelta(days=1)).isoformat()
    conn.execute("UPDATE revisoes SET prevista_para = ? WHERE etapa = 1", (ontem,))
    conn.commit()
    conn.close()

    painel = cliente.get("/painel").text
    assert "Revisões de hoje" in painel
    assert "Crase" in painel

    # "esqueci" conclui a revisão e cria uma extra para amanhã
    cliente.post("/revisoes/1/concluir", data={"resultado": "esqueci", "voltar_para": "/painel"})
    conn = sqlite3.connect(caminho)
    pendentes = conn.execute(
        "SELECT COUNT(*) FROM revisoes WHERE concluida_em IS NULL"
    ).fetchone()[0]
    concluidas = conn.execute(
        "SELECT COUNT(*) FROM revisoes WHERE concluida_em IS NOT NULL AND resultado = 'esqueci'"
    ).fetchone()[0]
    conn.close()
    assert concluidas == 1
    assert pendentes == 3  # 7d + 30d originais + a extra de amanhã
