"""Aspect-based sentiment — a separate score per detected entity.

Instead of one blended score for the whole text, each entity is scored from the
SENTENCES that mention it. So "I admire Macron but distrust the new policy"
yields distinct scores for Macron vs the policy, not an average of the two.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .entities import DetectedEntity
from .sentiment import SentimentScorer, score_to_label

_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")


@dataclass
class Sentence:
    text: str
    start: int
    end: int


@dataclass
class AspectSentiment:
    name: str
    entity_id: str | None
    tracked: bool
    score: float
    label: str
    mentions: int
    snippet: str


def split_sentences(text: str) -> list[Sentence]:
    out: list[Sentence] = []
    pos = 0
    for chunk in _SENT_SPLIT.split(text):
        if not chunk:
            continue
        idx = text.find(chunk, pos)
        if idx < 0:
            idx = pos
        out.append(Sentence(chunk, idx, idx + len(chunk)))
        pos = idx + len(chunk)
    return out or [Sentence(text, 0, len(text))]


def aspect_sentiment(text: str, entities: list[DetectedEntity],
                     scorer: SentimentScorer) -> list[AspectSentiment]:
    sents = split_sentences(text)
    results: list[AspectSentiment] = []
    for ent in entities:
        # sentences overlapping any mention span
        hit = [s for s in sents
               if any(sp[0] < s.end and sp[1] > s.start for sp in ent.spans)]
        if not hit:
            continue
        scored = [(s, scorer.score(s.text)) for s in hit]
        avg = round(sum(sc for _, sc in scored) / len(scored), 2)
        rep = max(scored, key=lambda x: abs(x[1]))[0].text.strip()
        results.append(AspectSentiment(
            name=ent.name, entity_id=ent.entity_id, tracked=ent.tracked,
            score=avg, label=score_to_label(avg),
            mentions=ent.mentions, snippet=rep))
    # most opinionated first
    return sorted(results, key=lambda r: abs(r.score), reverse=True)
