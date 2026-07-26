"""GDELT DOC 2.0 API client.

Pulls news coverage for a (query, country, date-window) and returns
per-article records carrying a media-tone value.

------------------------------------------------------------------------
IMPORTANT LIMITATION — per-article tone
------------------------------------------------------------------------
The DOC 2.0 `artlist` mode returns article METADATA (url, domain,
language, source country, date) but NOT a per-article tone. GDELT's tone
is exposed at aggregate level via the `timelinetone` mode. So this client:
  1. pulls the article list (metadata + volume), and
  2. pulls the daily average-tone timeline for the same query, then
  3. assigns each article the AVERAGE tone of its day.
That is an approximation: within a day, articles are given the same tone.
True per-article tone requires GDELT's GKG / BigQuery tables — that is the
documented upgrade path. For weekly aggregation (our grain) the daily
average is a faithful signal.

GDELT rate-limits aggressively (HTTP 429). This client throttles requests
and retries with exponential backoff; callers should fall back to the
synthetic source (see ingest.py, source='auto') when GDELT is unavailable.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Optional

import requests

DOC_API = "https://api.gdeltproject.org/api/v2/doc/doc"
_USER_AGENT = "GlobalPoliticalSentimentTracker/0.1 (research; contact via app)"

# GDELT asks for gentle pacing; keep >=5s between calls from one client.
_MIN_INTERVAL_S = 5.0
_last_call_ts = 0.0


class GdeltError(RuntimeError):
    """Raised when GDELT cannot satisfy a request (rate limit, network…)."""


@dataclass
class GdeltArticle:
    url: str
    title: str
    domain: str
    language: str
    country: str          # GDELT source country code
    seen_date: str        # UTC ISO date, YYYY-MM-DD
    tone: Optional[float]  # daily-average approximation (see module docstring)


def _throttle() -> None:
    global _last_call_ts
    wait = _MIN_INTERVAL_S - (time.monotonic() - _last_call_ts)
    if wait > 0:
        time.sleep(wait)
    _last_call_ts = time.monotonic()


def _fmt_dt(d: date) -> str:
    return d.strftime("%Y%m%d000000")


def _get(params: dict, *, session: requests.Session,
         max_retries: int = 3, timeout: int = 30) -> dict:
    """GET the DOC API with throttling + exponential backoff. Returns JSON."""
    last_exc: Optional[Exception] = None
    for attempt in range(max_retries):
        _throttle()
        try:
            resp = session.get(DOC_API, params=params, timeout=timeout,
                               headers={"User-Agent": _USER_AGENT})
            if resp.status_code == 429:
                raise GdeltError("HTTP 429 Too Many Requests (rate limited)")
            resp.raise_for_status()
            text = resp.text.strip()
            if not text:
                return {}
            # GDELT sometimes returns an HTML error page instead of JSON.
            if not text.startswith("{"):
                raise GdeltError(f"Non-JSON response: {text[:120]!r}")
            return resp.json()
        except (requests.RequestException, GdeltError, ValueError) as exc:
            last_exc = exc
            backoff = _MIN_INTERVAL_S * (2 ** attempt)
            if attempt < max_retries - 1:
                time.sleep(backoff)
    raise GdeltError(f"GDELT request failed after {max_retries} attempts: {last_exc}")


def _parse_gdelt_date(s: str) -> str:
    """GDELT dates look like '20240115T120000Z' -> '2024-01-15'."""
    s = s.strip()
    return datetime.strptime(s[:8], "%Y%m%d").strftime("%Y-%m-%d")


def fetch_daily_tone(query: str, country: str, start: date, end: date,
                     *, session: requests.Session) -> dict[str, float]:
    """Return {YYYY-MM-DD: average_tone} for the query+country window."""
    full_query = f"{query} sourcecountry:{country}"
    params = {
        "query": full_query,
        "mode": "timelinetone",
        "format": "json",
        "startdatetime": _fmt_dt(start),
        "enddatetime": _fmt_dt(end),
    }
    data = _get(params, session=session)
    out: dict[str, float] = {}
    for series in data.get("timeline", []):
        for point in series.get("data", []):
            try:
                out[_parse_gdelt_date(point["date"])] = float(point["value"])
            except (KeyError, ValueError, TypeError):
                continue
    return out


def fetch_articles(query: str, country: str, start: date, end: date,
                   *, max_records: int = 250,
                   session: Optional[requests.Session] = None) -> list[GdeltArticle]:
    """Pull article metadata for the window and attach daily-average tone.

    See the module docstring for why tone is a daily-average approximation.
    """
    close_session = session is None
    session = session or requests.Session()
    try:
        daily_tone = fetch_daily_tone(query, country, start, end, session=session)
        overall = (sum(daily_tone.values()) / len(daily_tone)) if daily_tone else None

        full_query = f"{query} sourcecountry:{country}"
        params = {
            "query": full_query,
            "mode": "artlist",
            "format": "json",
            "maxrecords": str(max_records),
            "sort": "datedesc",
            "startdatetime": _fmt_dt(start),
            "enddatetime": _fmt_dt(end),
        }
        data = _get(params, session=session)

        articles: list[GdeltArticle] = []
        for a in data.get("articles", []):
            seen = a.get("seendate")
            if not seen:
                continue
            iso_day = _parse_gdelt_date(seen)
            articles.append(GdeltArticle(
                url=a.get("url", ""),
                title=a.get("title", ""),
                domain=a.get("domain", ""),
                language=a.get("language", ""),
                country=country,
                seen_date=iso_day,
                tone=daily_tone.get(iso_day, overall),
            ))
        return articles
    finally:
        if close_session:
            session.close()


def health_check() -> bool:
    """Return True if the DOC API answers a tiny query (used for source='auto')."""
    try:
        with requests.Session() as s:
            today = datetime.now(timezone.utc).date()
            fetch_daily_tone("inflation", "US",
                             today.replace(day=1), today, session=s)
        return True
    except GdeltError:
        return False
