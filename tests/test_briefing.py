from starlette.testclient import TestClient
from api.main import app
from src.topics.analyze import analyze_topic
from src.reporting.briefing import (
    generate_topic_briefing_markdown,
    generate_topic_briefing_html,
    generate_topic_briefing,
)

client = TestClient(app)


def test_briefing_markdown_generation():
    data = analyze_topic("inflation")
    md = generate_topic_briefing_markdown(data)
    assert "# 🛡️ GEOPOLITICAL INTELLIGENCE BRIEFING" in md
    assert "INFLATION" in md
    assert "Quantitative Sentiment Indicators" in md


def test_briefing_html_generation():
    data = analyze_topic("donald_trump")
    html = generate_topic_briefing_html(data)
    assert "<!DOCTYPE html>" in html
    assert "DONALD TRUMP" in html
    assert "Executive Summary" in html


def test_briefing_api_endpoint():
    resp = client.get("/api/briefing?topic=inflation&format=markdown")
    assert resp.status_code == 200
    assert "GEOPOLITICAL INTELLIGENCE BRIEFING" in resp.text
    assert resp.headers["content-type"].startswith("text/markdown")

    resp_html = client.get("/api/briefing?topic=inflation&format=html")
    assert resp_html.status_code == 200
    assert "<!DOCTYPE html>" in resp_html.text


def test_alerts_and_correlation_endpoints():
    # Test live alerts
    resp_alerts = client.get("/api/alerts/live?threshold=1.5")
    assert resp_alerts.status_code == 200
    data = resp_alerts.json()
    assert "alerts" in data
    assert "count" in data

    # Test correlation
    resp_corr = client.get("/api/topics/correlation?topics=inflation,donald_trump&metric=media")
    assert resp_corr.status_code == 200
    corr = resp_corr.json()
    assert corr["metric"] == "media"
    assert len(corr["columns"]) == 2
    assert "matrix" in corr
    assert "pairs" in corr
    assert "lead_lag" in corr
