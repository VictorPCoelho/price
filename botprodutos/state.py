"""Dedupe entre execuções: data/seen.json guarda os IDs já postados.
O workflow do GitHub Actions commita o arquivo de volta ao repo."""

import json
from pathlib import Path

import config

SEEN_FILE = Path(__file__).parent / "data" / "seen.json"


def load_seen() -> list[str]:
    if SEEN_FILE.exists():
        try:
            return json.loads(SEEN_FILE.read_text())["posted"]
        except (json.JSONDecodeError, KeyError):
            return []
    return []


def save_seen(ids: list[str]) -> None:
    SEEN_FILE.parent.mkdir(exist_ok=True)
    trimmed = ids[-config.SEEN_MAX_IDS:]
    SEEN_FILE.write_text(json.dumps({"posted": trimmed}, indent=0) + "\n")
