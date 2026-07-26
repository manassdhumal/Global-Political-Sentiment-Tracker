"""Shared data-access helpers for the API (framework-agnostic, no Streamlit).

Mirrors what the old dashboard/common.py did: cached watchlist/events and an
enriched aggregated_scores DataFrame that refreshes when the DB file changes.
"""
from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path

import pandas as pd

from src.config import (DEFAULT_DB_PATH, load_events, load_watchlist,
                        Event, Watchlist)
from src import storage


@lru_cache(maxsize=1)
def get_watchlist() -> Watchlist:
    return load_watchlist()


@lru_cache(maxsize=1)
def get_events() -> list[Event]:
    return load_events()


_scores_cache: dict = {"mtime": None, "df": None, "n_synth": 0}


def _db_mtime() -> float | None:
    p = Path(DEFAULT_DB_PATH)
    return p.stat().st_mtime if p.exists() else None


def get_scores() -> pd.DataFrame:
    """Enriched aggregated_scores (entity/country names + iso3), cached by mtime."""
    mtime = _db_mtime()
    if mtime is None:
        return pd.DataFrame()
    if _scores_cache["mtime"] != mtime:
        wl = get_watchlist()
        conn = storage.connect(DEFAULT_DB_PATH)
        try:
            scores = storage.read_aggregated_scores(conn)
            entities = storage.list_entities(conn)
            row = conn.execute(
                "SELECT COUNT(*) FROM articles WHERE source='synthetic'").fetchone()
            n_synth = row[0] if row else 0
        finally:
            conn.close()
        if not scores.empty:
            scores = scores.merge(
                entities[["id", "name", "type"]].rename(
                    columns={"name": "entity_name", "type": "entity_type"}),
                left_on="entity_id", right_on="id", how="left").drop(columns=["id"])
            scores["country_name"] = scores["country"].map(wl.name_by_gdelt)
            scores["iso3"] = scores["country"].map(wl.iso3_by_gdelt)
        _scores_cache.update(mtime=mtime, df=scores, n_synth=n_synth)
    return _scores_cache["df"]


def synthetic_count() -> int:
    get_scores()  # ensure cache populated
    return _scores_cache["n_synth"]


_opinion_cache: dict = {"mtime": None, "df": None}


def get_opinion_scores() -> pd.DataFrame:
    """opinion_scores enriched with entity names, cached by DB mtime."""
    mtime = _db_mtime()
    if mtime is None:
        return pd.DataFrame()
    if _opinion_cache["mtime"] != mtime:
        wl = get_watchlist()
        conn = storage.connect(DEFAULT_DB_PATH)
        try:
            df = storage.read_opinion_scores(conn)
        finally:
            conn.close()
        if not df.empty:
            df["entity_name"] = df["entity_id"].map(wl.name_by_entity)
        _opinion_cache.update(mtime=mtime, df=df)
    return _opinion_cache["df"]


def opinion_ready() -> bool:
    df = get_opinion_scores()
    return df is not None and not df.empty


def data_ready() -> bool:
    df = get_scores()
    return df is not None and not df.empty


# ---------------------------------------------------------------------
# JSON-safety helpers
# ---------------------------------------------------------------------
def _clean_value(v):
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    if isinstance(v, (pd.Timestamp,)):
        return v.strftime("%Y-%m-%d")
    return v


def df_records(df: pd.DataFrame) -> list[dict]:
    """Convert a DataFrame to JSON-safe records (dates -> ISO, NaN -> null)."""
    if df is None or df.empty:
        return []
    out = df.copy()
    for col in out.columns:
        if pd.api.types.is_datetime64_any_dtype(out[col]):
            out[col] = out[col].dt.strftime("%Y-%m-%d")
    records = out.to_dict("records")
    return [{k: _clean_value(v) for k, v in r.items()} for r in records]


def weeks_range(df: pd.DataFrame) -> tuple[str | None, str | None]:
    if df is None or df.empty:
        return None, None
    return (df["week_start"].min().strftime("%Y-%m-%d"),
            df["week_start"].max().strftime("%Y-%m-%d"))
