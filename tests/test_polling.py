from starlette.testclient import TestClient
from api.main import app
from src.ingestion.polling_client import get_entity_polling_series, POLLING_ENTITIES
from src.analytics.polling import compare_polling_vs_sentiment

client = TestClient(app)


def test_get_entity_polling_series():
    df = get_entity_polling_series("donald_trump", weeks=26)
    assert len(df) == 26
    assert "approval_pct" in df.columns
    assert "disapproval_pct" in df.columns
    assert "net_approval" in df.columns
    assert "pollster" in df.columns


def test_compare_polling_vs_sentiment():
    res = compare_polling_vs_sentiment("keir_starmer", weeks=26)
    assert res["entity"]["id"] == "keir_starmer"
    assert "latest" in res
    assert "media_bias_index" in res["latest"]
    assert "verdict" in res["latest"]
    assert len(res["series"]) > 0


def test_polling_api_endpoints():
    resp_entities = client.get("/api/polling/entities")
    assert resp_entities.status_code == 200
    assert len(resp_entities.json()) >= 6

    resp_comp = client.get("/api/polling/comparison?entity=donald_trump&weeks=26")
    assert resp_comp.status_code == 200
    data = resp_comp.json()
    assert "entity" in data
    assert "latest" in data
    assert "series" in data
