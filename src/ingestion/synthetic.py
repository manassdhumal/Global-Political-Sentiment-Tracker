"""Synthetic coverage source — deterministic offline fallback.

Why this exists: GDELT rate-limits aggressively (HTTP 429) and requires
network access. To keep the whole pipeline runnable, testable and
demonstrable end-to-end without a live API, this module fabricates
realistic per-article records behind the SAME interface as the GDELT
client (per-article rows carrying a tone value).

The data is DETERMINISTIC (seeded per entity+country) and includes a
slow trend, weekly seasonality, noise, and one injected "event shock"
per series — so the downstream time-series, volatility, anomaly and
event features have real structure to detect.

!!! This is FABRICATED DATA. It is clearly tagged source='synthetic' in
    the DB and must never be presented as real media coverage. It is a
    development/demo stand-in for the GDELT feed only. !!!
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

import numpy as np

# Fake outlet domains per country, so "source diversity" has something to
# count. Names are obviously synthetic (.example) to avoid implying real
# outlets. Countries without a curated pool get a generated one (see
# _outlets_for) so the source-diversity metric scales to ANY watchlist.
_OUTLETS = {
    "US": ["examplewire.us", "libertypost.example", "beltwaydaily.example",
           "heartlandnews.example", "coastalledger.example"],
    "UK": ["albiontimes.example", "thamesreport.example", "britwire.example",
           "northernecho.example"],
    "IN": ["bharatchronicle.example", "subcontinentdaily.example",
           "gangesnews.example", "deccanledger.example"],
    "FR": ["hexagonepresse.example", "lemondistinct.example",
           "gauloiswire.example"],
    "BR": ["brasiljornal.example", "amazoniapost.example",
           "tropicaltimes.example"],
}
# Approximate primary language per country (for the cross-language framing
# comparison in Phase 3). Defaults to English if not listed.
_LANG = {
    "US": "English", "UK": "English", "CA": "English", "AS": "English",
    "IN": "English", "SF": "English", "NI": "English",
    "FR": "French", "BR": "Portuguese", "GM": "German", "IT": "Italian",
    "SP": "Spanish", "MX": "Spanish", "AR": "Spanish", "NL": "Dutch",
    "PL": "Polish", "RS": "Russian", "UP": "Ukrainian", "TU": "Turkish",
    "CH": "Chinese", "JA": "Japanese", "KS": "Korean", "ID": "Indonesian",
    "IS": "Hebrew", "SA": "Arabic", "EG": "Arabic",
}


def _outlets_for(country: str) -> list[str]:
    """Return a pool of fake outlet domains for any country code."""
    if country in _OUTLETS:
        return _OUTLETS[country]
    cc = country.lower()
    return [f"dailyledger-{cc}.example", f"nationalpost-{cc}.example",
            f"heraldwire-{cc}.example", f"eveningchronicle-{cc}.example"]


# Topic vocabulary per entity, so LDA/NMF topic modeling on synthetic article
# titles surfaces coherent, distinguishable themes (otherwise every title is
# identical and topic modeling is meaningless). Real GDELT titles supply this
# naturally. Themes use their own subject words; figures/parties share a
# general political pool. Near an injected tone shock, "shock words" are mixed
# in so the spike week is topically distinguishable from normal weeks.
_TOPIC_WORDS = {
    "inflation":     ["prices", "interest", "rates", "groceries", "wages", "costofliving", "centralbank"],
    "immigration":   ["border", "asylum", "migrants", "visa", "refugees", "deportation"],
    "climate_policy":["emissions", "netzero", "renewables", "carbon", "warming", "energy"],
    "unemployment":  ["jobs", "layoffs", "labour", "hiring", "recession", "workforce"],
    "healthcare":    ["hospitals", "insurance", "patients", "doctors", "funding", "clinics"],
    "corruption":    ["bribery", "fraud", "probe", "graft", "kickbacks", "tribunal"],
}
_FIGURE_WORDS = ["campaign", "election", "poll", "speech", "policy", "approval",
                 "rally", "coalition", "summit", "reform", "cabinet", "debate"]
_SHOCK_WORDS = ["crisis", "controversy", "scandal", "backlash", "protest",
                "resignation", "investigation", "outrage"]


def _make_title(rng, entity_id: str, entity_name: str, near_shock: bool) -> str:
    base = _TOPIC_WORDS.get(entity_id, _FIGURE_WORDS)
    k = int(rng.integers(2, 4))
    words = list(rng.choice(base, size=min(k, len(base)), replace=False))
    if near_shock:
        words += list(rng.choice(_SHOCK_WORDS, size=2, replace=False))
    rng.shuffle(words)
    return f"{entity_name}: {' '.join(words)}"


@dataclass
class SyntheticArticle:
    url: str
    title: str
    domain: str
    language: str
    country: str
    seen_date: str
    tone: Optional[float]


def _seed(entity_id: str, country: str) -> int:
    h = hashlib.sha256(f"{entity_id}|{country}".encode()).hexdigest()
    return int(h[:8], 16)


def fetch_articles(entity_id: str, entity_name: str, country: str,
                   start: date, end: date, *,
                   home_country: Optional[str] = None) -> list[SyntheticArticle]:
    """Fabricate per-article records for one entity x country x window."""
    rng = np.random.default_rng(_seed(entity_id, country))
    outlets = _outlets_for(country)
    language = _LANG.get(country, "English")

    n_days = (end - start).days + 1
    is_home = (home_country is not None and home_country == country)

    # --- tone process --------------------------------------------------
    base_tone = rng.uniform(-6, 6)                       # per-series baseline
    # Foreign coverage skews a touch more critical than domestic — gives the
    # domestic-vs-foreign framing comparison (Phase 3) something real to show.
    base_tone += 1.5 if is_home else -1.5
    trend = rng.uniform(-0.03, 0.03)                     # slow drift / day
    season_amp = rng.uniform(0.5, 2.0)

    # One injected event shock (spike or dip) that decays over ~10 days.
    shock_day = int(rng.integers(int(n_days * 0.2), int(n_days * 0.8) + 1))
    shock_mag = rng.uniform(-9, 9)

    # --- volume process ------------------------------------------------
    base_vol = 6.0 if is_home else 2.0
    base_vol += 1.5                                       # every series gets some

    articles: list[SyntheticArticle] = []
    for i in range(n_days):
        day = start + timedelta(days=i)
        # daily mean tone
        mean = (base_tone + trend * i
                + season_amp * np.sin(2 * np.pi * i / 7.0))
        decay = max(0.0, 1.0 - abs(i - shock_day) / 10.0)
        mean += shock_mag * decay
        # daily article count (weekdays busier than weekends)
        weekday_factor = 0.6 if day.weekday() >= 5 else 1.0
        lam = max(0.2, base_vol * weekday_factor)
        count = int(rng.poisson(lam))
        near_shock = decay > 0.3
        for j in range(count):
            tone = float(np.clip(rng.normal(mean, 3.0), -100, 100))
            domain = outlets[rng.integers(0, len(outlets))]
            articles.append(SyntheticArticle(
                url=f"https://{domain}/{entity_id}/{day.isoformat()}/{j}",
                title=_make_title(rng, entity_id, entity_name, near_shock),
                domain=domain,
                language=language,
                country=country,
                seen_date=day.isoformat(),
                tone=round(tone, 3),
            ))
    return articles
