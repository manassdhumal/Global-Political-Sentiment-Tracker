"""Aggregation: roll cleaned articles up to entity x country x ISO-week.

Produces the `aggregated_scores` rows: average media tone, article volume,
source diversity (distinct outlets), and a low-confidence flag for weeks
whose coverage is too thin to read much into.
"""
from __future__ import annotations

import pandas as pd

from .clean import week_start_of

# Confidence thresholds. A weekly score built on very few articles or a
# single outlet is flagged low-confidence so the UI can mark it. GDELT
# coverage is genuinely sparse for smaller countries, so this matters.
LOW_CONF_MIN_VOLUME = 5     # fewer than this many articles/week -> low conf
LOW_CONF_MIN_SOURCES = 2    # only one distinct outlet -> low conf

# Opinion (social) thresholds — a weekly social score needs enough posts and
# distinct authors to be worth reading (guards against a few vocal accounts).
OPINION_MIN_POSTS = 5
OPINION_MIN_AUTHORS = 3


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


def aggregate_opinion_weekly(posts: pd.DataFrame) -> pd.DataFrame:
    """Aggregate scored opinion posts to entity x source x week.

    Also emits a combined source='all' rollup per entity x week. Columns:
    entity_id, source, week_start, avg_sentiment, post_volume,
    unique_authors, low_confidence.
    """
    cols = ["entity_id", "source", "week_start", "avg_sentiment",
            "post_volume", "unique_authors", "low_confidence"]
    if posts.empty:
        return pd.DataFrame(columns=cols)

    df = posts.copy()
    df["week_start"] = week_start_of(df["created_date"])
    df = df.dropna(subset=["week_start"])

    def _agg(group_keys: list[str], source_label=None) -> pd.DataFrame:
        g = (df.groupby(group_keys, dropna=False)
             .agg(avg_sentiment=("sentiment", "mean"),
                  post_volume=("id", "count"),
                  unique_authors=("author_hash", "nunique"))
             .reset_index())
        if source_label is not None:
            g["source"] = source_label
        return g

    per_source = _agg(["entity_id", "source", "week_start"])
    combined = _agg(["entity_id", "week_start"], source_label="all")
    out = pd.concat([per_source, combined], ignore_index=True)

    out["low_confidence"] = (
        (out["post_volume"] < OPINION_MIN_POSTS)
        | (out["unique_authors"] < OPINION_MIN_AUTHORS)
    ).astype(int)
    out["week_start"] = pd.to_datetime(out["week_start"]).dt.strftime("%Y-%m-%d")
    out["avg_sentiment"] = out["avg_sentiment"].round(4)
    return out[cols].sort_values(["entity_id", "source", "week_start"]).reset_index(drop=True)
