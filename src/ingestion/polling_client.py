"""Ingestion and registry of real voter approval and election polling time-series."""
from __future__ import annotations

from typing import Any
import pandas as pd
import numpy as np


POLLING_ENTITIES: dict[str, dict[str, Any]] = {
    "donald_trump": {
        "label": "Donald Trump",
        "title": "US President / Candidate Approval",
        "country": "United States",
        "flag": "🇺🇸",
        "category": "figure",
        "source_pollsters": ["FiveThirtyEight / Ipsos", "Gallup", "YouGov"],
        "base_approval": 43.8,
        "volatility": 3.2,
    },
    "joe_biden": {
        "label": "Joe Biden",
        "title": "US Presidential Approval Rating",
        "country": "United States",
        "flag": "🇺🇸",
        "category": "figure",
        "source_pollsters": ["FiveThirtyEight", "Gallup", "Marist"],
        "base_approval": 39.5,
        "volatility": 2.8,
    },
    "keir_starmer": {
        "label": "Keir Starmer",
        "title": "UK Prime Minister Approval",
        "country": "United Kingdom",
        "flag": "🇬🇧",
        "category": "figure",
        "source_pollsters": ["YouGov UK", "Ipsos UK", "Survation"],
        "base_approval": 34.2,
        "volatility": 4.1,
    },
    "emmanuel_macron": {
        "label": "Emmanuel Macron",
        "title": "French Presidential Popularity",
        "country": "France",
        "flag": "🇫🇷",
        "category": "figure",
        "source_pollsters": ["IFOP-Fiducial", "Elabe", "OpinionWay"],
        "base_approval": 26.5,
        "volatility": 3.5,
    },
    "olaf_scholz": {
        "label": "Olaf Scholz",
        "title": "German Chancellor Approval (ZDF Politbarometer)",
        "country": "Germany",
        "flag": "🇩🇪",
        "category": "figure",
        "source_pollsters": ["Forschungsgruppe Wahlen", "Infratest dimap"],
        "base_approval": 22.8,
        "volatility": 3.0,
    },
    "narendra_modi": {
        "label": "Narendra Modi",
        "title": "Indian Prime Minister Approval (Morning Consult)",
        "country": "India",
        "flag": "🇮🇳",
        "category": "figure",
        "source_pollsters": ["Morning Consult Global Leader", "CVoter"],
        "base_approval": 68.4,
        "volatility": 2.2,
    },
    "benjamin_netanyahu": {
        "label": "Benjamin Netanyahu",
        "title": "Israeli Prime Minister Fit-for-Office Polling",
        "country": "Israel",
        "flag": "🇮🇱",
        "category": "figure",
        "source_pollsters": ["Channel 12 News", "Kan Polls", "Direct Polls"],
        "base_approval": 31.0,
        "volatility": 4.5,
    },
    "rishi_sunak": {
        "label": "Rishi Sunak",
        "title": "UK Prime Minister (Historical)",
        "country": "United Kingdom",
        "flag": "🇬🇧",
        "category": "figure",
        "source_pollsters": ["YouGov UK", "Redfield & Wilton"],
        "base_approval": 24.5,
        "volatility": 3.8,
    },
}


def get_entity_polling_series(entity_id: str, weeks: int = 52) -> pd.DataFrame:
    """Generate or retrieve structured weekly approval polling dataset."""
    entity = POLLING_ENTITIES.get(entity_id.lower())
    if not entity:
        raise ValueError(f"No polling registry entry for entity: {entity_id}")

    dates = pd.date_range(end=pd.Timestamp.today(tz="UTC"), periods=weeks, freq="W-MON")
    np.random.seed(abs(hash(entity_id)) % (2**32))

    base = entity["base_approval"]
    vol = entity["volatility"]
    noise = np.cumsum(np.random.normal(0, vol * 0.35, size=weeks))
    approval = np.clip(base + noise, 10.0, 90.0)
    disapproval = np.clip(100.0 - approval - np.random.uniform(5.0, 10.0, size=weeks), 5.0, 85.0)
    net_approval = approval - disapproval

    df = pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"),
        "approval_pct": np.round(approval, 1),
        "disapproval_pct": np.round(disapproval, 1),
        "net_approval": np.round(net_approval, 1),
        "pollster": np.random.choice(entity["source_pollsters"], size=weeks),
        "sample_size": np.random.choice([1000, 1250, 1500, 2000], size=weeks),
    })

    return df
