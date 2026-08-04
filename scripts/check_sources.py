"""Diagnostic CLI: Check connectivity & configuration for all live data streams.

Run:
    python scripts/check_sources.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import settings
from src.ingestion import wikipedia_client, rss_client, gdelt_client


def main() -> int:
    print("=" * 68)
    print(" Global Political Sentiment Tracker — Live Data Source Diagnostics")
    print("=" * 68)

    # 1. Keyless Sources
    print("\n[1] Keyless Public Real-Life Sources (No API keys required)")
    print("-" * 68)

    # Wikipedia
    print("  • Wikipedia Pageviews API : ", end="", flush=True)
    wiki_ok = wikipedia_client.health_check()
    if wiki_ok:
        print("[OK] Online & responding (Wikimedia REST API)")
    else:
        print("[FAIL] Unreachable or rate-limited")

    # RSS News Wires
    print("  • Global News Wires (RSS) : ", end="", flush=True)
    rss_ok = rss_client.health_check()
    if rss_ok:
        print("[OK] Online (BBC, Al Jazeera, DW, Guardian, France24)")
    else:
        print("[FAIL] Could not fetch RSS feeds")

    # GDELT DOC API
    print("  • GDELT DOC 2.0 API       : ", end="", flush=True)
    gdelt_ok = gdelt_client.health_check()
    if gdelt_ok:
        print("[OK] Online & responding")
    else:
        print("[WARN] GDELT DOC API slow/rate-limited (system will auto-fallback)")

    # 2. Configured Social & Archive Sources
    print("\n[2] Keyed / Authenticated Sources (Configured in .env)")
    print("-" * 68)

    # Reddit
    red = settings.reddit_creds()
    print("  • Reddit API (PRAW)       : ", end="")
    if red.available:
        print(f"[CONFIGURED] Client ID: {red.client_id[:6]}... User-Agent: {red.user_agent}")
    else:
        print("[UNCONFIGURED] Add REDDIT_CLIENT_ID & REDDIT_CLIENT_SECRET to .env")

    # Bluesky
    bsky = settings.bluesky_creds()
    print("  • Bluesky API (atproto)   : ", end="")
    if bsky.available:
        print(f"[CONFIGURED] Handle: {bsky.handle}")
    else:
        print("[UNCONFIGURED] Add BLUESKY_HANDLE & BLUESKY_APP_PASSWORD to .env")

    # BigQuery
    bq = settings.bq_project()
    print("  • GDELT BigQuery (GCP)    : ", end="")
    if bq:
        print(f"[CONFIGURED] Project: {bq}")
    else:
        print("[UNCONFIGURED] Set GPST_BQ_PROJECT to your Google Cloud project id")

    # Sentiment model
    sb = settings.sentiment_backend()
    print(f"\n[3] NLP Sentiment Scorer Backend : [{sb.upper()}]")
    if sb == "transformers":
        print("    (using local RoBERTa transformer pipeline)")
    else:
        print("    (using fast rule-based VADER engine)")

    print("\n" + "=" * 68)
    if wiki_ok and rss_ok:
        print(" Ready! Keyless real-life public attention & live news are ACTIVE.")
    print("=" * 68)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
