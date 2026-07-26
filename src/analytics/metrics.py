"""Analytical computations over the aggregated_scores frame.

Expected input columns (from storage.read_aggregated_scores):
    entity_id, country, week_start (datetime64), avg_tone,
    article_volume, source_diversity, low_confidence
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def _weighted_mean(values: pd.Series, weights: pd.Series) -> float:
    w = weights.to_numpy(dtype=float)
    v = values.to_numpy(dtype=float)
    total = w.sum()
    return float((v * w).sum() / total) if total > 0 else float("nan")


def weekly_weighted_series(df: pd.DataFrame) -> pd.DataFrame:
    """Collapse multiple countries into one weekly series (volume-weighted tone).

    Returns columns: week_start, avg_tone, article_volume, source_diversity,
    low_confidence.
    """
    if df.empty:
        return df.assign(avg_tone=[], article_volume=[])
    rows = []
    for week, g in df.groupby("week_start"):
        rows.append({
            "week_start": week,
            "avg_tone": _weighted_mean(g["avg_tone"], g["article_volume"]),
            "article_volume": int(g["article_volume"].sum()),
            "source_diversity": int(g["source_diversity"].max()),
            "low_confidence": int(g["low_confidence"].max()),
        })
    return pd.DataFrame(rows).sort_values("week_start").reset_index(drop=True)


def country_tone_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Per-country volume-weighted average tone over the given rows.

    Used by the choropleth. Returns one row per country with avg_tone,
    total volume, max source diversity, and how many weekly cells were
    low-confidence (thin coverage).
    """
    cols = ["country", "avg_tone", "article_volume",
            "source_diversity", "low_conf_weeks", "n_weeks"]
    if df.empty:
        return pd.DataFrame(columns=cols)
    rows = []
    for country, g in df.groupby("country"):
        rows.append({
            "country": country,
            "avg_tone": _weighted_mean(g["avg_tone"], g["article_volume"]),
            "article_volume": int(g["article_volume"].sum()),
            "source_diversity": int(g["source_diversity"].max()),
            "low_conf_weeks": int(g["low_confidence"].sum()),
            "n_weeks": int(g["week_start"].nunique()),
        })
    return pd.DataFrame(rows, columns=cols).sort_values("avg_tone").reset_index(drop=True)


def volatility_index(df: pd.DataFrame, *, group: str = "entity_country",
                     min_weeks: int = 4) -> pd.DataFrame:
    """Rank the most-swinging series by std-dev of weekly tone.

    group:
        'entity_country' -> one row per (entity, country)
        'entity'         -> collapse countries (volume-weighted) per entity
        'country'        -> collapse entities (volume-weighted) per country
    min_weeks: series with fewer weekly points are excluded (too little to
               judge volatility on).
    """
    base_cols = ["volatility", "mean_tone", "tone_range",
                 "n_weeks", "article_volume"]
    if df.empty:
        keys = {"entity_country": ["entity_id", "country"],
                "entity": ["entity_id"], "country": ["country"]}[group]
        return pd.DataFrame(columns=keys + base_cols)

    if group == "entity_country":
        keys = ["entity_id", "country"]
        work = df.copy()
    elif group == "entity":
        keys = ["entity_id"]
        work = (df.groupby(["entity_id", "week_start"])
                .apply(lambda g: pd.Series({
                    "avg_tone": _weighted_mean(g["avg_tone"], g["article_volume"]),
                    "article_volume": g["article_volume"].sum()}),
                    include_groups=False)
                .reset_index())
    elif group == "country":
        keys = ["country"]
        work = (df.groupby(["country", "week_start"])
                .apply(lambda g: pd.Series({
                    "avg_tone": _weighted_mean(g["avg_tone"], g["article_volume"]),
                    "article_volume": g["article_volume"].sum()}),
                    include_groups=False)
                .reset_index())
    else:
        raise ValueError(f"Unknown group '{group}'.")

    rows = []
    for key_vals, g in work.groupby(keys):
        if g["week_start"].nunique() < min_weeks:
            continue
        tones = g["avg_tone"].to_numpy(dtype=float)
        rec = dict(zip(keys, key_vals if isinstance(key_vals, tuple) else (key_vals,)))
        rec.update({
            "volatility": round(float(np.std(tones, ddof=1)), 3),
            "mean_tone": round(float(np.mean(tones)), 3),
            "tone_range": round(float(tones.max() - tones.min()), 3),
            "n_weeks": int(g["week_start"].nunique()),
            "article_volume": int(g["article_volume"].sum()),
        })
        rows.append(rec)

    out = pd.DataFrame(rows, columns=keys + base_cols)
    return out.sort_values("volatility", ascending=False).reset_index(drop=True)


def issue_association(df: pd.DataFrame) -> pd.DataFrame:
    """For a single theme's rows, rank countries by volume and tone.

    Returns one row per country: article_volume, avg_tone, source_diversity.
    Caller should pre-filter `df` to the theme of interest.
    """
    return country_tone_summary(df).sort_values(
        "article_volume", ascending=False).reset_index(drop=True)
