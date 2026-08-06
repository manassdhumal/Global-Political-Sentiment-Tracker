from starlette.testclient import TestClient
from api.main import app
from src.analytics.geography import get_world_sentiment_map, COUNTRY_REGISTRY

client = TestClient(app)


def test_get_world_sentiment_map_all():
    res = get_world_sentiment_map("all")
    assert "region" in res
    assert "summary" in res
    assert "countries" in res
    assert res["summary"]["country_count"] > 15
    assert len(res["countries"]) == res["summary"]["country_count"]

    first = res["countries"][0]
    assert "iso3" in first
    assert "name" in first
    assert "latest_tone" in first
    assert "spark" in first
    assert len(first["spark"]) == 12


def test_get_world_sentiment_map_g7_filter():
    res = get_world_sentiment_map("g7")
    assert res["region"] == "g7"
    for c in res["countries"]:
        assert "g7" in c["groups"]


def test_geography_api_endpoints():
    resp = client.get("/api/geography/world-map?region=all")
    assert resp.status_code == 200
    data = resp.json()
    assert "summary" in data
    assert "countries" in data

    resp_countries = client.get("/api/geography/countries")
    assert resp_countries.status_code == 200
    assert len(resp_countries.json()) >= 20
