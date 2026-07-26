"""Tests for the public-opinion layer: aggregation + media-vs-public compare."""
from __future__ import annotations

import pandas as pd

from src.processing.aggregate import (aggregate_opinion_weekly,
                                       OPINION_MIN_POSTS, OPINION_MIN_AUTHORS)
from src.analytics import media_vs_public


def _posts():
    rows = []
    for i in range(40):
        rows.append(dict(
            id=f"p{i}", entity_id="joe_biden",
            source="reddit" if i % 2 else "bluesky",
            community="r/x", lang="en", text="t",
            created_date="2026-05-04" if i < 20 else "2026-05-11",
            sentiment=20.0 if i % 2 else -10.0,
            author_hash=f"a{i % 7}", url=f"u{i}"))
    return pd.DataFrame(rows)


def test_opinion_aggregation_has_per_source_and_combined():
    agg = aggregate_opinion_weekly(_posts())
    sources = set(agg["source"])
    assert {"reddit", "bluesky", "all"} <= sources
    # combined 'all' for week 1 = mean(20, -10) = 5
    allrow = agg[(agg["source"] == "all") & (agg["week_start"] == "2026-05-04")].iloc[0]
    assert abs(allrow["avg_sentiment"] - 5.0) < 1e-6
    assert allrow["post_volume"] == 20


def test_opinion_low_confidence_flag():
    # 3 posts, 2 authors -> below thresholds -> low confidence
    posts = pd.DataFrame([
        dict(id=f"p{i}", entity_id="e1", source="reddit", community="r/x",
             lang="en", text="t", created_date="2026-05-04",
             sentiment=1.0, author_hash="a1" if i < 2 else "a2", url=f"u{i}")
        for i in range(3)
    ])
    agg = aggregate_opinion_weekly(posts)
    row = agg[agg["source"] == "reddit"].iloc[0]
    assert row["post_volume"] < OPINION_MIN_POSTS
    assert row["unique_authors"] < OPINION_MIN_AUTHORS
    assert row["low_confidence"] == 1


def test_media_vs_public_gap():
    media = pd.DataFrame([
        dict(entity_id="joe_biden", country="US", week_start=pd.Timestamp("2026-05-04"),
             avg_tone=-5.0, article_volume=50, source_diversity=5, low_confidence=0),
        dict(entity_id="joe_biden", country="US", week_start=pd.Timestamp("2026-05-11"),
             avg_tone=-3.0, article_volume=40, source_diversity=5, low_confidence=0),
    ])
    opinion = aggregate_opinion_weekly(_posts())
    opinion["week_start"] = pd.to_datetime(opinion["week_start"])
    mvp = media_vs_public(media, opinion, "joe_biden")
    assert not mvp.empty
    # week 1: public 5 - media -5 = +10
    r = mvp[mvp["week_start"] == pd.Timestamp("2026-05-04")].iloc[0]
    assert abs(r["gap"] - 10.0) < 1e-6
