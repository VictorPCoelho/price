"""Fonte Mercado Livre — FASE 2 (ainda não ativa).

Desde 2024 a API de busca (/sites/MLB/search) exige OAuth. Para ativar:

1. Crie um app em https://developers.mercadolivre.com.br/ (Minhas aplicações).
2. Gere um access token (fluxo client_credentials ou authorization_code).
3. Guarde como secret ML_ACCESS_TOKEN no GitHub e implemente aqui a busca
   por ofertas do dia: GET https://api.mercadolibre.com/sites/MLB/search
   com header Authorization: Bearer <token>, filtrando promotion/deal.

Enquanto isso, fetch() retorna vazio e o run segue com as outras fontes.
"""

import logging
import os

from models import Deal

log = logging.getLogger(__name__)


def fetch() -> list[Deal]:
    if not os.environ.get("ML_ACCESS_TOKEN"):
        log.info("Mercado Livre desativado (sem ML_ACCESS_TOKEN) — fase 2.")
        return []
    log.warning("ML_ACCESS_TOKEN definido, mas a integração ainda não foi implementada.")
    return []
