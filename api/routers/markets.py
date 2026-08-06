"""API Router for Cross-Asset Financial Spillover & Market Contagion."""
from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Query
from src.analytics.markets import analyze_market_spillover, get_all_assets_summary, GLOBAL_ASSET_REGISTRY


router = APIRouter(prefix="/api/markets", tags=["markets"])


@router.get("/assets", response_model=list[dict[str, Any]])
def get_assets() -> list[dict[str, Any]]:
    """Get registry of tracked global macroeconomic and financial assets."""
    return get_all_assets_summary()


@router.get("/spillover", response_model=dict[str, Any])
def get_market_spillover(
    topic: str = Query("inflation", description="Political topic / event slug"),
    asset: str = Query("brent_oil", description="Asset identifier (e.g., brent_oil, gold, eur_usd)"),
    weeks: int = Query(52, description="Number of weeks to analyze"),
) -> dict[str, Any]:
    """Analyze cross-asset market spillover, Granger causality, and elasticity beta."""
    return analyze_market_spillover(topic_id=topic, asset_id=asset, weeks=weeks)
