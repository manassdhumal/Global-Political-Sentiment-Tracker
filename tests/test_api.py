"""Smoke tests for the FastAPI backend via TestClient.

Data-dependent endpoints are skipped when the DB has no data yet, so the suite
passes in a fresh checkout; run the pipelines to exercise them fully.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def _data_ready() -> bool:
    return client.get("/health").json().get("data_ready", False)


def test_health_and_config():
    h = client.get("/health")
    assert h.status_code == 200 and h.json()["status"] == "ok"
    c = client.get("/api/config")
    assert c.status_code == 200
    body = c.json()
    assert "entities" in body and "countries" in body
    assert body["measures"].startswith("media")  # framing preserved


@pytest.mark.skipif(not _data_ready(), reason="no aggregated data in DB")
def test_core_data_endpoints():
    wl = client.get("/api/config").json()
    eid = wl["entities"][0]["id"]
    theme = next((e["id"] for e in wl["entities"] if e["type"] == "theme"), eid)

    assert client.get("/api/mood").status_code == 200
    assert client.get("/api/map", params={"entity": "__all__"}).status_code == 200
    assert client.get("/api/timeseries", params={"entity": eid}).status_code == 200
    assert client.get("/api/volatility", params={"group": "entity"}).status_code == 200
    assert client.get("/api/issue-drilldown", params={"theme": theme}).status_code == 200
    assert client.get("/api/forecast", params={"entity": eid}).status_code == 200
    assert client.get("/api/search", params={"q": ""}).status_code == 200


def test_analyze_text_endpoint():
    r = client.post("/api/analyze-text",
                    json={"text": "I admire Modi but distrust Trump and inflation is terrible."})
    assert r.status_code == 200
    body = r.json()
    assert "overall_score" in body and "aspects" in body
    # aspect-based: entities scored separately
    names = {a["entity_id"] for a in body["aspects"]}
    assert "narendra_modi" in names or "donald_trump" in names
