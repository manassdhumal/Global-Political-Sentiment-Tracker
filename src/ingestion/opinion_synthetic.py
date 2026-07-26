"""Synthetic public-opinion source — deterministic offline fallback.

Mirrors the role of synthetic.py for the media pipeline: when Reddit/Bluesky
credentials or network are unavailable, this fabricates realistic opinion
POSTS behind the same interface. Crucially it produces sentiment-laden TEXT
(not a pre-baked score) so the real sentiment MODEL actually scores it — the
same code path used on live posts.

Weekly positive/negative mix follows a deterministic lean (+ an injected
shock) so the model-scored weekly averages show real, detectable structure.

!!! FABRICATED DATA — tagged source='synthetic', never presented as real. !!!
"""
from __future__ import annotations

import hashlib
from datetime import date, timedelta

import numpy as np

from .opinion_types import OpinionPost

_POS = ["support", "admire", "praise", "back", "trust", "applaud", "welcome"]
_POS_ADJ = ["excellent", "impressive", "encouraging", "strong", "fair", "hopeful"]
_NEG = ["oppose", "distrust", "condemn", "criticize", "reject", "slam"]
_NEG_ADJ = ["terrible", "disappointing", "corrupt", "reckless", "dishonest", "weak"]
_TOPICS = {
    "inflation": ["prices", "the cost of living", "interest rates", "wages"],
    "immigration": ["the border", "asylum policy", "migration"],
    "climate_policy": ["net zero", "emissions targets", "energy policy"],
    "unemployment": ["jobs", "the labour market", "layoffs"],
    "healthcare": ["the health system", "hospital funding", "patient care"],
    "corruption": ["the scandal", "the investigation", "accountability"],
}
_GENERIC_TOPIC = ["their record", "the latest policy", "the campaign", "the speech"]
_COMMUNITIES = ["r/worldnews", "r/politics", "r/geopolitics",
                "bsky/politics", "bsky/news"]


def _seed(entity_id: str) -> int:
    return int(hashlib.sha256(f"opinion|{entity_id}".encode()).hexdigest()[:8], 16)


def fetch_posts(entity_id: str, entity_name: str, start: date, end: date, *,
                per_day: float = 2.5) -> list[OpinionPost]:
    """Fabricate opinion posts for one entity across the window."""
    rng = np.random.default_rng(_seed(entity_id))
    topics = _TOPICS.get(entity_id, _GENERIC_TOPIC)
    n_days = (end - start).days + 1

    # weekly positive-probability lean: baseline + seasonality + one shock
    base_p = rng.uniform(0.35, 0.6)
    shock_day = int(rng.integers(int(n_days * 0.2), int(n_days * 0.8) + 1))
    shock_mag = rng.uniform(-0.3, 0.3)

    posts: list[OpinionPost] = []
    for i in range(n_days):
        day = start + timedelta(days=i)
        decay = max(0.0, 1.0 - abs(i - shock_day) / 10.0)
        p_pos = float(np.clip(base_p + 0.1 * np.sin(2 * np.pi * i / 14.0)
                              + shock_mag * decay, 0.05, 0.95))
        count = int(rng.poisson(max(0.3, per_day)))
        for _ in range(count):
            r = rng.random()
            topic = topics[rng.integers(0, len(topics))]
            if r < p_pos:
                text = (f"I {rng.choice(_POS)} {entity_name} — {rng.choice(_POS_ADJ)} "
                        f"handling of {topic}.")
            elif r < p_pos + (1 - p_pos) * 0.75:
                text = (f"I {rng.choice(_NEG)} {entity_name}. {rng.choice(_NEG_ADJ).capitalize()} "
                        f"approach to {topic}.")
            else:
                text = f"Some discussion about {entity_name} and {topic} today."
            community = _COMMUNITIES[rng.integers(0, len(_COMMUNITIES))]
            author = f"user{int(rng.integers(0, 500))}"
            posts.append(OpinionPost(
                entity_id=entity_id, source="synthetic", community=community,
                lang="en", text=text, created_date=day.isoformat(),
                author=author,
                url=f"https://social.example/{entity_id}/{day.isoformat()}/{rng.integers(0,1_000_000)}"))
    return posts
