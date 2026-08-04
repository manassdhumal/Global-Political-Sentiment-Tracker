"""Ingestion layer: pull coverage from GDELT, RSS news wires, Wikipedia, Reddit, Bluesky."""
from .ingest import ingest_watchlist, IngestResult  # noqa: F401
from .wikipedia_client import weekly_pageviews_series, fetch_daily_pageviews  # noqa: F401
from .rss_client import fetch_live_news, LiveArticle  # noqa: F401
