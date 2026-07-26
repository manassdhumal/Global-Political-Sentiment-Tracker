"""Media-vs-public comparison — the gap between press tone and social sentiment.

Combines two independent signals for an entity:
  * MEDIA tone      — GDELT coverage tone (aggregated_scores), volume-weighted
                      across countries per week.
  * PUBLIC/SOCIAL   — model-scored social posts (opinion_scores, source='all')
                      per week.

The **gap** (public − media) is the headline feature: where the public and the
press diverge. NOTE: neither is representative public opinion — media is
coverage framing; social is vocal, non-representative users. Both caveats hold.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .metrics import weekly_weighted_series


def media_weekly(media_scores: pd.DataFrame, entity_id: str) -> pd.DataFrame:
    """Weekly volume-weighted MEDIA tone for an entity (all countries)."""
    ent = media_scores[media_scores["entity_id"] == entity_id]
    if ent.empty:
        return pd.DataFrame(columns=["week_start", "media_tone", "media_volume"])
    s = weekly_weighted_series(ent)
    return s.rename(columns={"avg_tone": "media_tone",
                             "article_volume": "media_volume"})[
        ["week_start", "media_tone", "media_volume"]]


def public_weekly(opinion_scores: pd.DataFrame, entity_id: str) -> pd.DataFrame:
    """Weekly PUBLIC/social sentiment for an entity (combined source='all')."""
    if opinion_scores.empty:
        return pd.DataFrame(columns=["week_start", "public_sentiment", "public_volume"])
    ent = opinion_scores[(opinion_scores["entity_id"] == entity_id)
                         & (opinion_scores["source"] == "all")]
    if ent.empty:
        return pd.DataFrame(columns=["week_start", "public_sentiment", "public_volume"])
    out = ent[["week_start", "avg_sentiment", "post_volume"]].rename(
        columns={"avg_sentiment": "public_sentiment", "post_volume": "public_volume"})
    return out.sort_values("week_start").reset_index(drop=True)


def media_vs_public(media_scores: pd.DataFrame, opinion_scores: pd.DataFrame,
                    entity_id: str) -> pd.DataFrame:
    """Weekly join of media tone and public sentiment, with the gap."""
    m = media_weekly(media_scores, entity_id)
    p = public_weekly(opinion_scores, entity_id)
    if m.empty and p.empty:
        return pd.DataFrame(columns=["week_start", "media_tone",
                                     "public_sentiment", "gap"])
    merged = pd.merge(m, p, on="week_start", how="outer").sort_values("week_start")
    merged["gap"] = merged["public_sentiment"] - merged["media_tone"]
    for c in ("media_tone", "public_sentiment", "gap"):
        merged[c] = merged[c].round(3)
    return merged.reset_index(drop=True)


def divergence_summary(media_scores: pd.DataFrame, opinion_scores: pd.DataFrame,
                       entity_ids: list[str], name_by_entity: dict) -> pd.DataFrame:
    """Rank entities by how far public sentiment sits from media tone (overall)."""
    rows = []
    for eid in entity_ids:
        mp = media_vs_public(media_scores, opinion_scores, eid)
        both = mp.dropna(subset=["media_tone", "public_sentiment"])
        if both.empty:
            continue
        rows.append({
            "entity_id": eid, "name": name_by_entity.get(eid, eid),
            "media_tone": round(float(both["media_tone"].mean()), 2),
            "public_sentiment": round(float(both["public_sentiment"].mean()), 2),
            "gap": round(float((both["public_sentiment"] - both["media_tone"]).mean()), 2),
            "weeks": int(len(both)),
        })
    out = pd.DataFrame(rows)
    if not out.empty:
        out["abs_gap"] = out["gap"].abs()
        out = out.sort_values("abs_gap", ascending=False).drop(columns=["abs_gap"])
    return out.reset_index(drop=True)
