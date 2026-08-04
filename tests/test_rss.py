"""Tests for Global News RSS client."""
import unittest.mock as mock

from src.ingestion.rss_client import (
    _strip_html,
    _parse_pub_date,
    fetch_feed_articles,
    fetch_live_news,
)

SAMPLE_RSS_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>BBC News - World</title>
    <link>https://www.bbc.co.uk/news/world</link>
    <item>
      <title><![CDATA[Global Inflation Figures Show Promising Economic Stabilization]]></title>
      <link>https://www.bbc.co.uk/news/world-12345</link>
      <description><![CDATA[Central banks report inflation slowing down across major economies.]]></description>
      <pubDate>Mon, 15 Jan 2024 12:00:00 GMT</pubDate>
    </item>
    <item>
      <title>Leaders Convene for High-Stakes Geopolitical Summit</title>
      <link>https://www.bbc.co.uk/news/world-67890</link>
      <description>Diplomats discuss ongoing international tensions.</description>
      <pubDate>Tue, 16 Jan 2024 15:30:00 +0000</pubDate>
    </item>
  </channel>
</rss>
"""


def test_strip_html():
    assert _strip_html("<p>Hello <b>World</b></p>") == "Hello World"
    assert _strip_html("No tags here") == "No tags here"
    assert _strip_html("") == ""


def test_parse_pub_date():
    iso_ts, day = _parse_pub_date("Mon, 15 Jan 2024 12:00:00 GMT")
    assert "2024-01-15" in iso_ts
    assert day == "2024-01-15"


def test_fetch_feed_articles_mocked():
    mock_resp = mock.MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = SAMPLE_RSS_XML
    mock_session = mock.MagicMock()
    mock_session.get.return_value = mock_resp

    feed = {"outlet": "BBC News", "country": "GB", "url": "https://example.com/rss"}
    items = fetch_feed_articles(feed, session=mock_session)

    assert len(items) == 2
    assert items[0]["title"] == "Global Inflation Figures Show Promising Economic Stabilization"
    assert items[0]["outlet"] == "BBC News"
    assert items[0]["country"] == "GB"
    assert items[0]["link"] == "https://www.bbc.co.uk/news/world-12345"


def test_fetch_live_news_filtering_and_scoring():
    mock_resp = mock.MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = SAMPLE_RSS_XML
    mock_session = mock.MagicMock()
    mock_session.get.return_value = mock_resp

    feeds = [{"outlet": "BBC News", "country": "GB", "url": "https://example.com/rss"}]
    articles = fetch_live_news("inflation", feeds=feeds, session=mock_session)

    assert len(articles) == 1
    assert "Inflation" in articles[0].title
    assert isinstance(articles[0].sentiment, (int, float))
    assert articles[0].label in ("positive", "negative", "neutral")
