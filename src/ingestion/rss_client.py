"""Global News RSS Client.

Fetches live breaking news headlines from major international news wires:
BBC News, Al Jazeera, Deutsche Welle, The Guardian, France 24, NPR, etc.
Extracts title, published date, outlet, URL, and runs on-the-fly sentiment scoring.

Free, public, no API keys required.
"""
from __future__ import annotations

import email.utils
import logging
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import requests

from ..nlp.sentiment import get_scorer, SentimentScorer, score_to_label

log = logging.getLogger(__name__)

USER_AGENT = "GlobalPoliticalSentimentTracker/1.0 (news-monitor; research)"

# Curated high-reliability global RSS feeds with outlet and country tags
GLOBAL_FEEDS: list[dict[str, str]] = [
    {
        "outlet": "BBC News",
        "country": "GB",
        "url": "https://feeds.bbci.co.uk/news/world/rss.xml",
    },
    {
        "outlet": "Al Jazeera",
        "country": "QA",
        "url": "https://www.aljazeera.com/xml/rss/all.xml",
    },
    {
        "outlet": "Deutsche Welle",
        "country": "DE",
        "url": "https://rss.dw.com/rdf/rss-en-all",
    },
    {
        "outlet": "The Guardian",
        "country": "GB",
        "url": "https://www.theguardian.com/world/rss",
    },
    {
        "outlet": "France 24",
        "country": "FR",
        "url": "https://www.france24.com/en/rss",
    },
    {
        "outlet": "NPR News",
        "country": "US",
        "url": "https://feeds.npr.org/1004/rss.xml",
    },
    {
        "outlet": "CNBC World",
        "country": "US",
        "url": "https://search.cnbc.com/rs/search/view.html?partnerId=2000&keywords=politics&format=rss",
    },
]


@dataclass
class LiveArticle:
    title: str
    link: str
    published: str          # ISO string YYYY-MM-DD HH:MM UTC
    published_date: str     # YYYY-MM-DD
    outlet: str
    country: str
    summary: str
    sentiment: float        # -100 .. +100
    label: str              # positive | negative | neutral


def _strip_html(text: str) -> str:
    if not text:
        return ""
    clean = re.sub(r"<[^>]+>", " ", text)
    return " ".join(clean.split()).strip()


def _parse_pub_date(pub_str: str) -> tuple[str, str]:
    """Parse RSS RFC 822/2822 dates to (ISO timestamp, YYYY-MM-DD)."""
    if not pub_str:
        now = datetime.now(timezone.utc)
        return now.strftime("%Y-%m-%d %H:%M UTC"), now.strftime("%Y-%m-%d")
    try:
        dt = email.utils.parsedate_to_datetime(pub_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt.strftime("%Y-%m-%d %H:%M UTC"), dt.strftime("%Y-%m-%d")
    except Exception:
        pass
    try:
        dt = datetime.fromisoformat(pub_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M UTC"), dt.strftime("%Y-%m-%d")
    except Exception:
        now = datetime.now(timezone.utc)
        return now.strftime("%Y-%m-%d %H:%M UTC"), now.strftime("%Y-%m-%d")


def fetch_feed_articles(
    feed: dict[str, str],
    *,
    session: Optional[requests.Session] = None,
    timeout: int = 10,
) -> list[dict]:
    """Fetch and parse items from a single RSS feed."""
    url = feed["url"]
    outlet = feed["outlet"]
    country = feed["country"]
    headers = {"User-Agent": USER_AGENT}

    close_session = session is None
    sess = session or requests.Session()
    try:
        resp = sess.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)

        items: list[dict] = []
        # Support standard RSS <channel><item> and RDF/Atom <item>/<entry>
        channel_items = root.findall(".//item")
        if not channel_items:
            channel_items = root.findall(".//{http://www.w3.org/2005/Atom}entry")
            if not channel_items:
                channel_items = root.findall(".//{http://purl.org/rss/1.0/}item")

        for el in channel_items:
            title = el.findtext("title") or el.findtext("{http://www.w3.org/2005/Atom}title") or ""
            link = el.findtext("link") or el.findtext("{http://www.w3.org/2005/Atom}link") or ""
            if not link and el.find("{http://www.w3.org/2005/Atom}link") is not None:
                link = el.find("{http://www.w3.org/2005/Atom}link").get("href", "")
            pub = (el.findtext("pubDate")
                   or el.findtext("published")
                   or el.findtext("{http://purl.org/dc/elements/1.1/}date")
                   or el.findtext("{http://www.w3.org/2005/Atom}published")
                   or el.findtext("{http://www.w3.org/2005/Atom}updated")
                   or "")
            desc = (el.findtext("description")
                    or el.findtext("summary")
                    or el.findtext("{http://www.w3.org/2005/Atom}summary")
                    or "")

            title_clean = _strip_html(title)
            desc_clean = _strip_html(desc)
            if not title_clean:
                continue

            iso_ts, iso_day = _parse_pub_date(pub)
            items.append({
                "title": title_clean,
                "link": link.strip(),
                "published": iso_ts,
                "published_date": iso_day,
                "outlet": outlet,
                "country": country,
                "summary": desc_clean[:300],
            })
        return items
    except Exception as exc:
        log.info("RSS fetch failed for %s (%s): %s", outlet, url, exc)
        return []
    finally:
        if close_session:
            sess.close()


def fetch_live_news(
    query: str = "",
    *,
    feeds: Optional[list[dict[str, str]]] = None,
    max_articles: int = 30,
    scorer: Optional[SentimentScorer] = None,
    session: Optional[requests.Session] = None,
) -> list[LiveArticle]:
    """Fetch live news from global feeds, optionally filtering by topic query and scoring tone."""
    target_feeds = feeds or GLOBAL_FEEDS
    close_session = session is None
    sess = session or requests.Session()
    raw_articles: list[dict] = []

    try:
        for feed in target_feeds:
            raw_articles.extend(fetch_feed_articles(feed, session=sess))
    finally:
        if close_session:
            sess.close()

    # Match query tokens if provided
    matched: list[dict] = []
    tokens = [t.lower() for t in query.split() if len(t) > 2]
    for art in raw_articles:
        text_corpus = f"{art['title']} {art['summary']}".lower()
        if not tokens or any(tok in text_corpus for tok in tokens):
            matched.append(art)

    # If query is very specific and yielded 0 matches, take general political wire items
    pool = matched if matched else raw_articles[:max_articles]
    pool = pool[:max_articles]

    scorer = scorer or get_scorer()
    scored_articles: list[LiveArticle] = []
    for item in pool:
        eval_text = f"{item['title']}. {item['summary']}".strip()
        score = scorer.score(eval_text)
        scored_articles.append(LiveArticle(
            title=item["title"],
            link=item["link"],
            published=item["published"],
            published_date=item["published_date"],
            outlet=item["outlet"],
            country=item["country"],
            summary=item["summary"],
            sentiment=score,
            label=score_to_label(score),
        ))

    return scored_articles


def health_check() -> bool:
    """Check if at least one global RSS feed is accessible."""
    try:
        items = fetch_feed_articles(GLOBAL_FEEDS[0], timeout=5)
        return len(items) > 0
    except Exception:
        return False
