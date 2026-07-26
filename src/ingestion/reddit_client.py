"""Reddit opinion source (via PRAW).

Searches Reddit for posts mentioning an entity and returns them as
OpinionPost records (text only — scoring happens later in the shared NLP
engine). Requires credentials in .env (see .env.example); raises OpinionError
if unavailable so the orchestrator can fall back to synthetic data.

Respects Reddit's API terms: read-only search via the official API, author
handles are hashed downstream, and only short text snippets are retained.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from .opinion_types import OpinionPost
from ..settings import reddit_creds


class OpinionError(RuntimeError):
    pass


def _client():
    creds = reddit_creds()
    if not creds.available:
        raise OpinionError("Reddit credentials not configured (see .env.example).")
    try:
        import praw
    except Exception as exc:  # pragma: no cover
        raise OpinionError(f"praw not installed: {exc}")
    try:
        return praw.Reddit(
            client_id=creds.client_id,
            client_secret=creds.client_secret,
            user_agent=creds.user_agent,
            check_for_async=False,
        )
    except Exception as exc:
        raise OpinionError(f"Could not init Reddit client: {exc}")


def fetch_posts(entity_id: str, query: str, start: date, end: date, *,
                limit: int = 200, client=None) -> list[OpinionPost]:
    reddit = client or _client()
    lo = datetime.combine(start, datetime.min.time(), tzinfo=timezone.utc).timestamp()
    hi = datetime.combine(end, datetime.max.time(), tzinfo=timezone.utc).timestamp()
    posts: list[OpinionPost] = []
    try:
        for sub in reddit.subreddit("all").search(query, sort="new", limit=limit):
            created = float(getattr(sub, "created_utc", 0) or 0)
            if not (lo <= created <= hi):
                continue
            text = (getattr(sub, "title", "") or "")
            body = (getattr(sub, "selftext", "") or "")
            if body:
                text = f"{text}. {body}"[:500]
            author = str(getattr(sub, "author", "") or "deleted")
            posts.append(OpinionPost(
                entity_id=entity_id, source="reddit",
                community=f"r/{sub.subreddit.display_name}",
                lang="en", text=text.strip(),
                created_date=datetime.fromtimestamp(created, timezone.utc)
                    .strftime("%Y-%m-%d"),
                author=author,
                url=f"https://reddit.com{getattr(sub, 'permalink', '')}"))
    except Exception as exc:
        raise OpinionError(f"Reddit search failed: {exc}")
    return posts
