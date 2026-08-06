"""Tests for Custom Watchlists & Threshold Alert Engine."""
import pytest
from fastapi.testclient import TestClient

from api.main import app
from src.analytics.alerts_engine import list_all_watchlists, evaluate_watchlist, get_global_unread_alerts

client = TestClient(app)


def test_list_all_watchlists():
    wls = list_all_watchlists()
    assert len(wls) >= 4
    for w in wls:
        assert "id" in w
        assert "name" in w
        assert "basket_tone" in w
        assert "members" in w
        assert len(w["members"]) > 0


def test_evaluate_watchlist():
    res = evaluate_watchlist("test_wl", ["inflation", "ukraine_war"])
    assert res["id"] == "test_wl"
    assert "basket_tone" in res
    assert "total_volume" in res
    assert len(res["members"]) == 2
    assert "active_alerts" in res


def test_get_global_unread_alerts():
    alerts = get_global_unread_alerts()
    assert isinstance(alerts, list)
