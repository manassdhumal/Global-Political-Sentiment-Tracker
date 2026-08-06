"""Webhook and messaging dispatchers for sentiment shock alerts."""
from __future__ import annotations

import os
import logging
from typing import Sequence
import requests

from .detector import SentimentShockAlert

logger = logging.getLogger(__name__)


def send_discord_webhook(webhook_url: str, alert: SentimentShockAlert) -> bool:
    """Send a structured rich embed alert to a Discord webhook channel."""
    color_map = {
        "critical": 0xE11D48,  # Red/Rose
        "warning": 0xF59E0B,   # Amber/Orange
        "info": 0x38BDF8,      # Sky Blue
    }
    color = color_map.get(alert.severity, 0x64748B)

    embed = {
        "title": f"🚨 [{alert.severity.upper()}] {alert.topic_label} — {alert.alert_type.replace('_', ' ').title()}",
        "description": alert.description,
        "color": color,
        "fields": [
            {"name": "Category", "value": alert.category, "inline": True},
            {"name": "Severity", "value": alert.severity.capitalize(), "inline": True},
            {"name": "Score / Delta", "value": f"{alert.delta:+.2f}", "inline": True},
        ],
        "footer": {"text": "Global Political Sentiment Tracker • Real-Time Alert Engine"},
        "timestamp": alert.timestamp,
    }

    payload = {
        "username": "GPST Alert Bot",
        "avatar_url": "https://raw.githubusercontent.com/manassdhumal/Global-Political-Sentiment-Tracker/main/frontend/public/icon.png",
        "embeds": [embed],
    }

    try:
        resp = requests.post(webhook_url, json=payload, timeout=8.0)
        return resp.status_code in (200, 204)
    except Exception as exc:
        logger.warning(f"Failed to send Discord webhook: {exc}")
        return False


def send_telegram_message(bot_token: str, chat_id: str, alert: SentimentShockAlert) -> bool:
    """Send formatted Markdown alert message to a Telegram chat or channel."""
    emoji_map = {
        "critical": "🔴",
        "warning": "🟡",
        "info": "🔵",
    }
    icon = emoji_map.get(alert.severity, "⚪")

    text = (
        f"{icon} *[GPST ALERT - {alert.severity.upper()}]*\n\n"
        f"*Topic:* `{alert.topic_label}` ({alert.category})\n"
        f"*Alert:* {alert.alert_type.replace('_', ' ').title()}\n"
        f"*Magnitude:* `{alert.delta:+.2f}`\n\n"
        f"{alert.description}\n\n"
        f"_Timestamp: {alert.timestamp[:19]}_"
    )

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
    }

    try:
        resp = requests.post(url, json=payload, timeout=8.0)
        return resp.status_code == 200
    except Exception as exc:
        logger.warning(f"Failed to send Telegram message: {exc}")
        return False


def send_generic_webhook(webhook_url: str, alert: SentimentShockAlert) -> bool:
    """Send standardized JSON alert payload to any HTTP webhook endpoint (e.g. Slack / Zapier)."""
    payload = {
        "source": "Global Political Sentiment Tracker",
        "event": "sentiment_shock",
        "alert": alert.to_dict(),
    }
    try:
        resp = requests.post(webhook_url, json=payload, timeout=8.0)
        return 200 <= resp.status_code < 300
    except Exception as exc:
        logger.warning(f"Failed to send generic webhook: {exc}")
        return False


def dispatch_alert(alert: SentimentShockAlert) -> dict[str, bool]:
    """Dispatch a single alert across all configured channels."""
    results = {}
    discord_url = os.environ.get("GPST_DISCORD_WEBHOOK")
    if discord_url:
        results["discord"] = send_discord_webhook(discord_url, alert)

    tg_token = os.environ.get("GPST_TELEGRAM_BOT_TOKEN")
    tg_chat = os.environ.get("GPST_TELEGRAM_CHAT_ID")
    if tg_token and tg_chat:
        results["telegram"] = send_telegram_message(tg_token, tg_chat, alert)

    generic_url = os.environ.get("GPST_ALERT_WEBHOOK_URL")
    if generic_url:
        results["generic"] = send_generic_webhook(generic_url, alert)

    return results


def dispatch_all_alerts(alerts: Sequence[SentimentShockAlert]) -> dict:
    """Dispatch multiple alerts and return execution summary."""
    dispatched = 0
    channel_counts = {"discord": 0, "telegram": 0, "generic": 0}

    for alert in alerts:
        res = dispatch_alert(alert)
        if any(res.values()):
            dispatched += 1
            for ch, ok in res.items():
                if ok:
                    channel_counts[ch] = channel_counts.get(ch, 0) + 1

    return {
        "total_alerts": len(alerts),
        "dispatched_alerts": dispatched,
        "channels": channel_counts,
    }
