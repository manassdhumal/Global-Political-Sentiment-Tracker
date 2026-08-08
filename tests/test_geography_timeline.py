"""Tests for geography timeline snapshots and history arrays."""
import pytest
from src.analytics.geography import get_world_sentiment_map


def test_world_sentiment_map_timeline():
    data = get_world_sentiment_map(region="all")
    assert "timeline_weeks" in data
    assert len(data["timeline_weeks"]) > 0
    assert "summary" in data
    assert "weekly_global_tones" in data["summary"]
    
    assert len(data["countries"]) > 0
    c1 = data["countries"][0]
    assert "history" in c1
    assert "spark" in c1
    assert len(c1["history"]) == len(data["timeline_weeks"])
