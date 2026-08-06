"""API Router for Media Polarization & Ideological Framing Matrix."""
from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Query
from src.analytics.polarization import analyze_media_polarization, MEDIA_SPECTRUM_REGISTRY


router = APIRouter(prefix="/api/polarization", tags=["polarization"])


@router.get("/analysis", response_model=dict[str, Any])
def get_polarization_analysis(
    topic: str = Query("inflation", description="Political topic slug"),
) -> dict[str, Any]:
    """Retrieve ideological spectrum breakdown, polarization spread timeline, and keyword divergence."""
    return analyze_media_polarization(topic_id=topic)
