"""Motor de prioridade: responde "o que estudar agora".

Cascata de decisão (§3 do brainstorm):
1. Revisões vencidas sempre primeiro.
2. Senão, o bloco apontado pelo ciclo; dentro da disciplina do bloco,
   o tópico de maior score.

score(tópico) = peso_relativo × (1 − proficiência) × urgência × fator_status
"""
from dataclasses import dataclass, field
from datetime import date

MINIMO_QUESTOES = 5

FATOR_STATUS = {
    "nao_visto": 1.0,
    "teoria_vista": 0.8,
    "exercitado": 0.5,
    "dominado": 0.1,
}

STATUS_ROTULOS = {
    "nao_visto": "Não visto",
    "teoria_vista": "Teoria vista",
    "exercitado": "Exercitado",
    "dominado": "Dominado",
}


@dataclass
class TopicoInfo:
    id: int
    titulo: str
    status: str = "nao_visto"
    peso_relativo: float = 1.0
    questoes_feitas: int = 0
    questoes_acertadas: int = 0
    score: float = field(default=0.0, init=False)


def proficiencia(feitas: int, acertadas: int) -> float:
    """Taxa de acerto no tópico; 0 quando ainda não há amostra confiável."""
    if feitas < MINIMO_QUESTOES:
        return 0.0
    return min(1.0, acertadas / feitas)


def urgencia(dias_para_prova: int | None) -> float:
    """1.0 longe da prova, crescendo até 2.0 nos últimos 90 dias."""
    if dias_para_prova is None:
        return 1.0
    if dias_para_prova <= 0:
        return 2.0
    return 1.0 + max(0.0, min(1.0, (90 - dias_para_prova) / 90))


def score(topico: TopicoInfo, dias_para_prova: int | None) -> float:
    prof = proficiencia(topico.questoes_feitas, topico.questoes_acertadas)
    fator = FATOR_STATUS.get(topico.status, 1.0)
    return topico.peso_relativo * (1.0 - prof) * urgencia(dias_para_prova) * fator


def ordenar_topicos(
    topicos: list[TopicoInfo], dias_para_prova: int | None
) -> list[TopicoInfo]:
    """Preenche o score de cada tópico e devolve a lista do maior para o menor."""
    for topico in topicos:
        topico.score = score(topico, dias_para_prova)
    return sorted(topicos, key=lambda t: t.score, reverse=True)


def novo_status(status_atual: str, feitas_acumuladas: int, acertadas_acumuladas: int) -> str:
    """Progressão/regressão do tópico conforme a proficiência em questões."""
    prof = proficiencia(feitas_acumuladas, acertadas_acumuladas)
    if feitas_acumuladas >= 10 and prof >= 0.8:
        return "dominado"
    if feitas_acumuladas > 0 and status_atual in ("teoria_vista", "exercitado", "dominado"):
        return "exercitado"
    return status_atual


def dias_ate(data_prova: date | None, hoje: date) -> int | None:
    if data_prova is None:
        return None
    return (data_prova - hoje).days
