"""API Router for Autonomous AI Geopolitical Analyst."""
from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Query
from src.analytics.analyst_agent import generate_analyst_dossier


router = APIRouter(prefix="/api/analyst", tags=["analyst"])


@router.get("/dossier", response_model=dict[str, Any])
def get_analyst_dossier(
    topic: str = Query("inflation", description="Political topic identifier"),
) -> dict[str, Any]:
    """Generate an institutional-grade intelligence dossier with causal reasoning & forward scenarios."""
    return generate_analyst_dossier(topic_id=topic)
