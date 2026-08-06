from __future__ import annotations

from fastapi import APIRouter, Query
from typing import Any

from src.analytics.network import build_ideological_network, CATEGORY_CLUSTERS

router = APIRouter(prefix="/api/network", tags=["network"])


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
