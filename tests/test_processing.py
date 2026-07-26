"""Tests for cleaning/normalization and weekly aggregation."""
from __future__ import annotations

import pandas as pd

from src.config import load_watchlist
from src.processing.clean import clean_articles, week_start_of
from src.processing.aggregate import (aggregate_weekly, LOW_CONF_MIN_VOLUME,
                                       LOW_CONF_MIN_SOURCES)

WL = load_watchlist()
_VALID_COUNTRY = WL.gdelt_country_codes[0]
_VALID_ENTITY = WL.entity_ids[0]


def _raw(**over):
    base = dict(entity_id=_VALID_ENTITY, country=_VALID_COUNTRY,
                url="http://x/1", title="t", domain="a.example",
                language="English", seen_date="2026-01-05", tone=5.0,
                source="synthetic")
    base.update(over)
    return base


def test_week_start_is_monday():
    s = pd.Series(pd.to_datetime(["2026-01-07", "2026-01-11"]))  # Wed, Sun
    ws = week_start_of(s)
    assert all(d.weekday() == 0 for d in ws)  # Monday


def test_clean_dedupes_and_drops_unknown():
    df = pd.DataFrame([
        _raw(), _raw(),                                  # duplicate
        _raw(country="ZZ"),                              # unknown country -> dropped
        _raw(entity_id="not_a_real_entity"),            # unknown entity -> dropped
        _raw(seen_date="not-a-date"),                   # bad date -> dropped
        _raw(url="http://x/2", tone=250.0),             # tone clipped to 100
    ])
    out = clean_articles(df, WL)
    assert len(out) == 2                                # one dedup survivor + the /2 row
    assert out["tone"].max() <= 100
    assert set(out["country"]) <= set(WL.gdelt_country_codes)


def test_aggregate_weekly_and_low_confidence():
    # 3 articles, 1 outlet -> low confidence (few articles AND one source)
    df = pd.DataFrame([
        _raw(url="http://x/1", domain="a.example"),
        _raw(url="http://x/2", domain="a.example"),
        _raw(url="http://x/3", domain="a.example"),
    ])
    clean = clean_articles(df, WL)
    agg = aggregate_weekly(clean)
    assert len(agg) == 1
    row = agg.iloc[0]
    assert row["article_volume"] == 3
    assert row["source_diversity"] == 1
    assert row["low_confidence"] == 1
    assert row["article_volume"] < LOW_CONF_MIN_VOLUME
    assert row["source_diversity"] < LOW_CONF_MIN_SOURCES
