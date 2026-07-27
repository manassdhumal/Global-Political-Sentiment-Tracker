"""Trending computation over the catalog (recent volume + sentiment movement)."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from functools import lru_cache

import numpy as np
import pandas as pd

from . import synth, live, bigquery
from .catalog import Topic, load_catalog

_LIVE_SOURCES = {"auto", "live", "gdelt", "bigquery"}


def _media_global(t: Topic, end: date, source: str) -> pd.DataFrame:
    """Weekly global media (week_start, avg_tone, article_volume) for trending."""
    if source in _LIVE_SOURCES:
        start = end - timedelta(weeks=synth.MAX_WEEKS)
        bm = bigquery.bq_media_weekly(t.query, start, end) if source != "gdelt" else None
        if bm is not None and not bm.empty:
            return bm[["week_start", "avg_tone", "article_volume"]]
        lm = live.live_media(t.query, start, end)
        if lm:
            return lm["media"][["week_start", "avg_tone", "article_volume"]]
    return synth.global_weekly(t.query, end)


def _topic_row(t: Topic, end: date, source: str = "synthetic") -> dict | None:
    g = _media_global(t, end, source)
    if g.empty or len(g) < 2:
        return None
    tone = g["avg_tone"].to_numpy()
    vol = g["article_volume"].to_numpy()
    recent_vol = int(vol[-4:].sum())
    prev = float(np.mean(tone[-5:-1])) if len(tone) >= 5 else float(tone[0])
    movement = round(float(tone[-1] - prev), 2)

    op = synth.opinion_weekly(t.query, end)
    gap = None
    if not op.empty:
        allrows = op[op["source"] == "all"].sort_values("week_start")
        if not allrows.empty:
            gap = round(float(allrows["avg_sentiment"].iloc[-1] - tone[-1]), 2)

    spark = [round(float(x), 2) for x in tone[-12:]]
    return {
        "id": t.id, "label": t.label, "category": t.category,
        "latest_tone": round(float(tone[-1]), 2),
        "recent_volume": recent_vol,
        "movement": movement,
        "gap": gap,
        "spark": spark,
    }


@lru_cache(maxsize=16)
def _compute(end_iso: str, source: str) -> list[dict]:
    end = date.fromisoformat(end_iso)
    rows = [r for t in load_catalog() if (r := _topic_row(t, end, source))]
    if not rows:
        return []
    vols = np.array([r["recent_volume"] for r in rows], dtype=float)
    vmean, vstd = vols.mean(), (vols.std() or 1.0)
    for r in rows:
        vz = (r["recent_volume"] - vmean) / vstd
        r["trend_score"] = round(float(vz + abs(r["movement"]) / 3.0), 3)
    rows.sort(key=lambda r: r["trend_score"], reverse=True)
    return rows


def _all_rows(end: date | None = None, source: str = "synthetic") -> list[dict]:
    end = end or datetime.now(timezone.utc).date()
    end_m = end - timedelta(days=end.weekday())
    return _compute(end_m.isoformat(), source)


def trending(top_n: int = 12, end: date | None = None, source: str = "synthetic") -> list[dict]:
    return _all_rows(end, source)[:top_n]


def catalog_stats(end: date | None = None, source: str = "synthetic") -> list[dict]:
    """Every catalog topic with quick stats (for the Browse page)."""
    return sorted(_all_rows(end, source), key=lambda r: r["label"])


def global_snapshot(end: date | None = None, source: str = "synthetic") -> dict:
    rows = _all_rows(end, source)
    if not rows:
        return {"global_tone": None, "total_volume": 0, "n_topics": 0}
    vols = np.array([r["recent_volume"] for r in rows], dtype=float)
    tones = np.array([r["latest_tone"] for r in rows], dtype=float)
    tot = vols.sum()
    gaps = [r["gap"] for r in rows if r["gap"] is not None]
    movers = sorted(rows, key=lambda r: r["movement"])
    return {
        "global_tone": round(float((tones * vols).sum() / tot), 2) if tot else None,
        "total_volume": int(tot),
        "n_topics": len(rows),
        "avg_gap": round(float(np.mean(gaps)), 2) if gaps else None,
        "top_rising": [r for r in reversed(movers[-5:])],
        "top_falling": movers[:5],
    }
