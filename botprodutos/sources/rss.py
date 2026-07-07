"""Parser RSS mínimo com a biblioteca padrão (evita depender do feedparser,
cuja dependência sgmllib3k está abandonada)."""

import xml.etree.ElementTree as ET
from dataclasses import dataclass


@dataclass
class RssItem:
    title: str
    link: str
    guid: str
    summary: str


def parse(content: bytes) -> list[RssItem]:
    try:
        root = ET.fromstring(content)
    except ET.ParseError:
        return []
    items = []
    for item in root.iter("item"):
        def text(tag):
            el = item.find(tag)
            return (el.text or "").strip() if el is not None else ""

        link = text("link")
        if not link:
            continue
        items.append(
            RssItem(
                title=text("title"),
                link=link,
                guid=text("guid") or link,
                summary=text("description"),
            )
        )
    return items
