"""Tests for Media Polarization & Editorial Framing Spectrum Suite."""
import pytest
from fastapi.testclient import TestClient

from api.main import app
from src.analytics.polarization import (
    analyze_media_polarization,
    MEDIA_SPECTRUM_REGISTRY,
)

client = TestClient(app)


def test_polarization_registry():
    assert len(MEDIA_SPECTRUM_REGISTRY) >= 4
    assert "center_left" in MEDIA_SPECTRUM_REGISTRY
    assert "center_right" in MEDIA_SPECTRUM_REGISTRY
    assert "centrist_wires" in MEDIA_SPECTRUM_REGISTRY


def test_analyze_media_polarization():
    res = analyze_media_polarization(topic_id="inflation")
    assert res["topic"]["id"] == "inflation"
    assert "summary" in res
    assert "latest_polarization_spread" in res["summary"]
    assert len(res["spectra"]) == len(MEDIA_SPECTRUM_REGISTRY)
    assert len(res["timeline"]) > 0
    assert "keywords" in res["spectra"][0]
