"""API Router for Custom User Watchlists & Threshold Trigger Alert Center."""
from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Query, Body
from src.analytics.alerts_engine import list_all_watchlists, evaluate_watchlist, get_global_unread_alerts


router = APIRouter(prefix="/api/watchlists", tags=["watchlists"])


@router.get("", response_model=list[dict[str, Any]])
def get_watchlists() -> list[dict[str, Any]]:
    """Retrieve all preset and active user watchlists with real-time basket metrics."""
    return list_all_watchlists()


@router.get("/alerts", response_model=list[dict[str, Any]])
def get_active_alerts() -> list[dict[str, Any]]:
    """Retrieve all active threshold alert triggers across monitored portfolios."""
    return get_global_unread_alerts()


@router.post("/evaluate", response_model=dict[str, Any])
def evaluate_custom_watchlist(
    watchlist_id: str = Body(..., embed=True),
    topic_ids: list[str] = Body(..., embed=True),
) -> dict[str, Any]:
    """Evaluate a custom user-defined topic portfolio and trigger threshold alerts."""
    return evaluate_watchlist(watchlist_id=watchlist_id, topic_ids=topic_ids)
