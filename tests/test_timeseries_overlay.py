"""Tests for timeseries volatility bands and multi-topic overlays."""
import pytest
from src.analytics.timeseries import analyze_econometric_timeseries, analyze_multi_topic_overlay


def test_timeseries_volatility_bands():
    res = analyze_econometric_timeseries("inflation")
    assert "volatility_bands" in res
    assert "upper" in res["volatility_bands"]
    assert "lower" in res["volatility_bands"]
    assert len(res["volatility_bands"]["upper"]) == len(res["dates"])


def test_timeseries_multi_overlay():
    res = analyze_multi_topic_overlay(["inflation", "interest_rates", "defense_spending"])
    assert "topics" in res
    assert len(res["topics"]) == 3
    assert "dates" in res
    assert "series" in res
    assert len(res["series"]) == 3
    for s in res["series"]:
        assert "trend" in s
        assert "cycle" in s
        assert "correlation_with_primary" in s
