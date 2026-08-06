"""Tests for Cross-Asset Financial Spillover & Market Contagion Suite."""
import pytest
from fastapi.testclient import TestClient
import numpy as np

from api.main import app
from src.ingestion.market_client import get_market_series, GLOBAL_ASSET_REGISTRY
from src.analytics.markets import (
    compute_granger_causality,
    analyze_market_spillover,
    get_all_assets_summary,
)

client = TestClient(app)


def test_market_client_ingestion():
    df = get_market_series("brent_oil", weeks=26)
    assert not df.empty
    assert len(df) == 26
    assert "price" in df.columns
    assert "weekly_return_pct" in df.columns


def test_compute_granger_causality():
    rng = np.random.default_rng(42)
    s1 = rng.normal(0, 1, 30)
    s2 = rng.normal(0, 1, 30)
    res = compute_granger_causality(s1, s2, max_lag=2)
    assert "causality_detected" in res
    assert "optimal_lag_weeks" in res
    assert "p_value" in res
    assert isinstance(res["causality_detected"], bool)


def test_analyze_market_spillover():
    res = analyze_market_spillover(topic_id="inflation", asset_id="gold", weeks=26)
    assert res["topic"]["id"] == "inflation"
    assert res["asset"]["id"] == "gold"
    assert "correlation_r" in res["metrics"]
    assert "spillover_beta" in res["metrics"]
    assert "granger_causality" in res["metrics"]
    assert len(res["series"]) > 0


def test_get_all_assets_summary():
    summary = get_all_assets_summary()
    assert len(summary) >= len(GLOBAL_ASSET_REGISTRY)
    assert "latest_price" in summary[0]
    assert "perf_12w_pct" in summary[0]
