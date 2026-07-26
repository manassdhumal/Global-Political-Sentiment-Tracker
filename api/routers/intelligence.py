"""Intelligence endpoints — forecast, anomalies, topics, event impact, framing."""
from __future__ import annotations

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from api import deps
from src import storage
from src.config import DEFAULT_DB_PATH
from src.analytics import (weekly_weighted_series, forecast_tone,
                           detect_anomalies, biggest_spike_week, extract_topics,
                           event_impact, domestic_vs_foreign, by_language)

router = APIRouter(prefix="/api", tags=["intelligence"])


def _entity_series(entity: str, country: str | None) -> pd.DataFrame:
    scores = deps.get_scores()
    ent = scores[scores["entity_id"] == entity] if not scores.empty else scores
    if country and country != "__all__":
        ent = ent[ent["country"] == country]
    return weekly_weighted_series(ent)


@router.get("/forecast")
def forecast(entity: str, country: str | None = None,
             periods: int = Query(4, ge=1, le=12)) -> dict:
    hist = _entity_series(entity, country)
    if hist.empty:
        raise HTTPException(404, "No data for this selection.")
    fc = forecast_tone(hist, periods=periods)
    return {
        "entity": entity, "country": country or "__all__",
        "method": fc.method, "note": fc.note,
        "history": deps.df_records(fc.history.rename(columns={"tone": "avg_tone"})),
        "forecast": deps.df_records(fc.forecast),
    }


@router.get("/anomalies")
def anomalies(entity: str, country: str | None = None,
              z_thresh: float = Query(3.0, ge=1.0, le=6.0)) -> dict:
    hist = _entity_series(entity, country)
    if hist.empty:
        raise HTTPException(404, "No data for this selection.")
    an = detect_anomalies(hist, z_thresh=z_thresh)
    flagged = an[an["is_anomaly"]]
    return {
        "entity": entity, "country": country or "__all__",
        "series": deps.df_records(an),
        "flagged": deps.df_records(flagged),
    }


@router.get("/spike-topics")
def spike_topics(entity: str, country: str | None = None,
                 n_topics: int = Query(3, ge=1, le=6)) -> dict:
    hist = _entity_series(entity, country)
    if hist.empty:
        raise HTTPException(404, "No data for this selection.")
    spike = biggest_spike_week(hist)
    if spike is None:
        return {"entity": entity, "spike_week": None, "topics": []}
    w0 = (spike - pd.Timedelta(weeks=1)).strftime("%Y-%m-%d")
    w1 = (spike + pd.Timedelta(weeks=1)).strftime("%Y-%m-%d")
    conn = storage.connect(DEFAULT_DB_PATH)
    try:
        titles = storage.read_titles(
            conn, entity, w0, w1,
            country=None if not country or country == "__all__" else country)
    finally:
        conn.close()
    wl = deps.get_watchlist()
    ent = wl.entity_by_id(entity)
    stop = list((ent.name.split() if ent else []) + (ent.aliases if ent else []))
    tops = extract_topics(titles, n_topics=n_topics, extra_stopwords=stop)
    return {
        "entity": entity, "spike_week": spike.strftime("%Y-%m-%d"),
        "n_titles": len(titles),
        "topics": [{"words": t.words, "weight": t.weight} for t in tops],
    }


@router.get("/event-impact")
def impact(entity: str, event_date: str, country: str | None = None,
           window_weeks: int = Query(3, ge=1, le=8)) -> dict:
    scores = deps.get_scores()
    ent = scores[scores["entity_id"] == entity] if not scores.empty else scores
    if country and country != "__all__":
        ent = ent[ent["country"] == country]
    hist = weekly_weighted_series(ent)
    if hist.empty:
        raise HTTPException(404, "No data for this selection.")
    res = event_impact(hist, event_date, window_weeks=window_weeks)
    return {
        "entity": entity, "country": country or "__all__",
        "event_date": event_date,
        "before_tone": res.before_tone, "after_tone": res.after_tone,
        "delta": res.delta, "n_before": res.n_before, "n_after": res.n_after,
        "vol_before": res.vol_before, "vol_after": res.vol_after,
        "p_value": res.p_value, "note": res.note,
    }


@router.get("/framing")
def framing(entity: str, w0: str | None = None, w1: str | None = None) -> dict:
    wl = deps.get_watchlist()
    scores = deps.get_scores()
    ent = scores[scores["entity_id"] == entity] if not scores.empty else scores
    if ent.empty:
        raise HTTPException(404, f"No data for entity '{entity}'.")
    if w0:
        ent = ent[ent["week_start"].dt.date >= pd.to_datetime(w0).date()]
    if w1:
        ent = ent[ent["week_start"].dt.date <= pd.to_datetime(w1).date()]
    e = wl.entity_by_id(entity)
    home = e.home_country if e else None
    dvf = domestic_vs_foreign(ent, home)

    conn = storage.connect(DEFAULT_DB_PATH)
    try:
        lang = by_language(storage.read_language_summary(
            conn, entity, w0, w1))
    finally:
        conn.close()
    return {
        "entity": entity, "home_country": home,
        "domestic_vs_foreign": dvf,
        "by_language": deps.df_records(lang),
    }
