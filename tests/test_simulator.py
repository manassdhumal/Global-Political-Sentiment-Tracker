from starlette.testclient import TestClient
from api.main import app
from src.analytics.simulator import simulate_policy_shock, EVENT_PRESETS

client = TestClient(app)


def test_simulate_policy_shock_rate_hike():
    res = simulate_policy_shock(
        topic_id="inflation",
        event_type="rate_hike",
        magnitude=1.0,
        weeks_ahead=6,
    )
    assert res["topic"]["id"] == "inflation"
    assert res["event"]["type"] == "rate_hike"
    assert "metrics" in res
    assert "simulation" in res
    assert len(res["simulation"]["dates"]) == 6
    assert len(res["simulation"]["shocked_media"]) == 6
    assert len(res["simulation"]["baseline_media"]) == 6
    assert res["metrics"]["recovery_weeks"] > 0


def test_simulate_policy_shock_custom():
    res = simulate_policy_shock(
        topic_id="donald_trump",
        event_type="custom",
        magnitude=1.5,
        weeks_ahead=4,
        custom_description="Major international summit speech",
    )
    assert res["topic"]["id"] == "donald_trump"
    assert len(res["simulation"]["dates"]) == 4


def test_simulator_api_endpoints():
    # Presets
    resp_presets = client.get("/api/simulator/presets")
    assert resp_presets.status_code == 200
    assert "presets" in resp_presets.json()

    # Run simulation
    payload = {
        "topic": "inflation",
        "event_type": "rate_cut",
        "magnitude": 1.0,
        "weeks_ahead": 6,
    }
    resp = client.post("/api/simulator/run", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "metrics" in data
    assert "simulation" in data
