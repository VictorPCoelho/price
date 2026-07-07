"""Fonte Promobit.

Estratégia em camadas, porque o site pode mudar ou bloquear:
1. RSS (se disponível).
2. Scraping da home de promoções via JSON embutido (__NEXT_DATA__).
Cada camada só roda se a anterior não retornar nada.
"""

import json
import logging
import re

from bs4 import BeautifulSoup

from models import Deal
from sources import rss
from sources.http_client import get

log = logging.getLogger(__name__)

RSS_URLS = [
    "https://www.promobit.com.br/rss",
    "https://www.promobit.com.br/rss/",
    "https://www.promobit.com.br/feed",
]
PAGE_URL = "https://www.promobit.com.br/promocoes/"

_PRICE_RE = re.compile(r"R\$\s?([\d.]+,\d{2}|[\d.]+)")


def _parse_price(text: str | None) -> float | None:
    if not text:
        return None
    m = _PRICE_RE.search(text)
    if not m:
        return None
    raw = m.group(1)
    if "," in raw:
        raw = raw.replace(".", "").replace(",", ".")
    try:
        return float(raw)
    except ValueError:
        return None


def _from_rss() -> list[Deal]:
    for url in RSS_URLS:
        try:
            resp = get(url)
        except Exception as exc:
            log.info("Promobit RSS %s indisponível: %s", url, exc)
            continue
        items = rss.parse(resp.content)
        deals = [
            Deal(
                id=f"promobit:{item.guid}",
                title=item.title,
                url=item.link,
                source="promobit",
                price=_parse_price(item.title) or _parse_price(item.summary),
            )
            for item in items
        ]
        if deals:
            log.info("Promobit RSS: %d ofertas via %s", len(deals), url)
            return deals
    return []


def _walk_json(node, found: dict):
    """Percorre o JSON do __NEXT_DATA__ coletando objetos que parecem ofertas."""
    if isinstance(node, dict):
        keys = set(node.keys())
        if {"title", "price"} <= keys or {"offer_title", "offer_price"} <= keys:
            found[json.dumps(node, sort_keys=True)[:120]] = node
        for v in node.values():
            _walk_json(v, found)
    elif isinstance(node, list):
        for v in node:
            _walk_json(v, found)


def _offer_from_obj(obj: dict) -> Deal | None:
    title = obj.get("title") or obj.get("offer_title")
    if not title:
        return None
    slug = obj.get("slug") or obj.get("offer_slug")
    oid = obj.get("id") or obj.get("offer_id") or slug
    if oid is None:
        return None
    url = f"https://www.promobit.com.br/oferta/{slug}" if slug else PAGE_URL

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

    return Deal(
        id=f"promobit:{oid}",
        title=str(title).strip(),
        url=url,
        source="promobit",
        price=num("price", "offer_price", "new_price"),
        old_price=num("old_price", "offer_old_price", "price_from"),
        store=(obj.get("store") or {}).get("name") if isinstance(obj.get("store"), dict) else obj.get("store_name"),
        image=obj.get("image") or obj.get("offer_image") or obj.get("photo"),
        hot_score=obj.get("temperature") or obj.get("likes"),
    )


def _from_page() -> list[Deal]:
    try:
        resp = get(PAGE_URL)
    except Exception as exc:
        log.warning("Promobit página indisponível: %s", exc)
        return []
    soup = BeautifulSoup(resp.text, "html.parser")
    script = soup.find("script", id="__NEXT_DATA__")
    if not script or not script.string:
        log.warning("Promobit: __NEXT_DATA__ não encontrado — layout mudou?")
        return []
    try:
        data = json.loads(script.string)
    except json.JSONDecodeError as exc:
        log.warning("Promobit: __NEXT_DATA__ inválido: %s", exc)
        return []
    found: dict = {}
    _walk_json(data, found)
    deals = [d for d in (_offer_from_obj(o) for o in found.values()) if d]
    log.info("Promobit página: %d ofertas extraídas", len(deals))
    return deals


def fetch() -> list[Deal]:
    return _from_rss() or _from_page()
