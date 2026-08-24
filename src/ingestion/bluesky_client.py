"""Bluesky opinion source (via the atproto SDK).

Searches Bluesky for posts mentioning an entity and returns OpinionPost
records. Requires a handle + app password in .env (see .env.example). Raises
OpinionError if unavailable so the orchestrator falls back to synthetic data.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from .opinion_types import OpinionPost
from .reddit_client import OpinionError  # reuse the same error type
from ..settings import bluesky_creds


def _client():
    creds = bluesky_creds()
    if not creds.available:
        raise OpinionError("Bluesky credentials not configured (see .env.example).")
    try:
        from atproto import Client
    except Exception as exc:  # pragma: no cover
        raise OpinionError(f"atproto not installed: {exc}")
    try:
        client = Client()
        client.login(creds.handle, creds.app_password)
        return client
    except Exception as exc:
        raise OpinionError(f"Bluesky login failed: {exc}")


def _parse_dt(s: str) -> str:
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).strftime("%Y-%m-%d")
    except Exception:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def fetch_posts(entity_id: str, query: str, start: date, end: date, *,
                limit: int = 100, lang: str = "en", client=None) -> list[OpinionPost]:
    bsky = client or _client()
    posts: list[OpinionPost] = []
    cursor = None
    
    # Cap internal loop to prevent runaway fetching if limit is very high
    max_loops = (limit // 100) + 2
    
    try:
        for _ in range(max_loops):
            # Try to pass as kwargs (newer atproto), fallback to dict (older)
            try:
                resp = bsky.app.bsky.feed.search_posts(q=query, limit=100, cursor=cursor)
            except Exception:
                params = {"q": query, "limit": 100}
                if cursor:
                    params["cursor"] = cursor
                resp = bsky.app.bsky.feed.search_posts(params)
                
            fetched_posts = getattr(resp, "posts", []) or []
            if not fetched_posts:
                break
                
            for p in fetched_posts:
                if len(posts) >= limit:
                    break
                    
                rec = getattr(p, "record", None)
                if not rec:
                    continue
                    
                # Language filter
                langs = getattr(rec, "langs", [])
                if lang and langs and lang not in langs:
                    continue
                    
                text = getattr(rec, "text", "")
                created = getattr(rec, "created_at", "")
                day = _parse_dt(created) if created else None
                if not day:
                    continue
                    
                d = date.fromisoformat(day)
                if not (start <= d <= end):
                    continue
                    
                author = getattr(getattr(p, "author", None), "handle", "") or "unknown"
                posts.append(OpinionPost(
                    entity_id=entity_id, source="bluesky", community="bluesky",
                    lang=lang, text=(text or "").strip()[:500],
                    created_date=day, author=author,
                    url=f"https://bsky.app/profile/{author}"))
            
            if len(posts) >= limit:
                break
                
            cursor = getattr(resp, "cursor", None)
            if not cursor:
                break
                
    except Exception as exc:
        raise OpinionError(f"Bluesky search failed: {exc}")
    return posts
