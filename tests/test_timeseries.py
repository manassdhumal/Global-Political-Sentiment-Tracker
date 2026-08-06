"""Tests for Applied Econometric Time-Series Suite."""
import pytest
from fastapi.testclient import TestClient
import pandas as pd
import numpy as np

from api.main import app
from src.analytics.timeseries import (
    decompose_hp_filter,
    evaluate_stationarity,
    detect_structural_breaks,
    compute_volatility_clustering,
    analyze_econometric_timeseries,
)

client = TestClient(app)


def test_decompose_hp_filter():
    s = pd.Series([1.0, 1.2, 1.8, 2.5, 2.1, 1.9, 2.4, 3.1, 2.8, 2.5, 3.2, 3.5])
    res = decompose_hp_filter(s, lamb=1600.0)
    assert "trend" in res
    assert "cycle" in res
    assert len(res["trend"]) == len(s)
    assert len(res["cycle"]) == len(s)
    assert isinstance(res["cyclical_variance_pct"], float)


def test_stationarity_evaluation():
    # Mean-reverting white noise series
    rng = np.random.default_rng(42)
    s = pd.Series(rng.normal(0, 1, 30))
    res = evaluate_stationarity(s)
    assert "adf_statistic" in res
    assert "p_value" in res
    assert "is_stationary" in res
    assert isinstance(res["is_stationary"], bool)


def test_detect_structural_breaks():
    # Construct series with an explicit regime shift in the middle
    vals = [1.0] * 15 + [6.0] * 15
    dates = [f"2025-01-{i+1:02d}" for i in range(30)]
    s = pd.Series(vals)
    breaks = detect_structural_breaks(dates, s)
    assert len(breaks) >= 1
    assert breaks[0]["type"] == "Bullish Regime Shift"


def test_compute_volatility_clustering():
    s = pd.Series([1.0, 1.1, 1.0, 1.2, 5.0, 0.5, 6.0, 1.0, 1.2])
    res = compute_volatility_clustering(s, window=4)
    assert "series" in res
    assert "current_volatility" in res
    assert "regime" in res


def test_timeseries_bundle_and_endpoint():
    res = analyze_econometric_timeseries("inflation", lamb=1600.0)
    assert res["topic"]["id"] == "inflation"
    assert len(res["dates"]) > 0
    assert "hp_decomposition" in res
    assert "stationarity" in res
    assert "structural_breaks" in res
    assert "volatility" in res
