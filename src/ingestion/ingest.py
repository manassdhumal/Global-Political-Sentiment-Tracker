"""Ingestion orchestrator.

Loops over every (entity x country) in the watchlist for a date window and
returns raw per-article records as a DataFrame. Two interchangeable sources
sit behind one interface:

    source='gdelt'      -- live GDELT DOC 2.0 API
    source='synthetic'  -- deterministic offline fallback (fabricated)
    source='auto'       -- try GDELT; fall back to synthetic if unavailable

The output schema is identical regardless of source, so cleaning,
storage, aggregation and the dashboard never care where data came from.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone

import pandas as pd
import requests

from ..config import Watchlist
from . import gdelt_client, synthetic

log = logging.getLogger(__name__)

RAW_COLUMNS = ["entity_id", "country", "url", "title", "domain",
               "language", "seen_date", "tone", "source"]


@dataclass
class IngestResult:
    articles: pd.DataFrame
    source_used: str
    n_entities: int
    n_countries: int
    window: tuple[date, date]
    notes: list[str] = field(default_factory=list)


def default_window(weeks: int = 16, *, today: date | None = None) -> tuple[date, date]:
    """Return (start, end) for the last `weeks` weeks ending today (UTC)."""
    end = today or datetime.now(timezone.utc).date()
    return end - timedelta(weeks=weeks), end


def _gdelt_rows(wl: Watchlist, start: date, end: date,
                notes: list[str]) -> pd.DataFrame:
    rows: list[dict] = []
    with requests.Session() as session:
        for entity in wl.entities:
            for country in wl.gdelt_country_codes:
                try:
                    arts = gdelt_client.fetch_articles(
                        entity.query, country, start, end, session=session)
                except gdelt_client.GdeltError as exc:
                    notes.append(f"GDELT failed for {entity.id}/{country}: {exc}")
                    log.warning("GDELT failed for %s/%s: %s", entity.id, country, exc)
                    continue
                for a in arts:
                    rows.append({
                        "entity_id": entity.id, "country": a.country,
                        "url": a.url, "title": a.title, "domain": a.domain,
                        "language": a.language, "seen_date": a.seen_date,
                        "tone": a.tone, "source": "gdelt",
                    })
    return pd.DataFrame(rows, columns=RAW_COLUMNS)


def _synthetic_rows(wl: Watchlist, start: date, end: date) -> pd.DataFrame:
    rows: list[dict] = []
    for entity in wl.entities:
        for country in wl.gdelt_country_codes:
            arts = synthetic.fetch_articles(
                entity.id, entity.name, country, start, end,
                home_country=entity.home_country)
            for a in arts:
                rows.append({
                    "entity_id": entity.id, "country": a.country,
                    "url": a.url, "title": a.title, "domain": a.domain,
                    "language": a.language, "seen_date": a.seen_date,
                    "tone": a.tone, "source": "synthetic",
                })
    return pd.DataFrame(rows, columns=RAW_COLUMNS)


def ingest_watchlist(wl: Watchlist, *, source: str = "auto",
                     window: tuple[date, date] | None = None) -> IngestResult:
    """Pull raw article records for the whole watchlist.

    source: 'auto' | 'gdelt' | 'synthetic'
    """
    start, end = window or default_window()
    notes: list[str] = []

    if source == "auto":
        log.info("source='auto': probing GDELT availability…")
        if gdelt_client.health_check():
            log.info("GDELT reachable — using live data.")
            source = "gdelt"
        else:
            notes.append("GDELT unreachable/rate-limited — fell back to synthetic data.")
            log.warning("GDELT unavailable — using SYNTHETIC fallback data.")
            source = "synthetic"

    if source == "gdelt":
        df = _gdelt_rows(wl, start, end, notes)
        if df.empty:
            notes.append("GDELT returned no rows — falling back to synthetic data.")
            log.warning("GDELT returned 0 rows — using SYNTHETIC fallback.")
            df = _synthetic_rows(wl, start, end)
            source = "synthetic"
    elif source == "synthetic":
        df = _synthetic_rows(wl, start, end)
    else:
        raise ValueError(f"Unknown source '{source}' (use auto|gdelt|synthetic).")

    return IngestResult(
        articles=df, source_used=source,
        n_entities=wl.entities.__len__(),
        n_countries=len(wl.gdelt_country_codes),
        window=(start, end), notes=notes,
    )
