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


def test_simulate_policy_shock_new_presets():
    res = simulate_policy_shock(
        topic_id="inflation",
        event_type="trade_war",
        magnitude=1.0,
        weeks_ahead=6,
    )
    assert res["event"]["type"] == "trade_war"
    
    res = simulate_policy_shock(
        topic_id="inflation",
        event_type="climate_accord",
        magnitude=1.0,
        weeks_ahead=6,
    )
    assert res["event"]["type"] == "climate_accord"
    
    res = simulate_policy_shock(
        topic_id="inflation",
        event_type="leadership_change",
        magnitude=1.0,
        weeks_ahead=6,
    )
    assert res["event"]["type"] == "leadership_change"


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
    assert isinstance(resp_presets.json(), list)

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

    # Batch simulation
    batch_payload = {
        "topic": "inflation",
        "magnitude": 1.0,
        "weeks_ahead": 6,
    }
    resp_batch = client.post("/api/simulator/batch", json=batch_payload)
    assert resp_batch.status_code == 200
    batch_data = resp_batch.json()
    assert "ranked_events" in batch_data
    assert len(batch_data["ranked_events"]) > 5  # should have all presets
