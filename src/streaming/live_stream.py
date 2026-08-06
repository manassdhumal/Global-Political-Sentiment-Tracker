"""Live Breaking News Sentiment Stream Generator (SSE / Event Ticker)."""
from __future__ import annotations

import asyncio
import json
from typing import AsyncGenerator, Any
from datetime import datetime, timezone
import numpy as np

LIVE_BREAKING_EVENTS = [
    {"topic": "Inflation & Rates", "outlet": "Reuters", "headline": "Central bank signals persistent rate plateau amid sticky services inflation.", "tone": -1.8, "velocity": "+18% vol"},
    {"topic": "Donald Trump", "outlet": "WSJ", "headline": "Trade tariff proposals spur cross-border manufacturing supply chain re-evaluations.", "tone": -0.6, "velocity": "+45% vol"},
    {"topic": "Defense Spending", "outlet": "Financial Times", "headline": "European defense procurement pact clears parliamentary budget review.", "tone": +2.4, "velocity": "+22% vol"},
    {"topic": "US-China Trade", "outlet": "Bloomberg", "headline": "High-level bilateral commerce delegates initiate semiconductor export dialog.", "tone": +1.1, "velocity": "+30% vol"},
    {"topic": "Energy & Oil", "outlet": "Associated Press", "headline": "OPEC+ delegates review voluntary production cuts ahead of quarterly summit.", "tone": -0.4, "velocity": "+12% vol"},
    {"topic": "AI Regulation", "outlet": "The Guardian", "headline": "Global tech consortium adopts unified watermarking standard for synthetic media.", "tone": +3.1, "velocity": "+15% vol"},
    {"topic": "Housing Crisis", "outlet": "BBC News", "headline": "Metropolitan zoning deregulation passes initial municipal council vote.", "tone": +1.7, "velocity": "+20% vol"},
]


def generate_live_tick() -> dict[str, Any]:
    """Generate a single live news pulse tick with realistic sentiment variation."""
    idx = int(np.random.randint(0, len(LIVE_BREAKING_EVENTS)))
    ev = LIVE_BREAKING_EVENTS[idx]
    jitter = round(float(np.random.normal(0, 0.2)), 2)

    return {
        "timestamp": datetime.now(timezone.utc).strftime("%H:%M:%S UTC"),
        "topic": ev["topic"],
        "outlet": ev["outlet"],
        "headline": ev["headline"],
        "tone": round(ev["tone"] + jitter, 2),
        "velocity": ev["velocity"],
        "active_monitors": 142,
    }


async def live_event_generator() -> AsyncGenerator[str, None]:
    """Asynchronously yield Server-Sent Events (SSE) pulses."""
    while True:
        tick = generate_live_tick()
        data_json = json.dumps(tick)
        yield f"event: pulse\ndata: {data_json}\n\n"
        await asyncio.sleep(3.5)
