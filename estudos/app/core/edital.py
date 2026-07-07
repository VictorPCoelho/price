"""Verticalização do edital: transforma texto colado em lista de tópicos.

Heurística conservadora (§10.2 do brainstorm): quebra apenas por separadores
inequívocos (quebra de linha e ponto e vírgula). Não tenta adivinhar estrutura;
o usuário revisa a lista antes de salvar.
"""


def parse_topicos(texto: str) -> list[str]:
    brutos: list[str] = []
    for linha in texto.splitlines():
        brutos.extend(linha.split(";"))

    topicos: list[str] = []
    vistos: set[str] = set()
    for bruto in brutos:
        topico = bruto.strip(" \t.:-–—•")
        if len(topico) < 3:
            continue
        chave = topico.casefold()
        if chave in vistos:
            continue
        vistos.add(chave)
        topicos.append(topico)
    return topicos
