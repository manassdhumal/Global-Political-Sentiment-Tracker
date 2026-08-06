"""Tests for Multi-Lingual Framing Analytics."""
import pytest
from fastapi.testclient import TestClient

from api.main import app
from src.analytics.multilingual import analyze_multilingual_framing, LANGUAGE_SPHERES

client = TestClient(app)


def test_language_spheres():
    assert len(LANGUAGE_SPHERES) == 8
    for s in LANGUAGE_SPHERES:
        assert "code" in s
        assert "name" in s
        assert "region" in s
        assert "outlets" in s
        assert len(s["outlets"]) > 0


def test_analyze_multilingual_framing():
    res = analyze_multilingual_framing("us_china")
    assert "topic" in res
    assert res["topic"]["id"] == "us_china"
    assert "disparity_spread" in res
    assert "spheres" in res
    assert len(res["spheres"]) == 8
    for s in res["spheres"]:
        assert "headline" in s
        assert "framing" in s
        assert "tone" in s
