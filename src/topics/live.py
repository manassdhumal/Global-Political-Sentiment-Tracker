"""Live data providers for the topic engine (GDELT media + social opinion).

Each function returns real data when reachable, or None on any failure so the
caller falls back to synthetic. Deliberately fast-failing (max_retries=1) so a
rate-limited GDELT / missing credentials degrade quickly rather than hanging.

NOTE: unverifiable where GDELT is rate-limited and no social credentials exist
(it will simply return None → synthetic). The transforms are unit-tested.
"""
from __future__ import annotations

import hashlib
import logging
from datetime import date

import pandas as pd
import requests

from ..ingestion import gdelt_client as gd
from ..ingestion import reddit_client, bluesky_client
from ..ingestion.reddit_client import OpinionError
from ..processing.aggregate import aggregate_opinion_weekly
from ..settings import which_opinion_sources
from ..nlp.sentiment import get_scorer, SentimentScorer

log = logging.getLogger(__name__)


def weekly_from_daily(tone: dict[str, float], vol: dict[str, float]) -> pd.DataFrame:
    """Collapse daily GDELT tone/volume into weekly rows (volume-weighted tone)."""
    dates = sorted(set(tone) | set(vol))
    if not dates:
        return pd.DataFrame(columns=["week_start", "avg_tone", "article_volume", "low_confidence"])
    df = pd.DataFrame({"date": pd.to_datetime(dates)})
    key = df["date"].dt.strftime("%Y-%m-%d")
    df["tone"] = key.map(tone)
    df["vol"] = key.map(vol).fillna(0.0)
    df["week_start"] = df["date"] - pd.to_timedelta(df["date"].dt.weekday, unit="D")
    rows = []
    for wk, g in df.groupby("week_start"):
        w = g["vol"].to_numpy(dtype=float)
        t = g["tone"].to_numpy(dtype=float)
        mask = ~pd.isna(t)
        if mask.sum() == 0:
            continue
        tt, ww = t[mask], w[mask]
        avg = float((tt * ww).sum() / ww.sum()) if ww.sum() > 0 else float(tt.mean())
        vol_wk = int(w.sum())
        rows.append({"week_start": wk, "avg_tone": round(avg, 3),
                     "article_volume": vol_wk,
                     "low_confidence": int(vol_wk < 5)})
    return pd.DataFrame(rows).sort_values("week_start").reset_index(drop=True)


def live_media(query: str, start: date, end: date, *, fast: bool = True) -> dict | None:
    """Global media weekly series (tone + volume) + recent driver titles, or None."""
    mr = 1 if fast else 3
    try:
        with requests.Session() as s:
            tone = gd.fetch_daily_tone(query, None, start, end, session=s, max_retries=mr)
            if not tone:
                return None
            try:
                vol = gd.fetch_daily_volume(query, None, start, end, session=s, max_retries=mr)
            except gd.GdeltError:
                vol = {}
            media = weekly_from_daily(tone, vol)
            if media.empty:
                return None
            try:
                arts = gd.fetch_articles(query, None, start, end, session=s, max_retries=mr)
                titles = [a.title for a in arts if a.title]
            except gd.GdeltError:
                titles = []
            return {"media": media, "titles": titles, "source": "gdelt"}
    except gd.GdeltError as exc:
        log.info("live_media fallback for %r: %s", query, exc)
        return None
    except Exception as exc:  # never let live break the request
        log.warning("live_media unexpected error for %r: %s", query, exc)
        return None


def _hash(s: str) -> str:
    return hashlib.sha1(s.encode()).hexdigest()[:16]


def live_opinion(query: str, start: date, end: date,
                 scorer: SentimentScorer | None = None) -> pd.DataFrame | None:
    """Weekly social sentiment for the query from configured sources, or None."""
    avail = [s for s, ok in which_opinion_sources().items() if ok]
    if not avail:
        return None
    fetchers = {"reddit": reddit_client.fetch_posts, "bluesky": bluesky_client.fetch_posts}
    posts = []
    for src in avail:
        try:
            posts.extend(fetchers[src](query, query, start, end))
        except OpinionError as exc:
            log.info("live_opinion %s failed for %r: %s", src, query, exc)
    if not posts:
        return None
    scorer = scorer or get_scorer()
    scores = scorer.score_many([p.text for p in posts])
    df = pd.DataFrame([{
        "id": _hash(f"{p.source}|{p.url or p.text}|{p.created_date}"),
        "entity_id": "topic", "source": p.source, "community": p.community,
        "lang": p.lang, "text": (p.text or "")[:280], "created_date": p.created_date,
        "sentiment": sc, "author_hash": _hash(p.author or "anon"), "url": p.url,
    } for p, sc in zip(posts, scores)]).drop_duplicates(subset=["id"])
    agg = aggregate_opinion_weekly(df)
    return agg if not agg.empty else None
