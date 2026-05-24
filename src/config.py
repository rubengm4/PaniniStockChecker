from __future__ import annotations

import os
from pathlib import Path

import yaml

from src.models import ProductWatch

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_WATCHLIST = ROOT / "config" / "watchlist.yaml"
DEFAULT_STATE_DB = ROOT / "data" / "state.db"


def watchlist_path() -> Path:
    return Path(os.environ.get("PANINI_WATCHLIST", DEFAULT_WATCHLIST))


def state_db_path() -> Path:
    return Path(os.environ.get("PANINI_STATE_DB", DEFAULT_STATE_DB))


def load_watchlist(path: Path | None = None) -> list[ProductWatch]:
    path = path or watchlist_path()
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    watches: list[ProductWatch] = []
    for entry in data.get("checks", []):
        if not entry.get("enabled", True):
            continue
        watches.append(
            ProductWatch(
                id=str(entry["id"]),
                store=str(entry["store"]),
                label=str(entry["label"]),
                url=str(entry["url"]),
                enabled=True,
            )
        )
    return watches
