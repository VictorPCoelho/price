"""Conexão e esquema do banco SQLite (fonte única de dados da ferramenta)."""
import os
import sqlite3
from pathlib import Path

PADRAO_DB = Path(__file__).resolve().parent.parent / "data" / "estudos.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS config (
    chave TEXT PRIMARY KEY,
    valor TEXT
);

CREATE TABLE IF NOT EXISTS concursos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    banca TEXT NOT NULL DEFAULT '',
    data_prova TEXT,
    ciclo_pos INTEGER NOT NULL DEFAULT 0,
    criado_em TEXT NOT NULL DEFAULT (date('now'))
);

CREATE TABLE IF NOT EXISTS disciplinas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    concurso_id INTEGER NOT NULL REFERENCES concursos(id) ON DELETE CASCADE,
    nome TEXT NOT NULL,
    peso INTEGER NOT NULL DEFAULT 1,
    ordem INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS topicos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    disciplina_id INTEGER NOT NULL REFERENCES disciplinas(id) ON DELETE CASCADE,
    titulo TEXT NOT NULL,
    ordem INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'nao_visto'
);

CREATE TABLE IF NOT EXISTS ciclo_blocos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    concurso_id INTEGER NOT NULL REFERENCES concursos(id) ON DELETE CASCADE,
    disciplina_id INTEGER NOT NULL REFERENCES disciplinas(id) ON DELETE CASCADE,
    duracao_min INTEGER NOT NULL DEFAULT 60,
    ordem INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS sessoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    concurso_id INTEGER NOT NULL REFERENCES concursos(id) ON DELETE CASCADE,
    disciplina_id INTEGER REFERENCES disciplinas(id) ON DELETE SET NULL,
    topico_id INTEGER REFERENCES topicos(id) ON DELETE SET NULL,
    tipo TEXT NOT NULL DEFAULT 'teoria',
    data TEXT NOT NULL DEFAULT (date('now')),
    minutos INTEGER NOT NULL,
    paginas INTEGER,
    questoes_feitas INTEGER,
    questoes_acertadas INTEGER,
    obs TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS revisoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topico_id INTEGER NOT NULL REFERENCES topicos(id) ON DELETE CASCADE,
    etapa INTEGER NOT NULL,
    prevista_para TEXT NOT NULL,
    concluida_em TEXT,
    resultado TEXT
);

CREATE INDEX IF NOT EXISTS idx_topicos_disc ON topicos(disciplina_id);
CREATE INDEX IF NOT EXISTS idx_sessoes_conc ON sessoes(concurso_id, data);
CREATE INDEX IF NOT EXISTS idx_revisoes_pend ON revisoes(prevista_para) WHERE concluida_em IS NULL;
"""


def caminho_db() -> Path:
    return Path(os.environ.get("ESTUDOS_DB", str(PADRAO_DB)))


def conectar(caminho: str | Path | None = None) -> sqlite3.Connection:
    caminho = Path(caminho) if caminho else caminho_db()
    caminho.parent.mkdir(parents=True, exist_ok=True)
    # check_same_thread=False: o FastAPI executa handlers síncronos em threadpool;
    # cada requisição tem conexão própria e uso sequencial, então é seguro.
    conn = sqlite3.connect(caminho, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    return conn


def config_get(conn: sqlite3.Connection, chave: str) -> str | None:
    linha = conn.execute("SELECT valor FROM config WHERE chave = ?", (chave,)).fetchone()
    return linha["valor"] if linha else None


def config_set(conn: sqlite3.Connection, chave: str, valor: str) -> None:
    conn.execute(
        "INSERT INTO config (chave, valor) VALUES (?, ?) "
        "ON CONFLICT(chave) DO UPDATE SET valor = excluded.valor",
        (chave, valor),
    )
    conn.commit()
