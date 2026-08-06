"""API Router for Live Breaking Sentiment SSE Stream."""
from __future__ import annotations

from typing import Any
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from src.streaming.live_stream import live_event_generator, generate_live_tick


router = APIRouter(prefix="/api/live", tags=["live"])


@router.get("/stream")
async def stream_live_events() -> StreamingResponse:
    """Stream real-time breaking news sentiment pulses via Server-Sent Events (SSE)."""
    return StreamingResponse(
        live_event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/latest", response_model=dict[str, Any])
def get_latest_live_pulse() -> dict[str, Any]:
    """Retrieve the most recent live sentiment snapshot without streaming."""
    return generate_live_tick()
