"""NLP endpoint — on-demand text analysis (shared src.nlp engine)."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from api import deps
from src.analytics import weekly_weighted_series
from src.nlp import analyze_text
from src.nlp.sentiment import available_backends

router = APIRouter(prefix="/api", tags=["nlp"])


class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=20000)
    backend: str | None = None          # 'vader' | 'transformers' | None(default)
    use_spacy: bool = True
    with_emotion: bool = True


@router.get("/sentiment-backends")
def backends() -> dict:
    return {"available": available_backends()}


@router.post("/analyze-text")
def analyze(req: AnalyzeRequest) -> dict:
    wl = deps.get_watchlist()
    scores = deps.get_scores()
    res = analyze_text(req.text, wl, backend=req.backend,
                       use_spacy=req.use_spacy, with_emotion=req.with_emotion)

    # attach live aggregate trend for each tracked entity
    aspects = []
    for a in res.aspects:
        trend = None
        if a.tracked and a.entity_id and not scores.empty:
            ser = weekly_weighted_series(scores[scores["entity_id"] == a.entity_id])
            if not ser.empty:
                trend = round(float(ser["avg_tone"].iloc[-1]), 2)
        aspects.append({
            "name": a.name, "entity_id": a.entity_id, "tracked": a.tracked,
            "score": a.score, "label": a.label, "mentions": a.mentions,
            "snippet": a.snippet, "current_trend": trend,
            "delta_vs_trend": round(a.score - trend, 2) if trend is not None else None,
        })

    return {
        "backend": res.backend,
        "used_spacy": res.used_spacy,
        "overall_score": res.overall_score,
        "overall_label": res.overall_label,
        "entities": [
            {"name": e.name, "entity_id": e.entity_id, "tracked": e.tracked,
             "type": e.entity_type, "mentions": e.mentions, "spans": e.spans}
            for e in res.entities
        ],
        "aspects": aspects,
        "contributions": [
            {"token": c.token, "start": c.start, "end": c.end, "delta": c.delta}
            for c in res.contributions
        ],
        "top_positive": [{"token": c.token, "delta": c.delta} for c in res.top_positive],
        "top_negative": [{"token": c.token, "delta": c.delta} for c in res.top_negative],
        "emotions": res.emotions,
        "notes": res.notes,
    }
