"""API Router for Applied Econometric Time-Series Suite."""
from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Query
from src.analytics.timeseries import analyze_econometric_timeseries, analyze_multi_topic_overlay


router = APIRouter(prefix="/api/timeseries", tags=["timeseries"])


@router.get("/analysis", response_model=dict[str, Any])
def get_timeseries_analysis(
    topic: str = Query("inflation", description="Topic identifier or keyword"),
    smoothness: float = Query(1600.0, description="HP filter lambda parameter"),
) -> dict[str, Any]:
    """Retrieve econometric HP filter decomposition, ADF stationarity, structural breaks, and volatility."""
    return analyze_econometric_timeseries(topic_id=topic, lamb=smoothness)


@router.get("/multi-overlay", response_model=dict[str, Any])
def get_multi_topic_overlay(
    topics: str = Query("inflation,interest_rates,energy_crisis", description="Comma-separated topic identifiers"),
    smoothness: float = Query(1600.0, description="HP filter lambda parameter"),
) -> dict[str, Any]:
    """Retrieve aligned multi-topic econometric overlay with HP trends, cycles, and cross-correlations."""
    topic_list = [t.strip() for t in topics.split(",") if t.strip()]
    return analyze_multi_topic_overlay(topic_ids=topic_list, lamb=smoothness)
