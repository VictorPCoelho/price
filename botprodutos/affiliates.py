"""Camada de afiliados — desativada por padrão.

Cada converter só age se a variável de ambiente correspondente existir
(cadastre como secret no GitHub quando sua conta de afiliado for aprovada):

- AMAZON_TAG        -> adiciona ?tag=SEU_TAG em links amazon.com.br
- ML_AFFILIATE_TOOL -> (fase 2) links do Mercado Livre via sua ferramenta de afiliado

Sem variáveis definidas, o link original é postado sem alteração.
"""

import os
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from models import Deal


def _amazon(url: str) -> str:
    tag = os.environ.get("AMAZON_TAG")
    if not tag:
        return url
    parts = urlparse(url)
    if "amazon.com" not in parts.netloc:
        return url
    query = dict(parse_qsl(parts.query))
    query["tag"] = tag
    return urlunparse(parts._replace(query=urlencode(query)))


CONVERTERS = [_amazon]


def rewrite_link(deal: Deal) -> str:
    url = deal.url
    for conv in CONVERTERS:
        url = conv(url)
    return url
