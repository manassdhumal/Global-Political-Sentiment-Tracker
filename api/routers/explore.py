"""Explore endpoints — time series, world map, comparisons, drill-down, volatility."""
from __future__ import annotations

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from api import deps
from src.analytics import (weekly_weighted_series, country_tone_summary,
                           volatility_index, issue_association)

router = APIRouter(prefix="/api", tags=["explore"])


def _window(df: pd.DataFrame, w0: str | None, w1: str | None) -> pd.DataFrame:
    if df.empty:
        return df
    out = df
    if w0:
        out = out[out["week_start"].dt.date >= pd.to_datetime(w0).date()]
    if w1:
        out = out[out["week_start"].dt.date <= pd.to_datetime(w1).date()]
    return out


def _csv(param: str | None) -> list[str] | None:
    if not param:
        return None
    return [p.strip() for p in param.split(",") if p.strip()]


@router.get("/timeseries")
def timeseries(entity: str, countries: str | None = None,
               w0: str | None = None, w1: str | None = None) -> dict:
    scores = deps.get_scores()
    ent = scores[scores["entity_id"] == entity] if not scores.empty else scores
    if ent.empty:
        raise HTTPException(404, f"No data for entity '{entity}'.")
    sel = _csv(countries) or sorted(ent["country"].unique())
    view = _window(ent[ent["country"].isin(sel)], w0, w1)
    if view.empty:
        raise HTTPException(404, "No data for the selected countries/window.")

    aggregate = deps.df_records(weekly_weighted_series(view))
    by_country = {
        c: deps.df_records(cdf.sort_values("week_start")[
            ["week_start", "avg_tone", "article_volume",
             "source_diversity", "low_confidence"]])
        for c in sel
        if not (cdf := view[view["country"] == c]).empty
    }
    return {
        "entity": entity,
        "countries": sel,
        "aggregate": aggregate,
        "by_country": by_country,
        "total_articles": int(view["article_volume"].sum()),
        "max_source_diversity": int(view["source_diversity"].max()),
        "low_confidence_weeks": int(view["low_confidence"].sum()),
    }


@router.get("/map")
def world_map(entity: str = "__all__", w0: str | None = None,
              w1: str | None = None) -> dict:
    wl = deps.get_watchlist()
    scores = deps.get_scores()
    if scores.empty:
        raise HTTPException(404, "No data.")
    view = _window(scores, w0, w1)
    if entity != "__all__":
        view = view[view["entity_id"] == entity]
    if view.empty:
        raise HTTPException(404, "No data for the selection.")
    summary = country_tone_summary(view)
    summary["iso3"] = summary["country"].map(wl.iso3_by_gdelt)
    summary["country_name"] = summary["country"].map(wl.name_by_gdelt)
    glob = float((view["avg_tone"] * view["article_volume"]).sum()
                 / max(view["article_volume"].sum(), 1))
    return {"entity": entity, "global_tone": round(glob, 2),
            "countries": deps.df_records(summary)}


@router.get("/entity-compare")
def entity_compare(entities: str, country: str | None = None,
                   w0: str | None = None, w1: str | None = None) -> dict:
    scores = deps.get_scores()
    ids = _csv(entities) or []
    if not ids:
        raise HTTPException(400, "Provide at least one entity id.")
    base = _window(scores, w0, w1)
    if country:
        base = base[base["country"] == country]
    series = {}
    for eid in ids:
        edf = base[base["entity_id"] == eid]
        if not edf.empty:
            series[eid] = deps.df_records(weekly_weighted_series(edf))
    return {"entities": ids, "country": country or "__all__", "series": series}


@router.get("/issue-drilldown")
def issue_drilldown(theme: str, w0: str | None = None, w1: str | None = None,
                    top_n: int = Query(12, ge=1, le=100)) -> dict:
    wl = deps.get_watchlist()
    scores = deps.get_scores()
    view = _window(scores[scores["entity_id"] == theme], w0, w1)
    if view.empty:
        raise HTTPException(404, f"No data for theme '{theme}'.")
    summary = issue_association(view)
    summary["country_name"] = summary["country"].map(wl.name_by_gdelt)
    return {
        "theme": theme,
        "total_articles": int(summary["article_volume"].sum()),
        "countries_covering": int(summary["country"].nunique()),
        "ranking": deps.df_records(summary.head(top_n)),
        "all": deps.df_records(summary),
    }


@router.get("/volatility")
def volatility(group: str = "entity", w0: str | None = None,
               w1: str | None = None, min_weeks: int = 4,
               top_n: int = Query(15, ge=1, le=100)) -> dict:
    if group not in {"entity", "country", "entity_country"}:
        raise HTTPException(400, "group must be entity|country|entity_country.")
    wl = deps.get_watchlist()
    view = _window(deps.get_scores(), w0, w1)
    idx = volatility_index(view, group=group, min_weeks=min_weeks)
    if not idx.empty:
        if "entity_id" in idx.columns:
            idx["entity_name"] = idx["entity_id"].map(wl.name_by_entity)
        if "country" in idx.columns:
            idx["country_name"] = idx["country"].map(wl.name_by_gdelt)
    return {"group": group, "ranking": deps.df_records(idx.head(top_n))}
