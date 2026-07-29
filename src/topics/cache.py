"""Trending cache — Redis when configured, else a local file.

A precompute job (scripts/precompute_trending.py) writes a snapshot here so the
/api/trending endpoint serves it instantly. Redis (GPST_REDIS_URL) lets the
precompute job and the web service share the cache across separate containers
(the file cache only works when they share a filesystem). Falls back cleanly:
Redis -> file -> (caller computes on the fly).
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from ..config import PROJECT_ROOT

_CACHE_PATH = PROJECT_ROOT / "data" / "trending_cache.json"
_REDIS_KEY = "gpst:trending"


def _redis():
    url = os.getenv("GPST_REDIS_URL")
    if not url:
        return None
    try:
        import redis
        return redis.from_url(url, decode_responses=True, socket_timeout=3)
    except Exception:
        return None


def _is_stale(data: dict, max_age_hours: float | None) -> bool:
    if max_age_hours is None:
        return False
    try:
        ts = datetime.fromisoformat(data["computed_at"])
        age_h = (datetime.now(timezone.utc) - ts).total_seconds() / 3600.0
        return age_h > max_age_hours
    except Exception:
        return True


def write_trending(payload: dict) -> None:
    out = {**payload, "computed_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    blob = json.dumps(out)
    r = _redis()
    if r is not None:
        try:
            r.set(_REDIS_KEY, blob)
            return
        except Exception:
            pass  # fall through to file
    _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _CACHE_PATH.write_text(blob, encoding="utf-8")


def read_trending(max_age_hours: float | None = None) -> dict | None:
    """Return the cached payload (Redis first, then file), or None if missing/stale."""
    data = None
    r = _redis()
    if r is not None:
        try:
            s = r.get(_REDIS_KEY)
            data = json.loads(s) if s else None
        except Exception:
            data = None
    if data is None and _CACHE_PATH.exists():
        try:
            data = json.loads(_CACHE_PATH.read_text(encoding="utf-8"))
        except Exception:
            return None
    if data is None or _is_stale(data, max_age_hours):
        return None
    return data
