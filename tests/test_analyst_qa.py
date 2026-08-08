"""Tests for Analyst archetypes and Q&A engine."""
import pytest
from src.analytics.analyst_agent import generate_analyst_dossier, answer_analyst_question


def test_analyst_archetypes():
    for arc in ["executive", "hedge_fund", "diplomatic"]:
        dossier = generate_analyst_dossier("inflation", archetype=arc)
        assert dossier["archetype"] == arc
        assert "bluf" in dossier
        assert len(dossier["drivers"]) > 0
        assert len(dossier["scenarios"]) == 3


def test_analyst_qa():
    qa = answer_analyst_question("inflation", "What are the market spillover risks?", archetype="hedge_fund")
    assert qa["topic_id"] == "inflation"
    assert "answer" in qa
    assert len(qa["answer"]) > 10
    assert "key_takeaways" in qa
    assert len(qa["key_takeaways"]) > 0
