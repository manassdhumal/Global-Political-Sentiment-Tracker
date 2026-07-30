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


def test_live_weekly_transform():
    from src.topics.live import weekly_from_daily
    w = weekly_from_daily({"2026-01-05": 2.0, "2026-01-06": 4.0, "2026-01-12": -3.0},
                          {"2026-01-05": 10, "2026-01-06": 30, "2026-01-12": 5})
    # Jan 5 (Mon) week: volume-weighted (2*10 + 4*30)/40 = 3.5
    assert abs(float(w.iloc[0]["avg_tone"]) - 3.5) < 1e-6
    assert int(w.iloc[0]["article_volume"]) == 40


def test_source_labels_present():
    a = analyze_topic("inflation")           # default synthetic
    assert a["stats"]["source_media"] == "synthetic"
    assert a["stats"]["source_opinion"] == "synthetic"
    assert "geo_modelled" in a["stats"]


def test_trending_and_snapshot():
    tr = trending(top_n=5)
    assert len(tr) == 5
    assert all("latest_tone" in r and "movement" in r for r in tr)
    snap = global_snapshot()
    assert "global_tone" in snap and snap["n_topics"] > 0
    assert "top_rising" in snap and "top_falling" in snap


def test_bigquery_guarded_fallback():
    from datetime import date
    from src.topics import bigquery
    # No BigQuery project/creds in tests -> must degrade to None, never raise.
    assert bigquery.bq_media_weekly("inflation", date(2025, 1, 1), date(2026, 1, 1)) is None


def test_trending_cache_roundtrip(tmp_path, monkeypatch):
    from src.topics import cache
    monkeypatch.setattr(cache, "_CACHE_PATH", tmp_path / "trending_cache.json")
    cache.write_trending({"snapshot": {"global_tone": 1.0}, "trending": [{"id": "x"}], "source": "synthetic"})
    c = cache.read_trending(max_age_hours=24)
    assert c and c["source"] == "synthetic" and c["trending"][0]["id"] == "x"
    assert "computed_at" in c
    assert cache.read_trending(max_age_hours=0) is None   # age>0h -> stale


def test_analyze_is_cached():
    import time
    analyze_topic("healthcare")                      # warm
    t = time.time(); analyze_topic("healthcare"); dt = time.time() - t
    assert dt < 0.05                                 # served from cache


def test_narrative_generated_in_bundle():
    a = analyze_topic("inflation")
    n = a["narrative"]
    assert n["backend"] == "rules"                   # rule-based default
    assert n["headline"] and n["summary"]
    assert len(n["points"]) >= 3
    # honest framing (media/social sentiment, not opinion)
    assert "tone" in n["summary"].lower() or "sentiment" in n["summary"].lower()


def test_events_in_bundle():
    a = analyze_topic("climate policy")
    ev = a["events"]
    assert isinstance(ev, list) and len(ev) > 0
    w0, w1 = a["window"]["start"], a["window"]["end"]
    for e in ev:
        assert "date" in e and "label" in e
        assert w0 <= e["date"] <= w1                 # within the topic window
    # a custom (uncatalogued) topic still gets global events
    custom = analyze_topic("teleportation policy")
    assert all(e["scope"] == "global" for e in custom["events"])


def test_narrative_handles_empty():
    from src.topics.narrative import generate_narrative
    out = generate_narrative({"topic": {"label": "Nothing"}, "media_series": []})
    assert "Not enough data" in out["headline"]
    assert out["points"] == []


def test_alerts_and_compare_endpoints():
    from fastapi.testclient import TestClient
    from api.main import app
    c = TestClient(app)

    a = c.get("/api/alerts", params={"threshold": 1.5})
    assert a.status_code == 200
    body = a.json()
    assert body["threshold"] == 1.5 and "alerts" in body
    assert all(abs(r["movement"]) >= 1.5 for r in body["alerts"])

    cmp = c.get("/api/compare-topics", params={"topics": "inflation,nato"})
    assert cmp.status_code == 200
    tops = cmp.json()["topics"]
    assert len(tops) == 2
    assert tops[0]["media_series"] and "avg_gap" in tops[0]
