"""Shared NLP pipeline for on-demand text analysis.

This is the ONE place the system scores raw text itself. (Bulk ingestion uses
GDELT's precomputed tone, so there is no ingestion model to share — this module
is the single sentiment/entity engine for any text the app analyses directly.)

Pluggable by design:
  * sentiment: VADER by default (offline, lightweight); a HuggingFace
    transformers backend activates automatically if installed + selected.
  * entities:  watchlist/alias matching always; spaCy NER enriches if installed.

Everything is reported on the SAME -100..+100 media-tone scale as the rest of
the app, and clearly framed as coverage/text sentiment, not public opinion.
"""
from .pipeline import analyze_text, AnalysisResult  # noqa: F401
from .sentiment import get_scorer, SentimentScorer, score_to_label  # noqa: F401
