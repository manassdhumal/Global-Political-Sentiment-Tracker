from __future__ import annotations

from fastapi import APIRouter, Query
from src.analytics.geography import get_world_sentiment_map, COUNTRY_REGISTRY

router = APIRouter(prefix="/api/geography", tags=["geography"])


@router.get("/world-map")
def get_world_map(
    region: str = Query("all", description="Region filter: all, g7, nato, brics, eu, americas, europe, apac, middle_east"),
) -> dict:
    """Return country-level sentiment scores, weekly delta, volume, and hotspot alerts."""
    return get_world_sentiment_map(region=region)


@router.get("/countries")
def list_countries() -> list[dict]:
    """Return list of supported countries in the geographical intelligence registry."""
    return COUNTRY_REGISTRY
