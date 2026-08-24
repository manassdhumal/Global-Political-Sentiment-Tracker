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


def test_generate_analyst_dossier_press_archetype():
    res = generate_analyst_dossier(topic_id="inflation", archetype="press")
    assert res["topic"]["id"] == "inflation"
    assert res["archetype"] == "press"
    assert "PRESS BRIEFING" in res["bluf"] or "press" in res["bluf"].lower()


def test_qa_includes_rag_sources():
    from src.analytics.analyst_agent import answer_analyst_question
    res = answer_analyst_question(topic_id="inflation", question="What is the market impact?")
    assert "answer" in res
    assert "key_takeaways" in res
    assert "rag_sources" in res


def test_generate_weekly_digest():
    from src.analytics.analyst_agent import generate_weekly_digest
    res = generate_weekly_digest("test_watchlist", ["inflation", "donald_trump"])
    assert res["watchlist_id"] == "test_watchlist"
    assert "narrative" in res
    assert "top_movers" in res
    assert res["topic_count"] > 0
