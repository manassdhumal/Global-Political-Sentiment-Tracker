"""Tests for Autonomous AI Geopolitical Analyst Suite."""
import pytest
from fastapi.testclient import TestClient

from api.main import app
from src.analytics.analyst_agent import generate_analyst_dossier

client = TestClient(app)


def test_generate_analyst_dossier():
    res = generate_analyst_dossier(topic_id="inflation")
    assert res["topic"]["id"] == "inflation"
    assert "bluf" in res
    assert len(res["bluf"]) > 10
    assert len(res["drivers"]) >= 3
    assert len(res["stakeholders"]) >= 3
    assert len(res["scenarios"]) == 3
    assert len(res["vulnerabilities"]) >= 2
    assert "source" in res
