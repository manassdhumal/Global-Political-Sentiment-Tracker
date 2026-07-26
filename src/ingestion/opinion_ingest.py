"""Public-opinion ingestion orchestrator.

For each watchlist entity, pulls posts from the configured source(s), scores
each post's TEXT with the shared NLP sentiment model (RoBERTa if available,
VADER otherwise), and returns scored posts as a DataFrame.

Sources (behind one interface, mirroring the media pipeline):
    source='reddit' | 'bluesky'  -- live (needs .env credentials)
    source='synthetic'           -- deterministic offline fallback (fabricated)
    source='auto'                -- use whichever live sources have creds;
                                    fall back to synthetic if none/empty

Author handles are HASHED before storage (privacy). Output is identical in
shape regardless of source.
"""
from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import date

import pandas as pd

from ..config import Watchlist
from ..nlp.sentiment import get_scorer
from ..settings import which_opinion_sources, sentiment_backend
from . import opinion_synthetic, reddit_client, bluesky_client
from .opinion_types import OpinionPost

log = logging.getLogger(__name__)

POST_COLUMNS = ["id", "entity_id", "source", "community", "lang", "text",
                "created_date", "sentiment", "author_hash", "url"]


@dataclass
class OpinionIngestResult:
    posts: pd.DataFrame
    source_used: str
    backend: str
    window: tuple[date, date]
    notes: list[str] = field(default_factory=list)


def _hash(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:16]


def _search_query(entity) -> str:
    """Plain-text search query for social platforms (not GDELT syntax)."""
    return entity.name


def _live_posts(wl: Watchlist, sources: list[str], start: date, end: date,
                notes: list[str]) -> list[OpinionPost]:
    posts: list[OpinionPost] = []
    fetchers = {"reddit": reddit_client.fetch_posts,
                "bluesky": bluesky_client.fetch_posts}
    for src in sources:
        fetch = fetchers[src]
        for entity in wl.entities:
            try:
                got = fetch(entity.id, _search_query(entity), start, end)
                posts.extend(got)
            except reddit_client.OpinionError as exc:
                notes.append(f"{src} failed for {entity.id}: {exc}")
                log.warning("%s failed for %s: %s", src, entity.id, exc)
    return posts


def _synthetic_posts(wl: Watchlist, start: date, end: date) -> list[OpinionPost]:
    posts: list[OpinionPost] = []
    for entity in wl.entities:
        posts.extend(opinion_synthetic.fetch_posts(
            entity.id, entity.name, start, end))
    return posts


def ingest_opinion(wl: Watchlist, *, source: str = "auto",
                   window: tuple[date, date], backend: str | None = None
                   ) -> OpinionIngestResult:
    start, end = window
    notes: list[str] = []

    if source == "auto":
        avail = [s for s, ok in which_opinion_sources().items() if ok]
        if avail:
            source_list, source_used = avail, "+".join(avail)
            posts = _live_posts(wl, avail, start, end, notes)
            if not posts:
                notes.append("Live sources returned no posts — using synthetic.")
                posts, source_used = _synthetic_posts(wl, start, end), "synthetic"
        else:
            notes.append("No opinion credentials configured — using synthetic data.")
            posts, source_used = _synthetic_posts(wl, start, end), "synthetic"
    elif source in ("reddit", "bluesky"):
        posts = _live_posts(wl, [source], start, end, notes)
        source_used = source
        if not posts:
            notes.append(f"{source} returned no posts — using synthetic.")
            posts, source_used = _synthetic_posts(wl, start, end), "synthetic"
    elif source == "synthetic":
        posts, source_used = _synthetic_posts(wl, start, end), "synthetic"
    else:
        raise ValueError(f"Unknown source '{source}'.")

    if not posts:
        return OpinionIngestResult(pd.DataFrame(columns=POST_COLUMNS),
                                   source_used, backend or "none", window, notes)

    # --- score every post's text with the shared NLP model (batched) ---
    scorer = get_scorer(backend or sentiment_backend())
    texts = [p.text for p in posts]
    scores = scorer.score_many(texts)

    rows = []
    for p, s in zip(posts, scores):
        rows.append({
            "id": _hash(f"{p.source}|{p.entity_id}|{p.url or p.text}|{p.created_date}"),
            "entity_id": p.entity_id, "source": p.source,
            "community": p.community, "lang": p.lang,
            "text": (p.text or "")[:280], "created_date": p.created_date,
            "sentiment": s, "author_hash": _hash(p.author or "anon"),
            "url": p.url,
        })
    df = pd.DataFrame(rows, columns=POST_COLUMNS).drop_duplicates(subset=["id"])
    return OpinionIngestResult(df, source_used, scorer.backend, window, notes)
