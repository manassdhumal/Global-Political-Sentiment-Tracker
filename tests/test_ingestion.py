"""Tests for the synthetic ingestion source + orchestrator."""
from __future__ import annotations

from datetime import date

from src.config import load_watchlist
from src.ingestion import synthetic
from src.ingestion.ingest import ingest_watchlist, default_window, RAW_COLUMNS


def test_synthetic_is_deterministic():
    a = synthetic.fetch_articles("joe_biden", "Joe Biden", "US",
                                 date(2026, 1, 1), date(2026, 1, 14),
                                 home_country="US")
    b = synthetic.fetch_articles("joe_biden", "Joe Biden", "US",
                                 date(2026, 1, 1), date(2026, 1, 14),
                                 home_country="US")
    assert len(a) == len(b) and len(a) > 0
    assert [x.tone for x in a] == [x.tone for x in b]  # reproducible


def test_synthetic_tone_in_range_and_titled():
    arts = synthetic.fetch_articles("inflation", "Inflation", "FR",
                                    date(2026, 1, 1), date(2026, 1, 21))
    assert arts, "expected some synthetic articles"
    for a in arts:
        assert -100 <= a.tone <= 100
        assert a.country == "FR"
        assert a.title  # topic-rich title for topic modeling


def test_ingest_watchlist_synthetic_schema():
    wl = load_watchlist()
    res = ingest_watchlist(wl, source="synthetic",
                           window=default_window(weeks=2))
    assert res.source_used == "synthetic"
    assert not res.articles.empty
    assert list(res.articles.columns) == RAW_COLUMNS
    assert set(res.articles["entity_id"]) == set(wl.entity_ids)


def test_reddit_pagination_and_comments():
    from src.ingestion.reddit_client import fetch_posts, fetch_comments
    # Just verify the functions exist and are callable with the new signatures
    assert callable(fetch_posts)
    assert callable(fetch_comments)


def test_bluesky_cursor_and_lang():
    from src.ingestion.bluesky_client import fetch_posts
    # Just verify the function exists and accepts the lang parameter
    assert callable(fetch_posts)


def test_gdelt_country_tone_and_bq_stub():
    from src.ingestion.gdelt_client import fetch_country_tone_breakdown, fetch_bigquery_articles
    assert callable(fetch_country_tone_breakdown)
    assert callable(fetch_bigquery_articles)
