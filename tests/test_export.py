"""Tests for PDF Dossier & CSV Data Export Engine."""
import pytest
from fastapi.testclient import TestClient

from api.main import app
from src.analytics.pdf_export import generate_topic_pdf_dossier

client = TestClient(app)


def test_generate_topic_pdf_dossier():
    pdf_bytes = generate_topic_pdf_dossier("us_china")
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    # PDF magic bytes header
    assert pdf_bytes.startswith(b"%PDF")


def test_api_export_pdf_endpoint():
    res = client.get("/api/export/pdf/dossier?topic=us_china")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert len(res.content) > 1000


def test_api_export_csv_timeseries():
    res = client.get("/api/export/csv/timeseries?topic=inflation")
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    assert b"date,avg_tone,secular_trend" in res.content


def test_api_export_csv_markets():
    res = client.get("/api/export/csv/market-spillover?topic=inflation&asset=brent_oil")
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    assert b"price" in res.content
