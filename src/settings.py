"""Runtime settings & credentials (loaded from environment / .env).

Secrets live ONLY in a git-ignored `.env` (see .env.example) or real env
vars — never in code or the repo. Nothing here is required to run the app on
synthetic fallback data; credentials only unlock LIVE public-opinion pulls.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Load .env if present (python-dotenv). Safe/no-op if the file or lib is absent.
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except Exception:
    pass


@dataclass(frozen=True)
class RedditCreds:
    client_id: str | None
    client_secret: str | None
    user_agent: str

    @property
    def available(self) -> bool:
        return bool(self.client_id and self.client_secret)


@dataclass(frozen=True)
class BlueskyCreds:
    handle: str | None
    app_password: str | None

    @property
    def available(self) -> bool:
        return bool(self.handle and self.app_password)


def reddit_creds() -> RedditCreds:
    return RedditCreds(
        client_id=os.getenv("REDDIT_CLIENT_ID") or None,
        client_secret=os.getenv("REDDIT_CLIENT_SECRET") or None,
        user_agent=os.getenv("REDDIT_USER_AGENT", "gpst:v2"),
    )


def bluesky_creds() -> BlueskyCreds:
    return BlueskyCreds(
        handle=os.getenv("BLUESKY_HANDLE") or None,
        app_password=os.getenv("BLUESKY_APP_PASSWORD") or None,
    )


def bq_project() -> str | None:
    return os.getenv("GPST_BQ_PROJECT") or None


def topic_source() -> str:
    return os.getenv("GPST_TOPIC_SOURCE", "auto").lower()


def sentiment_backend() -> str:
    return os.getenv("GPST_SENTIMENT_BACKEND", "vader").lower()


def which_opinion_sources() -> dict[str, bool]:
    """Which live social sources have credentials configured."""
    return {"reddit": reddit_creds().available,
            "bluesky": bluesky_creds().available}


def all_source_status() -> dict[str, dict]:
    """Summary of all configured and keyless live sources."""
    bq = bq_project()
    red = reddit_creds()
    bsky = bluesky_creds()
    anthropic = bool(os.getenv("ANTHROPIC_API_KEY"))

    return {
        "wikipedia": {
            "name": "Wikipedia Pageviews",
            "type": "public_attention",
            "status": "ready",
            "keyless": True,
            "description": "Public attention index (Wikimedia REST API)",
        },
        "rss": {
            "name": "Global News Wires (RSS)",
            "type": "media_headlines",
            "status": "ready",
            "keyless": True,
            "description": "Real-time coverage from BBC, Al Jazeera, DW, Guardian, France24",
        },
        "gdelt_doc": {
            "name": "GDELT DOC 2.0 API",
            "type": "media_tone",
            "status": "ready",
            "keyless": True,
            "description": "Global news tone & volume timeline",
        },
        "gdelt_bigquery": {
            "name": "GDELT BigQuery",
            "type": "media_tone_archive",
            "status": "configured" if bq else "unconfigured",
            "keyless": False,
            "description": f"GCP BigQuery project: {bq or 'not set'}",
        },
        "reddit": {
            "name": "Reddit API",
            "type": "social_opinion",
            "status": "configured" if red.available else "unconfigured",
            "keyless": False,
            "description": "PRAW client ID / secret",
        },
        "bluesky": {
            "name": "Bluesky API",
            "type": "social_opinion",
            "status": "configured" if bsky.available else "unconfigured",
            "keyless": False,
            "description": f"AT Protocol handle: {bsky.handle or 'not set'}",
        },
        "narrative_llm": {
            "name": "Anthropic Claude",
            "type": "ai_narrative",
            "status": "configured" if anthropic else "auto_rules",
            "keyless": False,
            "description": "AI narrative generator (uses auto rules if unset)",
        },
    }
