from __future__ import annotations

from fastapi import APIRouter, Query, Body, HTTPException
from pydantic import BaseModel, Field
from typing import Any

from src.analytics.simulator import simulate_policy_shock, EVENT_PRESETS

router = APIRouter(prefix="/api/simulator", tags=["simulator"])


class SimulationRequest(BaseModel):
    topic: str = Field(..., description="Topic slug or identifier (e.g. inflation, donald_trump)")
    event_type: str = Field("rate_hike", description="Shock event type from presets or 'custom'")
    magnitude: float = Field(1.0, ge=0.2, le=3.0, description="Intensity multiplier (0.2x to 3.0x)")
    weeks_ahead: int = Field(6, ge=2, le=12, description="Simulation horizon in weeks")
    custom_description: str | None = Field(None, description="Optional custom scenario text")


@router.get("/presets")
def get_simulation_presets() -> dict[str, Any]:
    """Return all available predefined geopolitical & macroeconomic shock models."""
    return {
        "presets": [
            {"key": k, **v} for k, v in EVENT_PRESETS.items()
        ]
    }


@router.post("/run")
def run_simulation(req: SimulationRequest) -> dict[str, Any]:
    """Run a counterfactual policy shock simulation and return projected trajectory."""
    try:
        return simulate_policy_shock(
            topic_id=req.topic,
            event_type=req.event_type,
            magnitude=req.magnitude,
            weeks_ahead=req.weeks_ahead,
            custom_description=req.custom_description,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
