"""Orchestrates the on-demand text analysis pipeline.

analyze_text(text, watchlist) runs the shared sentiment + entity engine and
returns everything the "Analyze text" view needs:
  * overall sentiment on the -100..+100 scale (+ label)
  * detected entities/themes (tracked vs untracked)
  * per-entity aspect sentiment (separate score each, not one blend)
  * explainability: which words drove the overall score
  * optional emotion breakdown
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..config import Watchlist
from .aspect import AspectSentiment, aspect_sentiment
from .emotion import emotion_breakdown
from .entities import DetectedEntity, detect_entities, spacy_available
from .explain import WordContribution, top_drivers, word_contributions
from .sentiment import get_scorer, score_to_label


@dataclass
class AnalysisResult:
    text: str
    backend: str
    overall_score: float
    overall_label: str
    entities: list[DetectedEntity]
    aspects: list[AspectSentiment]
    contributions: list[WordContribution]
    top_positive: list[WordContribution]
    top_negative: list[WordContribution]
    emotions: dict[str, float]
    used_spacy: bool
    notes: list[str] = field(default_factory=list)


def analyze_text(text: str, wl: Watchlist, *,
                 backend: str | None = None,
                 use_spacy: bool = True,
                 with_emotion: bool = True) -> AnalysisResult:
    scorer = get_scorer(backend)
    overall = scorer.score(text)

    ents = detect_entities(text, wl, use_spacy=use_spacy)
    aspects = aspect_sentiment(text, ents, scorer)
    contribs = word_contributions(text, scorer)
    pos, neg = top_drivers(contribs)
    emotions = emotion_breakdown(text) if with_emotion else {}

    notes: list[str] = []
    if scorer.backend == "vader":
        notes.append("Sentiment engine: VADER (lexicon/rule-based, offline). "
                     "Does not capture sarcasm or deep context.")
    else:
        notes.append(f"Sentiment engine: {scorer.backend}.")
    if not any(e.tracked for e in ents):
        notes.append("No tracked watchlist entities detected in this text.")

    return AnalysisResult(
        text=text, backend=scorer.backend,
        overall_score=overall, overall_label=score_to_label(overall),
        entities=ents, aspects=aspects, contributions=contribs,
        top_positive=pos, top_negative=neg, emotions=emotions,
        used_spacy=(use_spacy and spacy_available()), notes=notes,
    )
