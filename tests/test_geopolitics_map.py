"""Tests for Geopolitical Map Overlays (Chokepoints, Conflict Flashpoints, Elections)."""
import pytest
from fastapi.testclient import TestClient

from api.main import app
from src.analytics.geopolitics_map import (
    STRATEGIC_CHOKEPOINTS,
    CONFLICT_FLASHPOINTS,
    GLOBAL_ELECTIONS,
    get_geopolitical_map_layers,
)

client = TestClient(app)


def test_strategic_chokepoints_structure():
    assert len(STRATEGIC_CHOKEPOINTS) >= 7
    for cp in STRATEGIC_CHOKEPOINTS:
        assert "name" in cp
        assert "lat" in cp
        assert "lng" in cp
        assert "risk_tier" in cp
        assert "oil_transit_mbpd" in cp


def test_conflict_flashpoints_structure():
    assert len(CONFLICT_FLASHPOINTS) >= 6
    for fp in CONFLICT_FLASHPOINTS:
        assert "title" in fp
        assert "category" in fp
        assert "intensity" in fp
        assert "lat" in fp
        assert "lng" in fp


def test_global_elections_structure():
    assert len(GLOBAL_ELECTIONS) >= 4
    for el in GLOBAL_ELECTIONS:
        assert "country" in el
        assert "date" in el
        assert "event" in el
        assert "stakes" in el


def test_api_geography_layers_endpoint():
    res = client.get("/api/geography/layers")
    assert res.status_code == 200
    data = res.json()
    assert "chokepoints" in data
    assert "conflict_flashpoints" in data
    assert "elections" in data
    assert len(data["chokepoints"]) >= 7
