"""Ciclo de estudos: sequência circular de blocos por disciplina.

O ciclo não tem data — terminou um bloco, o ponteiro avança para o próximo.
Isso o torna resiliente a dias perdidos (não existe "atraso" acumulado).
"""


def indice_bloco_atual(n_blocos: int, pos: int) -> int | None:
    """Índice (0-based, na ordem dos blocos) do bloco apontado pelo ciclo."""
    if n_blocos <= 0:
        return None
    return pos % n_blocos


def avancar(n_blocos: int, pos: int) -> int:
    """Novo valor do ponteiro após concluir o bloco atual."""
    if n_blocos <= 0:
        return 0
    return (pos + 1) % n_blocos
