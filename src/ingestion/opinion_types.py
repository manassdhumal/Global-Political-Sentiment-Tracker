"""Shared type for public-opinion posts (used by every opinion source)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class OpinionPost:
    entity_id: str
    source: str          # reddit | bluesky | synthetic
    community: str        # subreddit / feed
    lang: str
    text: str
    created_date: str     # UTC ISO YYYY-MM-DD
    author: str           # raw handle (hashed before storage)
    url: str
