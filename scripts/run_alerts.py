"""CLI background worker to scan for sentiment shocks and dispatch notifications."""
from __future__ import annotations

import argparse
import sys
import os
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

# Load env variables
load_dotenv()

from src.alerts.detector import scan_catalog_alerts, scan_live_topic_alert
from src.alerts.notifiers import dispatch_all_alerts, dispatch_alert


def main() -> int:
    parser = argparse.ArgumentParser(description="GPST Automated Sentiment Shock Scanner & Alert Dispatcher")
    parser.add_argument("--threshold", type=float, default=2.0, help="Movement threshold for swing alerts (default: 2.0)")
    parser.add_argument("--topic", type=str, default=None, help="Scan a single specific topic query/slug instead of catalog")
    parser.add_argument("--dry-run", action="store_true", help="Print detected alerts without dispatching webhooks")
    parser.add_argument("--source", type=str, default="synthetic", choices=["synthetic", "auto", "live"])

    args = parser.parse_args()

    print("====================================================================")
    print(" Global Political Sentiment Tracker — Anomaly & Shock Alert Runner")
    print("====================================================================")
    print(f" Mode: {'Single Topic (' + args.topic + ')' if args.topic else 'Full Catalog'}")
    print(f" Threshold: {args.threshold} pts | Source: {args.source} | Dry Run: {args.dry_run}")
    print("--------------------------------------------------------------------")

    if args.topic:
        alerts = scan_live_topic_alert(args.topic, source=args.source)
    else:
        alerts = scan_catalog_alerts(threshold=args.threshold, source=args.source)

    if not alerts:
        print("✓ No anomalous sentiment shocks or divergence spikes detected.")
        return 0

    print(f"🚨 Found {len(alerts)} alert condition(s):\n")
    for i, a in enumerate(alerts, 1):
        sev_color = "[CRITICAL]" if a.severity == "critical" else "[WARNING]"
        print(f"  {i}. {sev_color} {a.topic_label} ({a.category})")
        print(f"     Type: {a.alert_type} | Magnitude: {a.delta:+.2f}")
        print(f"     {a.description}")
        print()

    if args.dry_run:
        print("[Dry Run] Skipping webhook notification dispatch.")
        return 0

    # Dispatch webhooks if channels configured
    has_discord = bool(os.environ.get("GPST_DISCORD_WEBHOOK"))
    has_telegram = bool(os.environ.get("GPST_TELEGRAM_BOT_TOKEN") and os.environ.get("GPST_TELEGRAM_CHAT_ID"))
    has_generic = bool(os.environ.get("GPST_ALERT_WEBHOOK_URL"))

    if not (has_discord or has_telegram or has_generic):
        print("ℹ️  No alert channels configured in .env (GPST_DISCORD_WEBHOOK, GPST_TELEGRAM_BOT_TOKEN, etc.).")
        print("   Alerts were scanned successfully.")
        return 0

    print("Dispatching alerts to configured channels...")
    summary = dispatch_all_alerts(alerts)
    print(f"✓ Dispatched {summary['dispatched_alerts']}/{summary['total_alerts']} alerts: {summary['channels']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
