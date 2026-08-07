"""API Router for Executive PDF Dossier Exports and Quantitative CSV Data Dumps."""
from __future__ import annotations

import io
from datetime import date
from typing import Any
import pandas as pd
from fastapi import APIRouter, Query, Response, HTTPException
from fastapi.responses import StreamingResponse

from src.analytics.pdf_export import generate_topic_pdf_dossier
from src.topics.catalog import resolve_topic
from src.topics.synth import global_weekly
from src.analytics.markets import analyze_market_spillover, GLOBAL_ASSET_REGISTRY
from src.analytics.timeseries import analyze_econometric_timeseries


router = APIRouter(prefix="/api/export", tags=["export"])


@router.get("/pdf/dossier")
def export_topic_pdf(
    topic: str = Query("us_china", description="Topic identifier for the PDF briefing memo")
):
    """Download publication-ready Executive Intelligence Dossier in vector PDF format."""
    try:
        pdf_bytes = generate_topic_pdf_dossier(topic_id=topic)
        filename = f"Intelligence_Dossier_{topic}_{date.today().strftime('%Y%m%d')}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")


@router.get("/csv/timeseries")
def export_timeseries_csv(
    topic: str = Query("inflation", description="Topic identifier for time series data dump")
):
    """Download historical sentiment, HP filter cycle, secular trend, and volatility data as CSV."""
    try:
        ts_data = analyze_econometric_timeseries(topic_id=topic)
        df = pd.DataFrame({
            "date": ts_data["dates"],
            "avg_tone": ts_data["raw_tone"],
            "secular_trend": ts_data["hp_decomposition"]["trend"],
            "cyclical_component": ts_data["hp_decomposition"]["cycle"],
            "rolling_volatility_4w": ts_data["volatility"]["series"],
        })
        stream = io.StringIO()
        df.to_csv(stream, index=False)
        stream.seek(0)
        filename = f"timeseries_data_{topic}_{date.today().strftime('%Y%m%d')}.csv"
        return StreamingResponse(
            io.BytesIO(stream.getvalue().encode("utf-8")),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export CSV: {str(e)}")


@router.get("/csv/market-spillover")
def export_market_spillover_csv(
    topic: str = Query("inflation", description="Topic identifier"),
    asset: str = Query("brent_oil", description="Macro financial asset identifier"),
):
    """Download aligned sentiment vs financial asset price and weekly return time series CSV."""
    try:
        mkt_data = analyze_market_spillover(topic_id=topic, asset_id=asset)
        df = pd.DataFrame(mkt_data["series"])
        stream = io.StringIO()
        df.to_csv(stream, index=False)
        stream.seek(0)
        filename = f"spillover_{topic}_{asset}_{date.today().strftime('%Y%m%d')}.csv"
        return StreamingResponse(
            io.BytesIO(stream.getvalue().encode("utf-8")),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export Market Spillover CSV: {str(e)}")
