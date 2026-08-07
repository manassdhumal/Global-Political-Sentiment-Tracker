from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Query
from src.analytics.geography import get_world_sentiment_map, COUNTRY_REGISTRY
from src.analytics.geopolitics_map import get_geopolitical_map_layers

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


@router.get("/layers", response_model=dict[str, Any])
def get_map_overlays() -> dict[str, Any]:
    """Return strategic maritime chokepoints, conflict flashpoints, and upcoming elections."""
    return get_geopolitical_map_layers()
