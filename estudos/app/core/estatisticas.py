"""Métricas do painel: constância, horas líquidas, cobertura e taxa de acerto."""
from collections import OrderedDict
from datetime import date, timedelta

STATUS_ORDEM = ("nao_visto", "teoria_vista", "exercitado", "dominado")


def streak(dias_com_estudo: set[date], hoje: date) -> int:
    """Dias consecutivos de estudo terminando hoje ou ontem.

    Se hoje ainda não teve estudo, a sequência que terminou ontem continua
    valendo (o dia ainda não acabou).
    """
    if hoje in dias_com_estudo:
        atual = hoje
    elif hoje - timedelta(days=1) in dias_com_estudo:
        atual = hoje - timedelta(days=1)
    else:
        return 0
    contagem = 0
    while atual in dias_com_estudo:
        contagem += 1
        atual -= timedelta(days=1)
    return contagem


def minutos_por_semana(
    sessoes: list[tuple[date, int]], hoje: date, semanas: int = 4
) -> "OrderedDict[date, int]":
    """Minutos líquidos por semana (chave = segunda-feira), da mais antiga à atual."""
    inicio_semana_atual = hoje - timedelta(days=hoje.weekday())
    resultado: OrderedDict[date, int] = OrderedDict()
    for i in range(semanas - 1, -1, -1):
        resultado[inicio_semana_atual - timedelta(weeks=i)] = 0
    for dia, minutos in sessoes:
        segunda = dia - timedelta(days=dia.weekday())
        if segunda in resultado:
            resultado[segunda] += minutos
    return resultado


def cobertura(status_topicos: list[str]) -> dict[str, int]:
    contagem = {status: 0 for status in STATUS_ORDEM}
    for status in status_topicos:
        if status in contagem:
            contagem[status] += 1
    return contagem


def percentual_visto(status_topicos: list[str]) -> float:
    """% de tópicos que saíram de 'não visto'."""
    if not status_topicos:
        return 0.0
    vistos = sum(1 for s in status_topicos if s != "nao_visto")
    return 100.0 * vistos / len(status_topicos)


def taxa_acerto(feitas: int, acertadas: int) -> float | None:
    if not feitas:
        return None
    return 100.0 * acertadas / feitas
