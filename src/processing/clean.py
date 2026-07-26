"""Cleaning / normalization of raw ingested articles.

Steps:
  1. drop rows missing an entity/country/date,
  2. standardize country codes (validate against the watchlist, uppercase),
  3. standardize dates to UTC ISO YYYY-MM-DD and derive the ISO-week Monday,
  4. compute a stable article id and de-duplicate on it.
"""
from __future__ import annotations

import hashlib

import pandas as pd

from ..config import Watchlist


def week_start_of(dt: pd.Series) -> pd.Series:
    """Monday (ISO week start) for a datetime series, as normalized dates."""
    dt = pd.to_datetime(dt, errors="coerce")
    return (dt - pd.to_timedelta(dt.dt.weekday, unit="D")).dt.normalize()


def _make_id(entity_id: str, country: str, url: str, title: str, day: str) -> str:
    key = url.strip() if isinstance(url, str) and url.strip() else f"{title}|{day}"
    raw = f"{entity_id}|{country}|{key}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def add_article_ids(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["id"] = [
        _make_id(r.entity_id, r.country, r.url or "", r.title or "", r.seen_date)
        for r in df.itertuples(index=False)
    ]
    return df


def clean_articles(df: pd.DataFrame, wl: Watchlist) -> pd.DataFrame:
    """Return a cleaned, de-duplicated article DataFrame with a `week_start`."""
    if df.empty:
        return df.assign(id=pd.Series(dtype=str), week_start=pd.Series(dtype="datetime64[ns]"))

    df = df.copy()

    # --- required fields present ---
    df = df.dropna(subset=["entity_id", "country", "seen_date"])

    # --- standardize country codes ---
    df["country"] = df["country"].astype(str).str.strip().str.upper()
    valid_countries = set(wl.gdelt_country_codes)
    unknown = set(df["country"]) - valid_countries
    if unknown:
        # Keep the pipeline honest: drop coverage from countries we don't track.
        df = df[df["country"].isin(valid_countries)]

    # --- validate entities against the watchlist ---
    valid_entities = set(wl.entity_ids)
    df = df[df["entity_id"].isin(valid_entities)]

    # --- standardize dates ---
    parsed = pd.to_datetime(df["seen_date"], errors="coerce", utc=False)
    df = df.assign(seen_dt=parsed).dropna(subset=["seen_dt"])
    df["seen_date"] = df["seen_dt"].dt.strftime("%Y-%m-%d")
    df["week_start"] = week_start_of(df["seen_dt"])

    # --- tone bounds sanity (GDELT tone lives in [-100, 100]) ---
    df["tone"] = pd.to_numeric(df["tone"], errors="coerce").clip(-100, 100)

    # --- stable id + dedupe ---
    df = add_article_ids(df)
    df = df.drop_duplicates(subset=["id"], keep="first")

    keep = ["id", "entity_id", "country", "url", "title", "domain",
            "language", "seen_date", "tone", "source", "week_start"]
    return df[keep].reset_index(drop=True)
