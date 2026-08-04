"""Tests for Wikipedia Pageviews client."""
from datetime import date
import unittest.mock as mock
import pandas as pd

from src.ingestion.wikipedia_client import (
    normalize_wiki_title,
    fetch_daily_pageviews,
    weekly_pageviews_series,
    WIKI_TITLE_MAP,
)


def test_normalize_wiki_title():
    assert normalize_wiki_title("donald trump") == "Donald_Trump"
    assert normalize_wiki_title("inflation") == "Inflation"
    assert normalize_wiki_title("ai regulation") == "Regulation_of_artificial_intelligence"
    assert normalize_wiki_title("NATO") == "NATO"
    assert normalize_wiki_title("some unknown political issue") == "Some_unknown_political_issue"


def test_fetch_daily_pageviews_mocked():
    mock_resp = mock.MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "items": [
            {"timestamp": "2024010100", "views": 15200},
            {"timestamp": "2024010200", "views": 18400},
            {"timestamp": "2024010300", "views": 14100},
        ]
    }
    mock_session = mock.MagicMock()
    mock_session.get.return_value = mock_resp

    res = fetch_daily_pageviews("Inflation", date(2024, 1, 1), date(2024, 1, 3), session=mock_session)
    assert res == {
        "2024-01-01": 15200,
        "2024-01-02": 18400,
        "2024-01-03": 14100,
    }


def test_weekly_pageviews_series_mocked():
    sample_daily = {
        "2024-01-01": 1000,
        "2024-01-02": 2000,
        "2024-01-03": 3000,
        "2024-01-08": 4000,
    }
    with mock.patch("src.ingestion.wikipedia_client.fetch_daily_pageviews", return_value=sample_daily):
        df = weekly_pageviews_series("Inflation", date(2024, 1, 1), date(2024, 1, 8))
        assert not df.empty
        assert "week_start" in df.columns
        assert "pageviews" in df.columns
        assert "daily_avg" in df.columns
        assert len(df) == 2
        assert df.iloc[0]["pageviews"] == 6000
