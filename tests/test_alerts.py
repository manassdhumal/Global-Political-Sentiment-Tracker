from src.alerts.detector import (
    SentimentShockAlert,
    scan_catalog_alerts,
    scan_live_topic_alert,
)
from src.alerts.notifiers import (
    send_discord_webhook,
    send_telegram_message,
    send_generic_webhook,
)


def test_sentiment_shock_alert_serialization():
    alert = SentimentShockAlert(
        topic_id="inflation",
        topic_label="Inflation & Cost of Living",
        category="economy",
        alert_type="sentiment_swing",
        severity="critical",
        delta=-3.8,
        current_value=-4.5,
        description="Severe negative drop in coverage sentiment.",
        timestamp="2026-08-06T00:00:00Z",
        details={"volume": 12000},
    )
    d = alert.to_dict()
    assert d["topic_id"] == "inflation"
    assert d["severity"] == "critical"
    assert d["delta"] == -3.8


def test_scan_catalog_alerts():
    # Scanning with low threshold should yield alerts from existing catalog
    alerts = scan_catalog_alerts(threshold=1.0)
    assert isinstance(alerts, list)
    for a in alerts:
        assert isinstance(a, SentimentShockAlert)
        assert a.topic_label
        assert a.severity in ("info", "warning", "critical")


def test_scan_live_topic_alert():
    alerts = scan_live_topic_alert("donald_trump")
    assert isinstance(alerts, list)


def test_notifiers_dry_mock():
    alert = SentimentShockAlert(
        topic_id="test",
        topic_label="Test Topic",
        category="politics",
        alert_type="sentiment_swing",
        severity="info",
        delta=1.0,
        current_value=0.5,
        description="Test description",
        timestamp="2026-08-06T00:00:00Z",
        details={},
    )
    # Invalid or dummy URLs should fail gracefully without throwing uncaught exceptions
    assert not send_discord_webhook("http://invalid.local/webhook", alert)
    assert not send_telegram_message("dummy_token", "dummy_chat", alert)
    assert not send_generic_webhook("http://invalid.local/webhook", alert)
