"""Gerador do catálogo web interativo (Projeto 2).

Monta um site estático (HTML único + imagens das páginas) a partir dos
dados que o precificador (Projeto 1) já produz: códigos, posições nas
páginas, descrições e preços de venda por tamanho.

O cliente navega pelas páginas, toca no ➕ da peça, escolhe o tamanho,
monta a sacolinha e envia o pedido pronto pelo WhatsApp da vendedora.

IMPORTANTE: aqui entram apenas preços de VENDA — nunca o preço de custo
do catálogo da marca.
"""

from __future__ import annotations

import io
import json
import re
import unicodedata
import zipfile
from pathlib import Path

_TEMPLATE = Path(__file__).parent / "template.html"


def _id_do_titulo(titulo: str) -> str:
    """Gera um id estável a partir do título (para o localStorage da sacola)."""
    s = unicodedata.normalize("NFKD", titulo).encode("ascii", "ignore").decode()
    s = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower()
    return s or "catalogo"


def limpar_whatsapp(numero: str) -> str:
    """Mantém só os dígitos e garante o código do Brasil (55) na frente.

    Aceita "(31) 99999-8888", "5531999998888", "31 99999 8888"...
    Retorna "" se não houver dígitos suficientes para um número válido.
    """
    digitos = re.sub(r"\D", "", numero or "")
    if len(digitos) in (10, 11):  # DDD + telefone, sem o país
        digitos = "55" + digitos
    if len(digitos) < 12 or not digitos.startswith("55"):
        return ""
    return digitos


def gerar_site(
    titulo: str,
    whatsapp: str,
    paginas_jpg: list[bytes],
    itens: list[dict],
    cor_tema: str = "#3D3D45",
) -> bytes:
    """Gera o zip do site estático do catálogo.

    ``itens``: lista de dicionários com
      - codigo: str
      - descricao: str (pode ser vazia)
      - pagina: int (0-based)
      - pontos: list[[x, y]] — centro de cada ocorrência do código na
        página, em fração da largura/altura (0..1)
      - precos: list[{"tamanho": str, "valor": float}] — preços de VENDA

    Retorna os bytes de um .zip com index.html + paginas/*.jpg, pronto
    para publicar em hospedagem estática (Netlify, GitHub Pages).
    """
    numero = limpar_whatsapp(whatsapp)
    if not numero:
        raise ValueError(
            "Número de WhatsApp inválido — informe com DDD, ex.: 31 99999-8888"
        )
    if not paginas_jpg:
        raise ValueError("O catálogo não tem páginas para publicar.")
    itens_validos = [i for i in itens if i.get("precos") and i.get("pontos")]

    nomes_paginas = [f"paginas/pagina-{n + 1:02d}.jpg" for n in range(len(paginas_jpg))]
    dados = {
        "id": _id_do_titulo(titulo),
        "titulo": titulo,
        "whatsapp": numero,
        "paginas": nomes_paginas,
        "itens": [
            {
                "codigo": i["codigo"],
                "descricao": i.get("descricao", ""),
                "pagina": i["pagina"],
                "pontos": i["pontos"],
                "precos": [
                    {"tamanho": p.get("tamanho", ""), "valor": round(float(p["valor"]), 2)}
                    for p in i["precos"]
                ],
            }
            for i in itens_validos
        ],
    }

    html = _TEMPLATE.read_text(encoding="utf-8")
    html = html.replace("__TITULO__", titulo)
    html = html.replace("__COR_TEMA__", cor_tema)
    html = html.replace("__DADOS__", json.dumps(dados, ensure_ascii=False))

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("index.html", html)
        for nome, jpg in zip(nomes_paginas, paginas_jpg):
            z.writestr(nome, jpg)
        z.writestr(
            "LEIA-ME.txt",
            "Como publicar o catálogo:\n"
            "1) Netlify (recomendado): acesse https://app.netlify.com/drop\n"
            "   e arraste esta pasta INTEIRA (descompactada) para a página.\n"
            "   Em segundos você recebe um link para mandar aos clientes.\n"
            "2) GitHub Pages: envie os arquivos para um repositório e ative\n"
            "   Settings > Pages.\n\n"
            "O link é 'não listado': só acessa quem o receber.\n",
        )
    return buf.getvalue()
