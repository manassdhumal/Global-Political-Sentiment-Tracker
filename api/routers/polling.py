from __future__ import annotations

from fastapi import APIRouter, Query, HTTPException
from typing import Any

from src.analytics.polling import compare_polling_vs_sentiment, POLLING_ENTITIES

router = APIRouter(prefix="/api/polling", tags=["polling"])


@router.get("/entities")
def get_polling_entities() -> list[dict[str, Any]]:
    """Return all global political figures with tracked approval polling series."""
    return [
        {"id": k, **v} for k, v in POLLING_ENTITIES.items()
    ]


@router.get("/comparison")
def get_polling_comparison(
    entity: str = Query("donald_trump", description="Political figure ID (e.g. donald_trump, keir_starmer, olaf_scholz)"),
    weeks: int = Query(26, ge=4, le=104, description="Historical horizon in weeks"),
) -> dict[str, Any]:
    """Return synchronized voter approval ratings vs press media tone and bias analytics."""
    try:
        return compare_polling_vs_sentiment(entity_id=entity, weeks=weeks)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
