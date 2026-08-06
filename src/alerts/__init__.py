"""Alerting and notification subsystem for sentiment shocks and anomaly events."""
from .detector import (
    SentimentShockAlert,
    scan_catalog_alerts,
    scan_live_topic_alert,
)
from .notifiers import (
    dispatch_alert,
    dispatch_all_alerts,
    send_discord_webhook,
    send_telegram_message,
    send_generic_webhook,
)

__all__ = [
    "SentimentShockAlert",
    "scan_catalog_alerts",
    "scan_live_topic_alert",
    "dispatch_alert",
    "dispatch_all_alerts",
    "send_discord_webhook",
    "send_telegram_message",
    "send_generic_webhook",
]
