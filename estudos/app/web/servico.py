"""Camada de serviço: consultas SQL + regras do núcleo, sem nada de HTTP."""
import sqlite3
from datetime import date, datetime

from app import db
from app.core import ciclo, edital, estatisticas, prioridade, revisao


# ------------------------------------------------------------------ concursos
def listar_concursos(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM concursos ORDER BY id DESC").fetchall()


def concurso_ativo(conn: sqlite3.Connection) -> sqlite3.Row | None:
    valor = db.config_get(conn, "concurso_ativo")
    if valor:
        linha = conn.execute("SELECT * FROM concursos WHERE id = ?", (valor,)).fetchone()
        if linha:
            return linha
    return conn.execute("SELECT * FROM concursos ORDER BY id LIMIT 1").fetchone()


def criar_concurso(
    conn: sqlite3.Connection, nome: str, banca: str, data_prova: str | None
) -> int:
    cursor = conn.execute(
        "INSERT INTO concursos (nome, banca, data_prova) VALUES (?, ?, ?)",
        (nome.strip(), banca.strip(), data_prova or None),
    )
    conn.commit()
    db.config_set(conn, "concurso_ativo", str(cursor.lastrowid))
    return cursor.lastrowid


def ativar_concurso(conn: sqlite3.Connection, concurso_id: int) -> None:
    db.config_set(conn, "concurso_ativo", str(concurso_id))


def data_prova_de(concurso: sqlite3.Row) -> date | None:
    if not concurso["data_prova"]:
        return None
    return datetime.strptime(concurso["data_prova"], "%Y-%m-%d").date()


# ---------------------------------------------------------------- disciplinas
def criar_disciplina(
    conn: sqlite3.Connection, concurso_id: int, nome: str, peso: int
) -> int:
    ordem = conn.execute(
        "SELECT COALESCE(MAX(ordem), 0) + 1 FROM disciplinas WHERE concurso_id = ?",
        (concurso_id,),
    ).fetchone()[0]
    cursor = conn.execute(
        "INSERT INTO disciplinas (concurso_id, nome, peso, ordem) VALUES (?, ?, ?, ?)",
        (concurso_id, nome.strip(), max(1, peso), ordem),
    )
    conn.commit()
    return cursor.lastrowid


def listar_disciplinas(conn: sqlite3.Connection, concurso_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM disciplinas WHERE concurso_id = ? ORDER BY ordem, id",
        (concurso_id,),
    ).fetchall()


def peso_total(conn: sqlite3.Connection, concurso_id: int) -> int:
    total = conn.execute(
        "SELECT COALESCE(SUM(peso), 0) FROM disciplinas WHERE concurso_id = ?",
        (concurso_id,),
    ).fetchone()[0]
    return total or 1


# -------------------------------------------------------------------- tópicos
def adicionar_topicos(conn: sqlite3.Connection, disciplina_id: int, texto: str) -> int:
    titulos = edital.parse_topicos(texto)
    existentes = {
        linha["titulo"].casefold()
        for linha in conn.execute(
            "SELECT titulo FROM topicos WHERE disciplina_id = ?", (disciplina_id,)
        )
    }
    ordem = conn.execute(
        "SELECT COALESCE(MAX(ordem), 0) FROM topicos WHERE disciplina_id = ?",
        (disciplina_id,),
    ).fetchone()[0]
    inseridos = 0
    for titulo in titulos:
        if titulo.casefold() in existentes:
            continue
        ordem += 1
        conn.execute(
            "INSERT INTO topicos (disciplina_id, titulo, ordem) VALUES (?, ?, ?)",
            (disciplina_id, titulo, ordem),
        )
        inseridos += 1
    conn.commit()
    return inseridos


def listar_topicos(conn: sqlite3.Connection, disciplina_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM topicos WHERE disciplina_id = ? ORDER BY ordem, id",
        (disciplina_id,),
    ).fetchall()


def definir_status_topico(
    conn: sqlite3.Connection, topico_id: int, status: str, hoje: date
) -> None:
    if status not in prioridade.FATOR_STATUS:
        return
    conn.execute("UPDATE topicos SET status = ? WHERE id = ?", (status, topico_id))
    if status != "nao_visto":
        _garantir_revisoes(conn, topico_id, hoje)
    conn.commit()


def _garantir_revisoes(conn: sqlite3.Connection, topico_id: int, base: date) -> None:
    """Agenda as revisões 1/7/30 uma única vez por tópico."""
    existe = conn.execute(
        "SELECT 1 FROM revisoes WHERE topico_id = ? LIMIT 1", (topico_id,)
    ).fetchone()
    if existe:
        return
    for etapa, prevista in revisao.agendar(base):
        conn.execute(
            "INSERT INTO revisoes (topico_id, etapa, prevista_para) VALUES (?, ?, ?)",
            (topico_id, etapa, prevista.isoformat()),
        )


# ---------------------------------------------------------------------- ciclo
def blocos_do_ciclo(conn: sqlite3.Connection, concurso_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT b.*, d.nome AS disciplina_nome FROM ciclo_blocos b "
        "JOIN disciplinas d ON d.id = b.disciplina_id "
        "WHERE b.concurso_id = ? ORDER BY b.ordem, b.id",
        (concurso_id,),
    ).fetchall()


def criar_bloco(
    conn: sqlite3.Connection, concurso_id: int, disciplina_id: int, duracao_min: int
) -> int:
    ordem = conn.execute(
        "SELECT COALESCE(MAX(ordem), 0) + 1 FROM ciclo_blocos WHERE concurso_id = ?",
        (concurso_id,),
    ).fetchone()[0]
    cursor = conn.execute(
        "INSERT INTO ciclo_blocos (concurso_id, disciplina_id, duracao_min, ordem) "
        "VALUES (?, ?, ?, ?)",
        (concurso_id, disciplina_id, max(10, duracao_min), ordem),
    )
    conn.commit()
    return cursor.lastrowid


def remover_bloco(conn: sqlite3.Connection, bloco_id: int) -> None:
    conn.execute("DELETE FROM ciclo_blocos WHERE id = ?", (bloco_id,))
    conn.commit()


def bloco_atual(conn: sqlite3.Connection, concurso: sqlite3.Row) -> sqlite3.Row | None:
    blocos = blocos_do_ciclo(conn, concurso["id"])
    indice = ciclo.indice_bloco_atual(len(blocos), concurso["ciclo_pos"])
    return blocos[indice] if indice is not None else None


def avancar_ciclo(conn: sqlite3.Connection, concurso_id: int) -> None:
    concurso = conn.execute(
        "SELECT * FROM concursos WHERE id = ?", (concurso_id,)
    ).fetchone()
    n_blocos = conn.execute(
        "SELECT COUNT(*) FROM ciclo_blocos WHERE concurso_id = ?", (concurso_id,)
    ).fetchone()[0]
    nova_pos = ciclo.avancar(n_blocos, concurso["ciclo_pos"])
    conn.execute(
        "UPDATE concursos SET ciclo_pos = ? WHERE id = ?", (nova_pos, concurso_id)
    )
    conn.commit()


# ------------------------------------------------------------------- questões
def questoes_por_topico(conn: sqlite3.Connection, disciplina_id: int) -> dict[int, tuple[int, int]]:
    """topico_id -> (feitas, acertadas) acumuladas nas sessões."""
    linhas = conn.execute(
        "SELECT topico_id, COALESCE(SUM(questoes_feitas), 0) AS feitas, "
        "COALESCE(SUM(questoes_acertadas), 0) AS acertadas "
        "FROM sessoes WHERE disciplina_id = ? AND topico_id IS NOT NULL "
        "GROUP BY topico_id",
        (disciplina_id,),
    ).fetchall()
    return {l["topico_id"]: (l["feitas"], l["acertadas"]) for l in linhas}


def topicos_priorizados(
    conn: sqlite3.Connection,
    concurso: sqlite3.Row,
    disciplina: sqlite3.Row,
    hoje: date,
) -> list[prioridade.TopicoInfo]:
    peso_rel = disciplina["peso"] / peso_total(conn, concurso["id"])
    questoes = questoes_por_topico(conn, disciplina["id"])
    infos = []
    for topico in listar_topicos(conn, disciplina["id"]):
        feitas, acertadas = questoes.get(topico["id"], (0, 0))
        infos.append(
            prioridade.TopicoInfo(
                id=topico["id"],
                titulo=topico["titulo"],
                status=topico["status"],
                peso_relativo=peso_rel,
                questoes_feitas=feitas,
                questoes_acertadas=acertadas,
            )
        )
    dias = prioridade.dias_ate(data_prova_de(concurso), hoje)
    return prioridade.ordenar_topicos(infos, dias)


# ------------------------------------------------------------------- revisões
def revisoes_vencidas(
    conn: sqlite3.Connection, concurso_id: int, hoje: date
) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT r.*, t.titulo AS topico_titulo, d.nome AS disciplina_nome, d.id AS disciplina_id "
        "FROM revisoes r "
        "JOIN topicos t ON t.id = r.topico_id "
        "JOIN disciplinas d ON d.id = t.disciplina_id "
        "WHERE d.concurso_id = ? AND r.concluida_em IS NULL AND r.prevista_para <= ? "
        "ORDER BY r.prevista_para, r.etapa",
        (concurso_id, hoje.isoformat()),
    ).fetchall()


def proximas_revisoes(
    conn: sqlite3.Connection, concurso_id: int, hoje: date, limite: int = 8
) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT r.*, t.titulo AS topico_titulo, d.nome AS disciplina_nome "
        "FROM revisoes r "
        "JOIN topicos t ON t.id = r.topico_id "
        "JOIN disciplinas d ON d.id = t.disciplina_id "
        "WHERE d.concurso_id = ? AND r.concluida_em IS NULL AND r.prevista_para > ? "
        "ORDER BY r.prevista_para LIMIT ?",
        (concurso_id, hoje.isoformat(), limite),
    ).fetchall()


def concluir_revisao(
    conn: sqlite3.Connection, revisao_id: int, resultado: str, hoje: date
) -> None:
    if resultado not in revisao.RESULTADOS:
        return
    linha = conn.execute(
        "SELECT * FROM revisoes WHERE id = ? AND concluida_em IS NULL", (revisao_id,)
    ).fetchone()
    if not linha:
        return
    conn.execute(
        "UPDATE revisoes SET concluida_em = ?, resultado = ? WHERE id = ?",
        (hoje.isoformat(), resultado, revisao_id),
    )
    extra = revisao.reagendamento(linha["etapa"], resultado, hoje)
    if extra:
        etapa, prevista = extra
        conn.execute(
            "INSERT INTO revisoes (topico_id, etapa, prevista_para) VALUES (?, ?, ?)",
            (linha["topico_id"], etapa, prevista.isoformat()),
        )
    conn.commit()


# -------------------------------------------------------------------- sessões
def registrar_sessao(
    conn: sqlite3.Connection,
    concurso_id: int,
    disciplina_id: int | None,
    topico_id: int | None,
    tipo: str,
    minutos: int,
    data_sessao: date,
    paginas: int | None = None,
    questoes_feitas: int | None = None,
    questoes_acertadas: int | None = None,
    obs: str = "",
    teoria_concluida: bool = False,
    bloco_concluido: bool = False,
) -> int:
    cursor = conn.execute(
        "INSERT INTO sessoes (concurso_id, disciplina_id, topico_id, tipo, data, "
        "minutos, paginas, questoes_feitas, questoes_acertadas, obs) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            concurso_id,
            disciplina_id,
            topico_id,
            tipo,
            data_sessao.isoformat(),
            max(1, minutos),
            paginas,
            questoes_feitas,
            questoes_acertadas,
            obs.strip(),
        ),
    )
    if topico_id:
        _atualizar_topico_pos_sessao(
            conn, topico_id, disciplina_id, teoria_concluida, data_sessao
        )
    if bloco_concluido:
        conn.commit()
        avancar_ciclo(conn, concurso_id)
    conn.commit()
    return cursor.lastrowid


def _atualizar_topico_pos_sessao(
    conn: sqlite3.Connection,
    topico_id: int,
    disciplina_id: int | None,
    teoria_concluida: bool,
    hoje: date,
) -> None:
    topico = conn.execute("SELECT * FROM topicos WHERE id = ?", (topico_id,)).fetchone()
    if not topico:
        return
    status = topico["status"]
    if teoria_concluida and status == "nao_visto":
        status = "teoria_vista"
    if teoria_concluida:
        _garantir_revisoes(conn, topico_id, hoje)
    if disciplina_id:
        feitas, acertadas = questoes_por_topico(conn, disciplina_id).get(topico_id, (0, 0))
        status = prioridade.novo_status(status, feitas, acertadas)
    if status != topico["status"]:
        conn.execute("UPDATE topicos SET status = ? WHERE id = ?", (status, topico_id))


def listar_sessoes(
    conn: sqlite3.Connection, concurso_id: int, limite: int = 50
) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT s.*, d.nome AS disciplina_nome, t.titulo AS topico_titulo "
        "FROM sessoes s "
        "LEFT JOIN disciplinas d ON d.id = s.disciplina_id "
        "LEFT JOIN topicos t ON t.id = s.topico_id "
        "WHERE s.concurso_id = ? ORDER BY s.data DESC, s.id DESC LIMIT ?",
        (concurso_id, limite),
    ).fetchall()


# --------------------------------------------------------------- estudar agora
def recomendar(conn: sqlite3.Connection, concurso: sqlite3.Row, hoje: date) -> dict:
    """Cascata: revisões vencidas → bloco do ciclo → tópico de maior score."""
    vencidas = revisoes_vencidas(conn, concurso["id"], hoje)
    bloco = bloco_atual(conn, concurso)
    topico = None
    alternativas: list[prioridade.TopicoInfo] = []
    if bloco:
        disciplina = conn.execute(
            "SELECT * FROM disciplinas WHERE id = ?", (bloco["disciplina_id"],)
        ).fetchone()
        priorizados = topicos_priorizados(conn, concurso, disciplina, hoje)
        pendentes = [t for t in priorizados if t.status != "dominado"] or priorizados
        if pendentes:
            topico = pendentes[0]
            alternativas = pendentes[1:4]
    return {
        "revisoes_vencidas": vencidas,
        "bloco": bloco,
        "topico": topico,
        "alternativas": alternativas,
    }


# --------------------------------------------------------------------- painel
def painel(conn: sqlite3.Connection, concurso: sqlite3.Row, hoje: date) -> dict:
    concurso_id = concurso["id"]
    linhas_sessao = conn.execute(
        "SELECT data, minutos FROM sessoes WHERE concurso_id = ?", (concurso_id,)
    ).fetchall()
    sessoes = [
        (datetime.strptime(l["data"], "%Y-%m-%d").date(), l["minutos"])
        for l in linhas_sessao
    ]
    dias_estudo = {dia for dia, _ in sessoes}
    semanas = estatisticas.minutos_por_semana(sessoes, hoje)

    disciplinas_painel = []
    total_pesos = peso_total(conn, concurso_id)
    for disc in listar_disciplinas(conn, concurso_id):
        status_lista = [t["status"] for t in listar_topicos(conn, disc["id"])]
        agregado = conn.execute(
            "SELECT COALESCE(SUM(questoes_feitas), 0) AS f, "
            "COALESCE(SUM(questoes_acertadas), 0) AS a "
            "FROM sessoes WHERE disciplina_id = ?",
            (disc["id"],),
        ).fetchone()
        disciplinas_painel.append(
            {
                "disciplina": disc,
                "peso_pct": 100.0 * disc["peso"] / total_pesos,
                "n_topicos": len(status_lista),
                "cobertura": estatisticas.cobertura(status_lista),
                "pct_visto": estatisticas.percentual_visto(status_lista),
                "taxa_acerto": estatisticas.taxa_acerto(agregado["f"], agregado["a"]),
            }
        )

    dias_prova = prioridade.dias_ate(data_prova_de(concurso), hoje)
    return {
        "streak": estatisticas.streak(dias_estudo, hoje),
        "semanas": semanas,
        "minutos_semana_atual": list(semanas.values())[-1] if semanas else 0,
        "disciplinas": disciplinas_painel,
        "revisoes_vencidas": revisoes_vencidas(conn, concurso_id, hoje),
        "proximas_revisoes": proximas_revisoes(conn, concurso_id, hoje),
        "dias_para_prova": dias_prova,
    }
