"""API Router for Autonomous AI Geopolitical Analyst & Interactive Q&A."""
from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from src.analytics.analyst_agent import generate_analyst_dossier, answer_analyst_question


router = APIRouter(prefix="/api/analyst", tags=["analyst"])


class AnalystQARequest(BaseModel):
    topic: str = Field("inflation", description="Topic identifier")
    question: str = Field(..., description="Intelligence query for the analyst")
    archetype: str = Field("executive", description="Analyst archetype: executive, hedge_fund, diplomatic")


@router.get("/dossier", response_model=dict[str, Any])
def get_analyst_dossier(
    topic: str = Query("inflation", description="Political topic identifier"),
    archetype: str = Query("executive", description="Analyst archetype: executive, hedge_fund, diplomatic"),
) -> dict[str, Any]:
    """Generate an institutional-grade intelligence dossier tailored by archetype."""
    return generate_analyst_dossier(topic_id=topic, archetype=archetype)


@router.post("/qa", response_model=dict[str, Any])
def ask_analyst_question(request: AnalystQARequest) -> dict[str, Any]:
    """Ask follow-up intelligence questions and receive contextual answers with key takeaways."""
    return answer_analyst_question(
        topic_id=request.topic,
        question=request.question,
        archetype=request.archetype,
    )
