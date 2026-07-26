"""Public-opinion + media-vs-public endpoints (v2)."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api import deps
from src.analytics import media_vs_public, divergence_summary

router = APIRouter(prefix="/api", tags=["opinion"])


@router.get("/opinion/status")
def status() -> dict:
    ops = deps.get_opinion_scores()
    sources = (sorted(ops[ops["source"] != "all"]["source"].unique().tolist())
               if not ops.empty else [])
    return {"available": deps.opinion_ready(), "sources": sources}


@router.get("/opinion/timeseries")
def opinion_timeseries(entity: str) -> dict:
    ops = deps.get_opinion_scores()
    if ops.empty:
        raise HTTPException(404, "No opinion data. Run run_opinion_pipeline.py.")
    ent = ops[ops["entity_id"] == entity]
    if ent.empty:
        raise HTTPException(404, f"No opinion data for '{entity}'.")
    combined = ent[ent["source"] == "all"].sort_values("week_start")
    by_source = {
        src: deps.df_records(g.sort_values("week_start")[
            ["week_start", "avg_sentiment", "post_volume",
             "unique_authors", "low_confidence"]])
        for src, g in ent[ent["source"] != "all"].groupby("source")
    }
    return {
        "entity": entity,
        "combined": deps.df_records(combined[
            ["week_start", "avg_sentiment", "post_volume",
             "unique_authors", "low_confidence"]]),
        "by_source": by_source,
    }


@router.get("/compare/media-vs-public")
def compare(entity: str) -> dict:
    media = deps.get_scores()
    opinion = deps.get_opinion_scores()
    if media.empty:
        raise HTTPException(404, "No media data.")
    merged = media_vs_public(media, opinion, entity)
    if merged.empty:
        raise HTTPException(404, f"No comparable data for '{entity}'.")
    both = merged.dropna(subset=["media_tone", "public_sentiment"])
    avg_gap = round(float(both["gap"].mean()), 2) if not both.empty else None
    return {
        "entity": entity,
        "series": deps.df_records(merged),
        "avg_media": round(float(both["media_tone"].mean()), 2) if not both.empty else None,
        "avg_public": round(float(both["public_sentiment"].mean()), 2) if not both.empty else None,
        "avg_gap": avg_gap,
    }


@router.get("/compare/divergence")
def divergence() -> dict:
    media = deps.get_scores()
    opinion = deps.get_opinion_scores()
    wl = deps.get_watchlist()
    if opinion.empty:
        return {"available": False, "ranking": []}
    rank = divergence_summary(media, opinion, wl.entity_ids, wl.name_by_entity)
    return {"available": True, "ranking": deps.df_records(rank)}
