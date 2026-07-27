"""v3 topic endpoints — trending, browse catalog, and on-demand topic analysis."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from src.topics import analyze_topic, trending, global_snapshot
from src.topics.catalog import categories, load_catalog
from src.topics.trending import catalog_stats
from src.topics.cache import read_trending

router = APIRouter(prefix="/api", tags=["topics"])


@router.get("/trending")
def get_trending(top_n: int = Query(12, ge=1, le=40),
                 max_age_hours: float = Query(12.0, ge=0)) -> dict:
    """Global snapshot + most trending topics (volume + movement).

    Serves a precomputed snapshot (scripts/precompute_trending.py) when fresh —
    which lets trending use real/live data without paying the cost per request.
    Falls back to computing on the fly (synthetic).
    """
    cached = read_trending(max_age_hours=max_age_hours)
    if cached and cached.get("trending"):
        return {"snapshot": cached["snapshot"],
                "trending": cached["trending"][:top_n],
                "cached": True, "computed_at": cached.get("computed_at"),
                "source": cached.get("source", "synthetic")}
    return {"snapshot": global_snapshot(), "trending": trending(top_n=top_n),
            "cached": False, "source": "synthetic"}


@router.get("/topics")
def get_topics() -> dict:
    """The full browsable catalog with quick stats + trending scores."""
    return {
        "categories": categories(),
        "count": len(load_catalog()),
        "topics": catalog_stats(),
    }


@router.get("/topic")
def get_topic(q: str = Query(..., min_length=1, max_length=120),
              source: str | None = Query(None, pattern="^(auto|live|gdelt|synthetic)$")) -> dict:
    """Full on-demand analysis for ANY topic (catalog slug or free text).

    source: 'synthetic' (default here) | 'auto'/'live' (try GDELT + social,
    fall back to synthetic per-piece). Also set GPST_TOPIC_SOURCE to change the
    default on a live-capable machine.
    """
    try:
        return analyze_topic(q, source=source)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
