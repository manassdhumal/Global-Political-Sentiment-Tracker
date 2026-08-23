"""API Router for Autonomous AI Geopolitical Analyst & Interactive Q&A."""
from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field

from src.analytics.analyst_agent import (
    generate_analyst_dossier,
    answer_analyst_question,
    generate_weekly_digest,
)


router = APIRouter(prefix="/api/analyst", tags=["analyst"])

VALID_ARCHETYPES = {"executive", "hedge_fund", "diplomatic", "press"}


class AnalystQARequest(BaseModel):
    topic: str = Field("inflation", description="Topic identifier")
    question: str = Field(..., description="Intelligence query for the analyst")
    archetype: str = Field("executive", description="Analyst archetype: executive, hedge_fund, diplomatic, press")


class DigestRequest(BaseModel):
    watchlist_id: str = Field(..., description="Watchlist identifier (used as label in narrative)")
    topic_ids: list[str] = Field(..., description="List of topic IDs to include in the digest")


@router.get("/dossier", response_model=dict[str, Any])
def get_analyst_dossier(
    topic: str = Query("inflation", description="Political topic identifier"),
    archetype: str = Query("executive", description="Analyst archetype: executive, hedge_fund, diplomatic, press"),
) -> dict[str, Any]:
    """Generate an institutional-grade intelligence dossier tailored by archetype."""
    if archetype not in VALID_ARCHETYPES:
        raise HTTPException(status_code=400, detail=f"Invalid archetype '{archetype}'. Valid: {sorted(VALID_ARCHETYPES)}")
    return generate_analyst_dossier(topic_id=topic, archetype=archetype)


@router.post("/qa", response_model=dict[str, Any])
def ask_analyst_question(request: AnalystQARequest) -> dict[str, Any]:
    """Ask follow-up intelligence questions and receive contextual answers with key takeaways."""
    if request.archetype not in VALID_ARCHETYPES:
        raise HTTPException(status_code=400, detail=f"Invalid archetype '{request.archetype}'. Valid: {sorted(VALID_ARCHETYPES)}")
    return answer_analyst_question(
        topic_id=request.topic,
        question=request.question,
        archetype=request.archetype,
    )


@router.post("/digest", response_model=dict[str, Any])
def get_weekly_digest(request: DigestRequest) -> dict[str, Any]:
    """Generate a multi-topic weekly executive digest across a watchlist portfolio."""
    if not request.topic_ids:
        raise HTTPException(status_code=400, detail="topic_ids must be a non-empty list.")
    return generate_weekly_digest(
        watchlist_id=request.watchlist_id,
        topic_ids=request.topic_ids,
    )
