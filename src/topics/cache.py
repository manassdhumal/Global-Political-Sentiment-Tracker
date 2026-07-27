"""Lightweight caches for the topic engine.

- Trending file cache: a precompute job writes a snapshot here so the
  /api/trending endpoint serves it instantly (and can use expensive live data
  without paying the cost per request).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from ..config import PROJECT_ROOT

_CACHE_PATH = PROJECT_ROOT / "data" / "trending_cache.json"


def write_trending(payload: dict) -> None:
    _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    out = {**payload, "computed_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    _CACHE_PATH.write_text(json.dumps(out), encoding="utf-8")


def read_trending(max_age_hours: float | None = None) -> dict | None:
    """Return the cached trending payload, or None if missing/stale."""
    if not _CACHE_PATH.exists():
        return None
    try:
        data = json.loads(_CACHE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return None
    if max_age_hours is not None:
        try:
            ts = datetime.fromisoformat(data["computed_at"])
            age_h = (datetime.now(timezone.utc) - ts).total_seconds() / 3600.0
            if age_h > max_age_hours:
                return None
        except Exception:
            return None
    return data
