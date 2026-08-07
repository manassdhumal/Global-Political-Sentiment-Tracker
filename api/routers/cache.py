"""API Router for In-Memory Caching Observability and Invalidation."""
from __future__ import annotations

from typing import Any
from fastapi import APIRouter
from src.cache import GLOBAL_CACHE

router = APIRouter(prefix="/api/cache", tags=["cache"])


@router.get("/stats", response_model=dict[str, Any])
def get_cache_stats() -> dict[str, Any]:
    """Retrieve runtime in-memory cache hit rate, active keys, and eviction statistics."""
    return GLOBAL_CACHE.stats()


@router.post("/flush", response_model=dict[str, Any])
def flush_cache() -> dict[str, Any]:
    """Manually invalidate all active cache entries."""
    cleared = GLOBAL_CACHE.invalidate()
    return {"status": "ok", "cleared_entries": cleared}
