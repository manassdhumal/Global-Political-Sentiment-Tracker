"""Tests for the v3 open-ended topic layer."""
from __future__ import annotations

from src.topics import analyze_topic, trending, global_snapshot
from src.topics.catalog import load_catalog, resolve_topic


def test_catalog_loads():
    cat = load_catalog()
    assert len(cat) >= 50
    assert any(t.category == "issue" for t in cat)


def test_resolve_catalog_and_custom():
    known = resolve_topic("inflation")
    assert not known.custom
    custom = resolve_topic("quantum computing policy")
    assert custom.custom and custom.id == "quantum-computing-policy"


def test_analyze_catalog_topic_bundle():
    a = analyze_topic("inflation")
    assert a["topic"]["label"]
    assert a["age_weeks"] >= 16                 # long history
    assert len(a["media_series"]) == a["age_weeks"] or len(a["media_series"]) > 0
    assert a["media_vs_public"]                 # media + public merged
    assert a["forecast"]["method"] in {"arima", "linear", "none"}
    assert len(a["by_country"]) > 0
    assert a["stats"]["total_articles"] > 0


def test_analyze_custom_topic():
    a = analyze_topic("space policy reform")
    assert a["topic"]["custom"] is True
    assert a["media_series"]                    # open-ended topic still analysable


def test_trending_and_snapshot():
    tr = trending(top_n=5)
    assert len(tr) == 5
    assert all("latest_tone" in r and "movement" in r for r in tr)
    snap = global_snapshot()
    assert "global_tone" in snap and snap["n_topics"] > 0
    assert "top_rising" in snap and "top_falling" in snap
