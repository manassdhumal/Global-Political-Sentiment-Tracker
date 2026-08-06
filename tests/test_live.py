"""Tests for Live Breaking News Sentiment Stream Suite."""
import pytest
from fastapi.testclient import TestClient

from api.main import app
from src.streaming.live_stream import generate_live_tick

client = TestClient(app)


def test_generate_live_tick():
    tick = generate_live_tick()
    assert "timestamp" in tick
    assert "topic" in tick
    assert "outlet" in tick
    assert "headline" in tick
    assert "tone" in tick
    assert "velocity" in tick
    assert isinstance(tick["tone"], float)
