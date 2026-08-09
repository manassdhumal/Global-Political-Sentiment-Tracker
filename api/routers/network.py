"""API Router for Ideological Network Graph & Contagion Simulation."""
from __future__ import annotations

from fastapi import APIRouter, Query
from typing import Any
from pydantic import BaseModel, Field

from src.analytics.network import build_ideological_network, simulate_contagion_spread


router = APIRouter(prefix="/api/network", tags=["network"])


class ContagionSimRequest(BaseModel):
    seed_topic: str = Field("inflation", description="Seed topic identifier for shock origin")
    shock_magnitude: float = Field(-3.0, description="Magnitude of the sentiment shock (e.g., -3.0 or +2.5)")
    attenuation: float = Field(0.65, ge=0.1, le=0.95, description="Per-hop transmission attenuation factor")
    max_steps: int = Field(3, ge=1, le=5, description="Maximum propagation hop steps")


@router.get("/graph")
def get_network_graph(
    min_correlation: float = Query(0.25, ge=0.05, le=0.90, description="Minimum correlation threshold for connecting edges"),
    max_nodes: int = Query(30, ge=5, le=50, description="Maximum entities to include in the network"),
) -> dict[str, Any]:
    """Return force-directed graph nodes, correlation links, and ideological community clusters."""
    return build_ideological_network(min_correlation=min_correlation, max_nodes=max_nodes)


@router.get("/clusters")
def get_clusters() -> list[dict[str, Any]]:
    """Return all predefined ideological & thematic clusters."""
    return list(CATEGORY_CLUSTERS.values())


@router.post("/simulate-contagion", response_model=dict[str, Any])
def run_contagion_simulation(request: ContagionSimRequest) -> dict[str, Any]:
    """Simulate shock propagation across correlated narrative clusters."""
    return simulate_contagion_spread(
        seed_topic_id=request.seed_topic,
        shock_magnitude=request.shock_magnitude,
        attenuation=request.attenuation,
        max_steps=request.max_steps,
    )
