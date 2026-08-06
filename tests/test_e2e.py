"""Comprehensive End-to-End (E2E) Test Suite for Global Political Sentiment Tracker.

Validates:
1. Live Data Connector Status & Diagnostics (/api/sources/status)
2. Live Attention & News Ingestion (Wikipedia pageviews + RSS News Wire)
3. Topic Analysis Pipeline (Forecasts, Drivers, Geography, Anomalies)
4. Multi-Topic Statistical Correlation & Lead-Lag Analytics (/api/topics/correlation)
5. Anomaly & Sentiment Shock Alert Engine (/api/alerts/live)
6. Executive Intelligence Briefing Export (/api/briefing for markdown & html)
7. Core Catalog Browsing & Search Endpoints
"""
import pytest
from starlette.testclient import TestClient

from api.main import app
from src.topics.analyze import analyze_topic
from src.alerts.detector import scan_catalog_alerts, scan_live_topic_alert
from src.analytics.correlation import analyze_topic_correlations
from src.reporting.briefing import generate_topic_briefing_markdown, generate_topic_briefing_html

client = TestClient(app)


class TestE2ELiveConnectors:
    def test_sources_status_endpoint(self):
        """Test /api/sources/status returns health and telemetry for all feeds."""
        resp = client.get("/api/sources/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "sources" in data
        assert "mode" in data
        assert "active_source_count" in data

        sources = data["sources"]
        assert "wikipedia" in sources
        assert "rss_news" in sources
        assert "gdelt" in sources
        assert "bluesky" in sources
        assert "reddit" in sources

        # Wikipedia and RSS news should be active and working
        assert sources["wikipedia"]["status"] == "active"
        assert sources["rss_news"]["status"] == "active"


class TestE2ETopicAnalysisPipeline:
    @pytest.mark.parametrize("topic_query", ["donald_trump", "inflation", "AI regulation"])
    def test_topic_analysis_full_bundle(self, topic_query):
        """Test topic analysis end-to-end with attention, news, forecast, and drivers."""
        resp = client.get(f"/api/topic?q={topic_query}")
        assert resp.status_code == 200
        data = resp.json()

        # 1. Topic metadata
        assert "topic" in data
        assert data["topic"]["label"]
        assert data["topic"]["category"]

        # 2. Media and Opinion time series
        assert "media_series" in data
        assert len(data["media_series"]) > 0
        assert "opinion_series" in data
        assert len(data["opinion_series"]) > 0

        # 3. Real Attention & News streams
        assert "attention_series" in data
        assert len(data["attention_series"]) > 0
        assert "live_articles" in data
        assert isinstance(data["live_articles"], list)

        # 4. Analytics: Forecasts, Anomalies, Drivers, Geography
        assert "forecast" in data
        assert "points" in data["forecast"]
        assert len(data["forecast"]["points"]) == 4  # 4-week projections

        assert "narrative" in data
        assert data["narrative"]["headline"]
        assert data["narrative"]["summary"]

        assert "stats" in data
        assert data["stats"]["total_pageviews"] >= 0


class TestE2ECorrelationAndComparison:
    def test_correlation_matrix_and_lead_lag(self):
        """Test /api/topics/correlation matrix, pairs, and lead-lag analysis."""
        topics = "inflation,donald_trump,housing_crisis"
        resp = client.get(f"/api/topics/correlation?topics={topics}&metric=media")
        assert resp.status_code == 200
        data = resp.json()

        assert data["n_topics"] == 3
        assert len(data["columns"]) == 3
        assert len(data["matrix"]) == 9  # 3x3 matrix
        assert len(data["pairs"]) == 3   # 3 choose 2

        # Verify diagonal elements are ~1.0
        for i in range(3):
            cell = next(c for c in data["matrix"] if c[0] == i and c[1] == i)
            assert abs(cell[2] - 1.0) < 0.05

        # Verify lead-lag analysis contains valid metadata
        assert len(data["lead_lag"]) >= 1
        for ll in data["lead_lag"]:
            assert "label_a" in ll
            assert "label_b" in ll
            assert "optimal_lag" in ll
            assert "summary" in ll

    def test_compare_topics_overlay(self):
        """Test /api/compare-topics returns overlaid series."""
        resp = client.get("/api/compare-topics?topics=inflation,donald_trump")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["topics"]) == 2
        for tp in data["topics"]:
            assert "media_series" in tp
            assert "opinion_series" in tp
            assert "avg_gap" in tp


class TestE2EAlertSubsystem:
    def test_live_alerts_endpoint(self):
        """Test /api/alerts/live endpoint returns formatted shock alerts."""
        resp = client.get("/api/alerts/live?threshold=1.5")
        assert resp.status_code == 200
        data = resp.json()
        assert "alerts" in data
        assert "count" in data
        assert data["count"] == len(data["alerts"])

        for alert in data["alerts"]:
            assert "topic_id" in alert
            assert "topic_label" in alert
            assert "alert_type" in alert
            assert alert["severity"] in ("info", "warning", "critical")
            assert "delta" in alert
            assert "description" in alert

    def test_scan_catalog_and_topic_alerts(self):
        """Test detector logic directly on catalog and specific topic."""
        catalog_alerts = scan_catalog_alerts(threshold=2.0)
        assert isinstance(catalog_alerts, list)

        topic_alerts = scan_live_topic_alert("donald_trump")
        assert isinstance(topic_alerts, list)


class TestE2EIntelligenceBriefings:
    def test_markdown_briefing_export(self):
        """Test Markdown briefing endpoint /api/briefing."""
        resp = client.get("/api/briefing?topic=inflation&format=markdown")
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/markdown")
        body = resp.text
        assert "# 🛡️ GEOPOLITICAL INTELLIGENCE BRIEFING: INFLATION & COST OF LIVING" in body
        assert "Executive Summary & Volatility Rating" in body
        assert "Strategic Risk Rating" in body
        assert "Quantitative Sentiment Indicators" in body
        assert "30-Day Predictive Trajectory & Scenarios" in body

    def test_html_briefing_export(self):
        """Test HTML briefing endpoint /api/briefing."""
        resp = client.get("/api/briefing?topic=donald_trump&format=html")
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/html")
        body = resp.text
        assert "<!DOCTYPE html>" in body
        assert "DONALD TRUMP" in body
        assert "Assessment:" in body
        assert "Sentiment & Attention Metrics" in body


class TestE2ECoreCatalog:
    def test_topics_catalog_endpoint(self):
        """Test /api/topics returns all catalog items with sparklines."""
        resp = client.get("/api/topics")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] > 0
        assert len(data["topics"]) == data["count"]
        first = data["topics"][0]
        assert "id" in first
        assert "label" in first
        assert "latest_tone" in first
        assert "spark" in first
