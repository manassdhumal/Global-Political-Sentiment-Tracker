"""Aggregation: roll cleaned articles up to entity x country x ISO-week.

Produces the `aggregated_scores` rows: average media tone, article volume,
source diversity (distinct outlets), and a low-confidence flag for weeks
whose coverage is too thin to read much into.
"""
from __future__ import annotations

import pandas as pd

# Confidence thresholds. A weekly score built on very few articles or a
# single outlet is flagged low-confidence so the UI can mark it. GDELT
# coverage is genuinely sparse for smaller countries, so this matters.
LOW_CONF_MIN_VOLUME = 5     # fewer than this many articles/week -> low conf
LOW_CONF_MIN_SOURCES = 2    # only one distinct outlet -> low conf


def aggregate_weekly(clean_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate cleaned articles into weekly entity x country scores."""
    cols = ["entity_id", "country", "week_start", "avg_tone",
            "article_volume", "source_diversity", "low_confidence"]
    if clean_df.empty:
        return pd.DataFrame(columns=cols)

    grouped = (
        clean_df.groupby(["entity_id", "country", "week_start"], dropna=False)
        .agg(
            avg_tone=("tone", "mean"),
            article_volume=("id", "count"),
            source_diversity=("domain", "nunique"),
        )
        .reset_index()
    )

    grouped["low_confidence"] = (
        (grouped["article_volume"] < LOW_CONF_MIN_VOLUME)
        | (grouped["source_diversity"] < LOW_CONF_MIN_SOURCES)
    ).astype(int)

    # Store week_start as an ISO date string for the DB.
    grouped["week_start"] = pd.to_datetime(grouped["week_start"]).dt.strftime("%Y-%m-%d")
    grouped["avg_tone"] = grouped["avg_tone"].round(4)

    return grouped[cols].sort_values(["entity_id", "country", "week_start"]).reset_index(drop=True)
