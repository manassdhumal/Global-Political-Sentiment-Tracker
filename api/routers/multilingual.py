"""API Router for Multi-Lingual Media Ingestion & Cross-Cultural Framing."""
from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Query
from src.analytics.multilingual import analyze_multilingual_framing, LANGUAGE_SPHERES


router = APIRouter(prefix="/api/multilingual", tags=["multilingual"])


@router.get("/spheres", response_model=list[dict[str, Any]])
def get_language_spheres() -> list[dict[str, Any]]:
    """Return all 8 supported language spheres and tracked international outlets."""
    return LANGUAGE_SPHERES


@router.get("/matrix", response_model=dict[str, Any])
def get_multilingual_framing_matrix(
    topic: str = Query("us_china", description="Topic identifier for cross-lingual disparity analysis"),
) -> dict[str, Any]:
    """Compute cross-lingual sentiment disparity and narrative framing matrix for a topic."""
    return analyze_multilingual_framing(topic_id=topic)
