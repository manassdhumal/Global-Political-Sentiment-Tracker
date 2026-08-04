"""Wikimedia REST API client for real-world public attention (Pageviews).

Fetches daily/weekly pageviews for political figures, parties, issues, and
institutions from the official Wikimedia REST API.
Endpoint: https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/

Public, free, no API key required (requires a respectful User-Agent header).
"""
from __future__ import annotations

import logging
import urllib.parse
from datetime import date, datetime, timedelta, timezone
from typing import Optional

import pandas as pd
import requests

log = logging.getLogger(__name__)

API_BASE = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article"
USER_AGENT = "GlobalPoliticalSentimentTracker/1.0 (research; https://github.com/manassdhumal/Global-Political-Sentiment-Tracker)"

# Common topic query -> Wikipedia canonical article title mappings
WIKI_TITLE_MAP: dict[str, str] = {
    "joe biden": "Joe_Biden",
    "joe_biden": "Joe_Biden",
    "donald trump": "Donald_Trump",
    "donald_trump": "Donald_Trump",
    "kamala harris": "Kamala_Harris",
    "kamala_harris": "Kamala_Harris",
    "keir starmer": "Keir_Starmer",
    "keir_starmer": "Keir_Starmer",
    "rishi sunak": "Rishi_Sunak",
    "rishi_sunak": "Rishi_Sunak",
    "justin trudeau": "Justin_Trudeau",
    "justin_trudeau": "Justin_Trudeau",
    "emmanuel macron": "Emmanuel_Macron",
    "emmanuel_macron": "Emmanuel_Macron",
    "olaf scholz": "Olaf_Scholz",
    "olaf_scholz": "Olaf_Scholz",
    "friedrich merz": "Friedrich_Merz",
    "friedrich_merz": "Friedrich_Merz",
    "giorgia meloni": "Giorgia_Meloni",
    "giorgia_meloni": "Giorgia_Meloni",
    "pedro sanchez": "Pedro_Sánchez",
    "pedro_sanchez": "Pedro_Sánchez",
    "ursula von der leyen": "Ursula_von_der_Leyen",
    "ursula_vdl": "Ursula_von_der_Leyen",
    "vladimir putin": "Vladimir_Putin",
    "vladimir_putin": "Vladimir_Putin",
    "volodymyr zelensky": "Volodymyr_Zelenskyy",
    "volodymyr_zelensky": "Volodymyr_Zelenskyy",
    "narendra modi": "Narendra_Modi",
    "narendra_modi": "Narendra_Modi",
    "xi jinping": "Xi_Jinping",
    "xi_jinping": "Xi_Jinping",
    "kim jong un": "Kim_Jong_Un",
    "kim_jong_un": "Kim_Jong_Un",
    "fumio kishida": "Fumio_Kishida",
    "fumio_kishida": "Fumio_Kishida",
    "anthony albanese": "Anthony_Albanese",
    "anthony_albanese": "Anthony_Albanese",
    "lula": "Luiz_Inácio_Lula_da_Silva",
    "javier milei": "Javier_Milei",
    "javier_milei": "Javier_Milei",
    "claudia sheinbaum": "Claudia_Sheinbaum",
    "claudia_sheinbaum": "Claudia_Sheinbaum",
    "erdogan": "Recep_Tayyip_Erdoğan",
    "netanyahu": "Benjamin_Netanyahu",
    "mbs": "Mohammed_bin_Salman",
    "ramaphosa": "Cyril_Ramaphosa",
    # Parties
    "democratic party": "Democratic_Party_(United_States)",
    "us_democrats": "Democratic_Party_(United_States)",
    "republican party": "Republican_Party_(United_States)",
    "us_republicans": "Republican_Party_(United_States)",
    "labour party": "Labour_Party_(UK)",
    "uk_labour": "Labour_Party_(UK)",
    "conservative party": "Conservative_Party_(UK)",
    "uk_conservatives": "Conservative_Party_(UK)",
    "reform uk": "Reform_UK",
    "uk_reform": "Reform_UK",
    "afd": "Alternative_for_Germany",
    "de_afd": "Alternative_for_Germany",
    "rassemblement national": "National_Rally",
    "fr_rn": "National_Rally",
    "bjp": "Bharatiya_Janata_Party",
    "in_bjp": "Bharatiya_Janata_Party",
    "indian national congress": "Indian_National_Congress",
    "in_congress": "Indian_National_Congress",
    # Issues
    "inflation": "Inflation",
    "unemployment": "Unemployment",
    "housing": "Housing_affordability",
    "taxation": "Tax",
    "immigration": "Immigration",
    "climate": "Climate_change",
    "energy prices": "Energy_crisis",
    "energy_prices": "Energy_crisis",
    "healthcare": "Health_care",
    "education": "Education",
    "abortion": "Abortion",
    "gun control": "Gun_control",
    "gun_control": "Gun_control",
    "crime": "Crime",
    "corruption": "Corruption",
    "ai regulation": "Regulation_of_artificial_intelligence",
    "ai_regulation": "Regulation_of_artificial_intelligence",
    "artificial intelligence": "Artificial_intelligence",
    "data privacy": "Information_privacy",
    "data_privacy": "Information_privacy",
    "free speech": "Freedom_of_speech",
    "free_speech": "Freedom_of_speech",
    "trade tariffs": "Tariff",
    "trade_tariffs": "Tariff",
    "pensions": "Pension",
    "defense spending": "Military_budget",
    "defense_spending": "Military_budget",
    "elections": "Election",
    "misinformation": "Misinformation",
    "refugees": "Refugee",
    "food security": "Food_security",
    "food_security": "Food_security",
    "water scarcity": "Water_scarcity",
    "water_scarcity": "Water_scarcity",
    # Institutions & Geopolitics
    "european union": "European_Union",
    "european_union": "European_Union",
    "united nations": "United_Nations",
    "united_nations": "United_Nations",
    "nato": "NATO",
    "who": "World_Health_Organization",
    "imf": "International_Monetary_Fund",
    "world bank": "World_Bank",
    "world_bank": "World_Bank",
    "us fed": "Federal_Reserve",
    "us_fed": "Federal_Reserve",
    "federal reserve": "Federal_Reserve",
    "ecb": "European_Central_Bank",
    "supreme court": "Supreme_Court_of_the_United_States",
    "us_supreme_court": "Supreme_Court_of_the_United_States",
    "opec": "OPEC",
    "ukraine war": "Russian_invasion_of_Ukraine",
    "ukraine_war": "Russian_invasion_of_Ukraine",
    "middle east": "Middle_Eastern_conflict",
    "middle_east": "Middle_Eastern_conflict",
    "taiwan": "Cross-Strait_relations",
    "brexit": "Brexit",
    "sanctions": "International_sanctions",
}


def normalize_wiki_title(query: str) -> str:
    """Resolve a free-text or catalog query to a canonical Wikipedia page title."""
    clean = query.strip().lower()
    if clean in WIKI_TITLE_MAP:
        return WIKI_TITLE_MAP[clean]
    # Generic title casing: "artificial intelligence" -> "Artificial_intelligence"
    parts = query.strip().split()
    if not parts:
        return "Main_Page"
    capitalized = parts[0].capitalize() + ("_" + "_".join(parts[1:]) if len(parts) > 1 else "")
    return capitalized


def fetch_daily_pageviews(
    article: str,
    start: date,
    end: date,
    *,
    project: str = "en.wikipedia",
    session: Optional[requests.Session] = None,
    timeout: int = 15,
) -> dict[str, int]:
    """Fetch daily user pageviews for a Wikipedia article.

    Returns {YYYY-MM-DD: pageview_count}.
    """
    article_title = normalize_wiki_title(article)
    # Wikimedia date format: YYYYMMDD
    start_str = start.strftime("%Y%m%d")
    end_str = end.strftime("%Y%m%d")
    encoded_title = urllib.parse.quote(article_title, safe="")

    url = f"{API_BASE}/{project}/all-access/user/{encoded_title}/daily/{start_str}/{end_str}"
    headers = {"User-Agent": USER_AGENT}

    close_session = session is None
    sess = session or requests.Session()
    try:
        resp = sess.get(url, headers=headers, timeout=timeout)
        if resp.status_code == 404:
            log.info("Wikipedia pageviews: article %r not found", article_title)
            return {}
        resp.raise_for_status()
        data = resp.json()
        items = data.get("items", [])
        out = {}
        for item in items:
            ts = item.get("timestamp", "")
            views = item.get("views", 0)
            if len(ts) >= 8:
                day_str = f"{ts[:4]}-{ts[4:6]}-{ts[6:8]}"
                out[day_str] = int(views)
        return out
    except Exception as exc:
        log.warning("Wikipedia pageviews request failed for %r: %s", article_title, exc)
        return {}
    finally:
        if close_session:
            sess.close()


def weekly_pageviews_series(
    article: str,
    start: date,
    end: date,
    *,
    session: Optional[requests.Session] = None,
) -> pd.DataFrame:
    """Fetch and aggregate daily pageviews into weekly attention index."""
    daily = fetch_daily_pageviews(article, start, end, session=session)
    if not daily:
        return pd.DataFrame(columns=["week_start", "pageviews", "daily_avg"])

    df = pd.DataFrame(list(daily.items()), columns=["date_str", "views"])
    df["date"] = pd.to_datetime(df["date_str"])
    df["week_start"] = df["date"] - pd.to_timedelta(df["date"].dt.weekday, unit="D")

    rows = []
    for wk, g in df.groupby("week_start"):
        tot = int(g["views"].sum())
        avg = round(float(g["views"].mean()), 1)
        rows.append({"week_start": wk, "pageviews": tot, "daily_avg": avg})

    out = pd.DataFrame(rows).sort_values("week_start").reset_index(drop=True)
    return out


def health_check() -> bool:
    """Check if the Wikimedia Pageviews REST API is reachable."""
    try:
        today = datetime.now(timezone.utc).date()
        w0 = today - timedelta(days=7)
        data = fetch_daily_pageviews("Inflation", w0, today, timeout=5)
        return bool(data)
    except Exception:
        return False
