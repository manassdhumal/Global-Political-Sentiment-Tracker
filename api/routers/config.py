"""Config endpoints — the watchlist the frontend needs to build its controls."""
from __future__ import annotations

from fastapi import APIRouter

from api import deps

router = APIRouter(prefix="/api", tags=["config"])


@router.get("/config")
def get_config() -> dict:
    """Watchlist entities + countries + data-window metadata for the UI."""
    wl = deps.get_watchlist()
    scores = deps.get_scores()
    w0, w1 = deps.weeks_range(scores)
    return {
        "measures": "media_and_social_sentiment",  # NOT public opinion
        "tone_range": [-100, 100],
        "synthetic": deps.synthetic_count() > 0,
        "window": {"start": w0, "end": w1},
        "weeks": sorted(scores["week_start"].dt.strftime("%Y-%m-%d").unique().tolist())
                 if not scores.empty else [],
        "countries": [
            {"gdelt": c.gdelt, "iso3": c.iso3, "name": c.name}
            for c in wl.countries
        ],
        "entities": [
            {"id": e.id, "name": e.name, "type": e.type,
             "home_country": e.home_country, "aliases": e.aliases}
            for e in wl.entities
        ],
    }


@router.get("/events")
def get_events() -> list[dict]:
    return [
        {"date": e.date, "scope_type": e.scope_type,
         "scope_id": e.scope_id, "label": e.label}
        for e in deps.get_events()
    ]
