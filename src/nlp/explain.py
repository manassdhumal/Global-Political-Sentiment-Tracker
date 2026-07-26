"""Explainability — which words drove the sentiment score.

Uses a backend-agnostic LEAVE-ONE-OUT method: remove one token at a time,
re-score, and attribute the change to that token. This works identically for
VADER or a transformers backend (no SHAP/attention dependency), and directly
answers "which words moved the score".

For long inputs the number of re-scorings is capped for responsiveness.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .sentiment import SentimentScorer

_TOKEN_RE = re.compile(r"\b[\w']+\b")


@dataclass
class WordContribution:
    token: str
    start: int
    end: int
    delta: float   # score_full - score_without_token  (>0 = pushed positive)


def word_contributions(text: str, scorer: SentimentScorer, *,
                       max_tokens: int = 60) -> list[WordContribution]:
    """Return per-token contribution to the overall score (leave-one-out)."""
    if not text or not text.strip():
        return []
    tokens = [(m.group(0), m.start(), m.end())
              for m in _TOKEN_RE.finditer(text)]
    if not tokens:
        return []
    # cap for responsiveness: keep the first max_tokens tokens
    capped = tokens[:max_tokens]

    full = scorer.score(text)
    contribs: list[WordContribution] = []
    for tok, s, e in capped:
        without = text[:s] + " " * (e - s) + text[e:]
        delta = round(full - scorer.score(without), 2)
        if delta != 0.0:
            contribs.append(WordContribution(tok, s, e, delta))
    return contribs


def top_drivers(contribs: list[WordContribution], n: int = 5
                ) -> tuple[list[WordContribution], list[WordContribution]]:
    """Return (top positive drivers, top negative drivers)."""
    pos = sorted([c for c in contribs if c.delta > 0],
                 key=lambda c: c.delta, reverse=True)[:n]
    neg = sorted([c for c in contribs if c.delta < 0],
                 key=lambda c: c.delta)[:n]
    return pos, neg
