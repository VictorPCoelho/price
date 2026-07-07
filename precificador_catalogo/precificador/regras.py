"""Regras de precificação: multiplicador, arredondamento e perfis por marca."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, asdict
from pathlib import Path

ARREDONDAMENTOS = {
    "nenhum": "Sem arredondamento (2 casas)",
    "inteiro": "Para cima, sem centavos (ex.: 47,32 → 48,00)",
    "90": "Para cima, terminando em ,90 (ex.: 47,32 → 47,90)",
    "99": "Para cima, terminando em ,99 (ex.: 47,32 → 47,99)",
    "50": "Para cima, múltiplo de 0,50 (ex.: 47,32 → 47,50)",
}

MODOS_CARIMBO = {
    "substituir": "Substituir: cobre o preço original com o novo",
    "adicionar": "Adicionar: escreve o novo preço ao lado do original",
}


def arredondar(valor: float, regra: str) -> float:
    """Aplica a regra de arredondamento (sempre para cima, nunca abaixa o preço)."""
    if regra == "nenhum":
        return round(valor, 2)
    if regra == "inteiro":
        return float(math.ceil(valor - 1e-9))
    if regra == "50":
        return math.ceil((valor - 1e-9) * 2) / 2
    if regra in ("90", "99"):
        centavos = 0.90 if regra == "90" else 0.99
        base = math.floor(valor) + centavos
        if base < valor - 1e-9:
            base += 1.0
        return round(base, 2)
    raise ValueError(f"Regra de arredondamento desconhecida: {regra}")


def calcular_preco(valor_original: float, multiplicador: float, regra: str) -> float:
    return arredondar(valor_original * multiplicador, regra)


def formatar_brl(valor: float, com_rs: bool = True) -> str:
    """Formata 1234.5 como "R$ 1.234,50"."""
    inteiro, centavos = divmod(round(valor * 100), 100)
    inteiro_fmt = f"{inteiro:,}".replace(",", ".")
    texto = f"{inteiro_fmt},{centavos:02d}"
    return f"R$ {texto}" if com_rs else texto


def hex_para_rgb(cor_hex: str) -> tuple[float, float, float]:
    """Converte "#3D3D45" em (r, g, b) na faixa 0..1."""
    cor = cor_hex.lstrip("#")
    return tuple(int(cor[i:i + 2], 16) / 255 for i in (0, 2, 4))


def linhas_da_etiqueta(
    descricao: str,
    precos: list[tuple[str, float]],
    max_descricao: int = 30,
) -> list[str]:
    """Monta as linhas de texto da etiqueta de uma peça.

    Com mais de um código por foto, a descrição diz o que é cada peça
    (ex.: "BERMUDA MOLETINHO" × "CAMISETA MALHA"). ``precos`` é a lista
    de (rótulo do tamanho, valor de venda).
    """
    linhas: list[str] = []
    desc = (descricao or "").strip()
    if desc:
        if len(desc) > max_descricao:
            desc = desc[:max_descricao - 1].rstrip() + "…"
        linhas.append(desc)
    for rotulo, valor in precos:
        preco_fmt = formatar_brl(valor)
        if rotulo and rotulo != "—":
            linhas.append(f"{rotulo}: {preco_fmt}")
        else:
            linhas.append(preco_fmt)
    return linhas


@dataclass
class PerfilMarca:
    """Configuração de precificação de uma marca de catálogo."""

    nome: str
    multiplicador: float = 2.0
    arredondamento: str = "90"  # chave de ARREDONDAMENTOS
    modo_carimbo: str = "substituir"  # chave de MODOS_CARIMBO
    exigir_rs: bool = True
    valor_minimo: float = 1.0  # abaixo disso o item é sinalizado para revisão
    valor_maximo: float = 2000.0  # acima disso o item é sinalizado para revisão
    cor_etiqueta: str = "#3D3D45"  # cor de fundo da etiqueta (grafite neutro)
    descricao_na_etiqueta: bool = True  # 1ª linha da etiqueta = descrição da peça
    posicao_etiqueta: str = "auto"  # chave de POSICOES_ETIQUETA (carimbo.py)
    ocorrencias_carimbo: str = "todas"  # "todas" | "primeira" (por página)
    usar_logo: bool = True  # inserir o logo salvo da marca ao gerar o PDF
    logo_posicao: str = "inferior-direito"  # chave de POSICOES_LOGO
    logo_largura: int = 20  # largura do logo em % da largura da página
    logo_todas_paginas: bool = False  # False = só na primeira página
    whatsapp: str = ""  # número que recebe os pedidos do catálogo web


class RepositorioPerfis:
    """Guarda os perfis de marca em um arquivo JSON simples."""

    def __init__(self, caminho: str | Path):
        self.caminho = Path(caminho)

    def carregar(self) -> dict[str, PerfilMarca]:
        if not self.caminho.exists():
            return {}
        dados = json.loads(self.caminho.read_text(encoding="utf-8"))
        perfis = {}
        for nome, cfg in dados.items():
            campos = {k: v for k, v in cfg.items() if k in PerfilMarca.__dataclass_fields__}
            campos["nome"] = nome
            perfis[nome] = PerfilMarca(**campos)
        return perfis

    def salvar(self, perfis: dict[str, PerfilMarca]) -> None:
        dados = {nome: asdict(p) for nome, p in perfis.items()}
        for cfg in dados.values():
            cfg.pop("nome", None)
        self.caminho.write_text(
            json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8"
        )
