"""Misc endpoints — political-mood homepage, search, report export."""
from __future__ import annotations

import pandas as pd
from fastapi import APIRouter, HTTPException, Query, Response

from api import deps
from src.analytics import weekly_weighted_series, detect_anomalies
from src.reporting import build_summary, to_markdown, to_pdf_bytes

router = APIRouter(prefix="/api", tags=["misc"])


@router.get("/mood")
def mood() -> dict:
    wl = deps.get_watchlist()
    scores = deps.get_scores()
    if scores.empty:
        raise HTTPException(404, "No data.")
    latest_week = scores["week_start"].max()
    glob = float((scores["avg_tone"] * scores["article_volume"]).sum()
                 / max(scores["article_volume"].sum(), 1))

    rows = []
    for eid, g in scores.groupby("entity_id"):
        s = weekly_weighted_series(g)
        if s.empty:
            continue
        latest = float(s["avg_tone"].iloc[-1])
        prev = float(s["avg_tone"].iloc[-2]) if len(s) > 1 else latest
        an = detect_anomalies(s, z_thresh=2.5)
        rows.append({
            "entity_id": eid, "name": wl.name_by_entity.get(eid, eid),
            "type": wl.entity_by_id(eid).type if wl.entity_by_id(eid) else "",
            "latest": round(latest, 2), "delta": round(latest - prev, 2),
            "volume": int(g["article_volume"].sum()),
            "anomaly": bool(an["is_anomaly"].iloc[-1]) if not an.empty else False,
        })
    md = pd.DataFrame(rows)
    movers = md[md["delta"].abs() > 0].sort_values("delta", ascending=False)
    return {
        "global_tone": round(glob, 2),
        "total_articles": int(scores["article_volume"].sum()),
        "n_entities": int(scores["entity_id"].nunique()),
        "n_countries": int(scores["country"].nunique()),
        "latest_week": latest_week.strftime("%Y-%m-%d"),
        "improving": deps.df_records(movers.head(5)),
        "worsening": deps.df_records(movers.sort_values("delta").head(5)),
        "ranking": deps.df_records(md.sort_values("latest")),
        "alerts": deps.df_records(md[md["anomaly"]].sort_values("delta")),
    }


@router.get("/search")
def search(q: str = "") -> dict:
    wl = deps.get_watchlist()
    scores = deps.get_scores()
    q = q.strip().lower()
    results = []
    for e in wl.entities:
        hay = " ".join([e.id, e.name, e.type] + list(e.aliases)).lower()
        if q and q not in hay:
            continue
        ent = scores[scores["entity_id"] == e.id] if not scores.empty else scores
        series = weekly_weighted_series(ent) if not ent.empty else pd.DataFrame()
        latest = first = None
        spark = []
        if not series.empty:
            latest = round(float(series["avg_tone"].iloc[-1]), 2)
            first = round(float(series["avg_tone"].iloc[0]), 2)
            spark = deps.df_records(series[["week_start", "avg_tone"]])
        results.append({
            "id": e.id, "name": e.name, "type": e.type,
            "home_country": e.home_country, "aliases": e.aliases,
            "latest": latest, "delta": (round(latest - first, 2)
                                        if latest is not None and first is not None else None),
            "spark": spark,
        })
    return {"query": q, "count": len(results), "results": results}


@router.get("/report")
def report(scope: str, id: str, w0: str | None = None, w1: str | None = None,
           format: str = Query("markdown", pattern="^(markdown|pdf)$")) -> Response:
    if scope not in {"entity", "country"}:
        raise HTTPException(400, "scope must be 'entity' or 'country'.")
    wl = deps.get_watchlist()
    scores = deps.get_scores()
    if scores.empty:
        raise HTTPException(404, "No data.")
    weeks = sorted(scores["week_start"].dt.date.unique())
    w0d = pd.to_datetime(w0).date() if w0 else weeks[0]
    w1d = pd.to_datetime(w1).date() if w1 else weeks[-1]
    label = (wl.name_by_entity.get(id, id) if scope == "entity"
             else wl.name_by_gdelt.get(id, id))
    summary = build_summary(
        scores, scope=scope, scope_id=id, scope_label=label, w0=w0d, w1=w1d,
        name_by_gdelt=wl.name_by_gdelt, name_by_entity=wl.name_by_entity,
        events=deps.get_events(), synthetic=deps.synthetic_count() > 0)

    safe = "".join(c if c.isalnum() else "_" for c in label).strip("_").lower()
    fname = f"report_{scope}_{safe}_{w0d}_{w1d}"
    if format == "pdf":
        return Response(
            content=to_pdf_bytes(summary), media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{fname}.pdf"'})
    return Response(
        content=to_markdown(summary), media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{fname}.md"'})
