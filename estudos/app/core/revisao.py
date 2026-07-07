"""Revisões espaçadas no esquema fixo 1d / 7d / 30d (decisão nº 5 do brainstorm:
começar simples; SM-2/FSRS entra em fase posterior via Anki)."""
from datetime import date, timedelta

ETAPAS = (1, 7, 30)

RESULTADOS = ("lembrei", "parcial", "esqueci")


def agendar(base: date) -> list[tuple[int, date]]:
    """Agenda as três revisões de um tópico cuja teoria foi concluída em `base`."""
    return [(etapa, base + timedelta(days=etapa)) for etapa in ETAPAS]


def reagendamento(etapa: int, resultado: str, hoje: date) -> tuple[int, date] | None:
    """Revisão extra quando a retenção falhou; None se não precisa reagendar.

    - "esqueci": repete a mesma etapa amanhã.
    - "parcial": repete a mesma etapa em 3 dias.
    - "lembrei": nada — as próximas etapas pré-agendadas bastam.
    """
    if resultado == "esqueci":
        return (etapa, hoje + timedelta(days=1))
    if resultado == "parcial":
        return (etapa, hoje + timedelta(days=3))
    return None
