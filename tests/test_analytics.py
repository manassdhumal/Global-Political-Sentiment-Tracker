"""Tests for analytics: weighted series, volatility, forecast, anomaly, impact."""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.analytics import (weekly_weighted_series, volatility_index,
                           forecast_tone, detect_anomalies, event_impact)
from src.analytics.polarization import analyze_media_polarization
from src.analytics.timeseries import analyze_econometric_timeseries


def _scores(entity="e1", country="US", n=12, base=0.0, slope=0.5, vol=20):
    weeks = pd.date_range("2026-01-05", periods=n, freq="7D")
    return pd.DataFrame({
        "entity_id": entity, "country": country, "week_start": weeks,
        "avg_tone": base + slope * np.arange(n),
        "article_volume": vol, "source_diversity": 4, "low_confidence": 0,
    })


def test_weighted_series_collapses_countries():
    df = pd.concat([_scores(country="US", base=10, vol=30),
                    _scores(country="FR", base=-10, vol=10)])
    s = weekly_weighted_series(df)
    assert len(s) == 12
    # US weighted 3:1 over FR -> first week weighted mean = (10*30 + -10*10)/40 = 5
    assert abs(s["avg_tone"].iloc[0] - 5.0) < 1e-6


def test_forecast_extends_series():
    df = _scores(n=16)  # Give it enough data for ETS
    fr = forecast_tone(df.rename(columns={}), periods=4)
    assert len(fr.forecast) == 4
    assert fr.method in {"arima", "linear", "ets"}
    assert (fr.forecast["upper"] >= fr.forecast["lower"]).all()
    assert hasattr(fr, "preferred_method")
    assert hasattr(fr, "ets_forecast")


def test_anomaly_flags_a_clear_spike():
    df = _scores(n=12, slope=0.0, base=0.0)
    df.loc[6, "avg_tone"] = 50.0            # inject a clear outlier
    a = detect_anomalies(df[["week_start", "avg_tone"]], z_thresh=3.0)
    assert bool(a["is_anomaly"].any())
    # Ensure our new fields are populated
    assert "kind" in a.columns
    assert "direction" in a.columns
    assert "shift" in a.columns


def test_volatility_ranks_higher_for_noisier_series():
    calm = _scores(entity="calm", slope=0.0, base=0.0)
    swing = _scores(entity="swing", slope=0.0, base=0.0)
    swing["avg_tone"] = [(-20 if i % 2 else 20) for i in range(len(swing))]
    idx = volatility_index(pd.concat([calm, swing]), group="entity", min_weeks=4)
    top = idx.iloc[0]
    assert top["entity_id"] == "swing"


def test_event_impact_delta():
    df = _scores(n=12, slope=0.0, base=0.0)
    df.loc[df.index >= 6, "avg_tone"] = 10.0   # step up after week index 6
    res = event_impact(df[["week_start", "avg_tone", "article_volume"]],
                       df["week_start"].iloc[6], window_weeks=3)
    assert res.delta > 0


def test_polarization_convergence_trend():
    res = analyze_media_polarization("inflation")
    assert "summary" in res
    assert "convergence_trend" in res["summary"]
    assert res["summary"]["convergence_trend"] in {"widening", "narrowing", "stable"}


def test_timeseries_ewm_trend():
    res = analyze_econometric_timeseries("inflation")
    assert "ewm_trend" in res
    assert len(res["ewm_trend"]) == len(res["raw_tone"])
