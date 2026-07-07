"""Fonte Pelando.

O Pelando é uma SPA (Next.js). Estratégia em camadas:
1. RSS (herdado da época Pepper, pode não existir mais).
2. Scraping da home via JSON embutido (__NEXT_DATA__).
"""

import json
import logging

from bs4 import BeautifulSoup

from models import Deal
from sources import rss
from sources.http_client import get
from sources.promobit import _parse_price  # mesmo formato de preço BR

log = logging.getLogger(__name__)

RSS_URLS = [
    "https://www.pelando.com.br/rss",
    "https://www.pelando.com.br/rss/hot",
    "https://www.pelando.com.br/feed",
]
PAGE_URL = "https://www.pelando.com.br/recentes"


def _from_rss() -> list[Deal]:
    for url in RSS_URLS:
        try:
            resp = get(url)
        except Exception as exc:
            log.info("Pelando RSS %s indisponível: %s", url, exc)
            continue
        items = rss.parse(resp.content)
        deals = [
            Deal(
                id=f"pelando:{item.guid}",
                title=item.title,
                url=item.link,
                source="pelando",
                price=_parse_price(item.title) or _parse_price(item.summary),
            )
            for item in items
        ]
        if deals:
            log.info("Pelando RSS: %d ofertas via %s", len(deals), url)
            return deals
    return []


def _walk(node, found: dict):
    if isinstance(node, dict):
        # Cards de oferta do Pelando têm title + (price ou temperature) + id
        if "title" in node and "id" in node and ("price" in node or "temperature" in node):
            found[str(node.get("id"))] = node
        for v in node.values():
            _walk(v, found)
    elif isinstance(node, list):
        for v in node:
            _walk(v, found)


def _deal_from_obj(obj: dict) -> Deal | None:
    title = obj.get("title")
    oid = obj.get("id")
    if not title or oid is None:
        return None
    url = obj.get("url") or obj.get("sourceUrl")
    if not url:
        slug = obj.get("slug")
        url = f"https://www.pelando.com.br/d/{oid}-{slug}" if slug else f"https://www.pelando.com.br/d/{oid}"

    def num(*names):
        for n in names:
            v = obj.get(n)
            if isinstance(v, (int, float)) and v > 0:
                return float(v)
            if isinstance(v, str):
                p = _parse_price(v) or _parse_price(f"R$ {v}")
                if p:
                    return p
        return None

    temp = obj.get("temperature")
    return Deal(
        id=f"pelando:{oid}",
        title=str(title).strip(),
        url=url,
        source="pelando",
        price=num("price"),
        old_price=num("oldPrice", "originalPrice"),
        store=(obj.get("store") or {}).get("name") if isinstance(obj.get("store"), dict) else None,
        image=obj.get("image") if isinstance(obj.get("image"), str) else None,
        hot_score=int(temp) if isinstance(temp, (int, float)) else None,
        coupon=obj.get("couponCode"),
    )


def _from_page() -> list[Deal]:
    try:
        resp = get(PAGE_URL)
    except Exception as exc:
        log.warning("Pelando página indisponível: %s", exc)
        return []
    soup = BeautifulSoup(resp.text, "html.parser")
    script = soup.find("script", id="__NEXT_DATA__")
    if not script or not script.string:
        log.warning("Pelando: __NEXT_DATA__ não encontrado — layout mudou?")
        return []
    try:
        data = json.loads(script.string)
    except json.JSONDecodeError as exc:
        log.warning("Pelando: __NEXT_DATA__ inválido: %s", exc)
        return []
    found: dict = {}
    _walk(data, found)
    deals = [d for d in (_deal_from_obj(o) for o in found.values()) if d]
    log.info("Pelando página: %d ofertas extraídas", len(deals))
    return deals


def fetch() -> list[Deal]:
    return _from_rss() or _from_page()
