"""Bot de ofertas: busca promoções nas fontes, filtra e posta no Telegram.

Uso:
  python main.py                     # run normal (exige TELEGRAM_BOT_TOKEN/CHAT_ID)
  python main.py --dry-run           # mostra o que seria postado, sem postar
  python main.py --source promobit   # roda só uma fonte
"""

import argparse
import logging
import os
import sys

import config
import state
import telegram_poster
from models import Deal
from sources import SOURCES

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger("main")


def passes_filters(deal: Deal) -> bool:
    title = deal.title.lower()
    if any(w.lower() in title for w in config.BLOCKED_WORDS):
        return False
    if config.KEYWORDS and not any(w.lower() in title for w in config.KEYWORDS):
        return False
    disc = deal.discount_pct
    if disc is not None:
        return disc >= config.MIN_DISCOUNT_PCT
    if deal.hot_score is not None:
        return deal.hot_score >= config.MIN_HOT_SCORE
    # Sem desconto nem temperatura conhecidos: não dá pra ranquear, pula.
    return False


def collect(only_source: str | None) -> list[Deal]:
    deals: list[Deal] = []
    for name, fetch in SOURCES.items():
        if only_source and name != only_source:
            continue
        try:
            found = fetch()
        except Exception:
            log.exception("Fonte %s falhou, seguindo com as demais", name)
            continue
        deals.extend(found)
    return deals


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="não posta, só imprime")
    parser.add_argument("--source", choices=sorted(SOURCES), help="roda só esta fonte")
    args = parser.parse_args()

    if not args.dry_run and not (os.environ.get("TELEGRAM_BOT_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID")):
        log.error("Defina TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID (ou use --dry-run).")
        return 1

    seen = state.load_seen()
    seen_set = set(seen)

    candidates = [d for d in collect(args.source) if d.id not in seen_set and passes_filters(d)]
    # Prioriza maiores descontos, depois temperatura.
    candidates.sort(key=lambda d: (d.discount_pct or 0, d.hot_score or 0), reverse=True)
    to_post = candidates[: config.MAX_POSTS_PER_RUN]

    log.info("%d candidatas após filtros/dedupe; postando %d", len(candidates), len(to_post))

    posted_ids = []
    for deal in to_post:
        if args.dry_run:
            print("-" * 60)
            print(telegram_poster.format_caption(deal))
            posted_ids.append(deal.id)
        elif telegram_poster.post(deal):
            log.info("Postado: %s", deal.title[:80])
            posted_ids.append(deal.id)

    if posted_ids and not args.dry_run:
        state.save_seen(seen + posted_ids)
    return 0


if __name__ == "__main__":
    sys.exit(main())
