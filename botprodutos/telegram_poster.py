"""Postagem no canal do Telegram via Bot API (HTTP puro)."""

import html
import logging
import os

import requests

import config
from affiliates import rewrite_link
from models import Deal

log = logging.getLogger(__name__)

API = "https://api.telegram.org/bot{token}/{method}"


def format_caption(deal: Deal) -> str:
    lines = []
    disc = deal.discount_pct
    if disc and disc >= config.BUG_DISCOUNT_PCT:
        lines.append("🚨 <b>POSSÍVEL BUG DE PREÇO</b> 🚨")
        lines.append("<i>Pedido sujeito a cancelamento pela loja.</i>")
        lines.append("")
    title = html.escape(deal.title)
    lines.append(f"🔥 <b>{title}</b>")
    lines.append("")
    if deal.price is not None:
        price = f"R$ {deal.price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        if deal.old_price:
            old = f"R$ {deal.old_price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            lines.append(f"💰 <s>{old}</s> ➜ <b>{price}</b> ({disc:.0f}% OFF)")
        else:
            lines.append(f"💰 <b>{price}</b>")
    if deal.store:
        lines.append(f"🏪 {html.escape(str(deal.store))}")
    if deal.coupon:
        lines.append(f"🎟 Cupom: <code>{html.escape(deal.coupon)}</code>")
    lines.append("")
    lines.append(f'🛒 <a href="{html.escape(rewrite_link(deal))}">COMPRAR AGORA</a>')
    return "\n".join(lines)


def post(deal: Deal) -> bool:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    caption = format_caption(deal)

    if deal.image:
        resp = requests.post(
            API.format(token=token, method="sendPhoto"),
            json={"chat_id": chat_id, "photo": deal.image, "caption": caption, "parse_mode": "HTML"},
            timeout=30,
        )
        if resp.ok:
            return True
        log.warning("sendPhoto falhou (%s), tentando sendMessage: %s", resp.status_code, resp.text[:200])

    resp = requests.post(
        API.format(token=token, method="sendMessage"),
        json={"chat_id": chat_id, "text": caption, "parse_mode": "HTML", "disable_web_page_preview": False},
        timeout=30,
    )
    if not resp.ok:
        log.error("sendMessage falhou (%s): %s", resp.status_code, resp.text[:300])
    return resp.ok
