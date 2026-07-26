"""Pluggable sentiment scorer — VADER default, transformers optional.

All scores are returned on the project's -100..+100 media-tone scale so a
user's submitted text is directly comparable to GDELT-derived aggregates.

Backends:
  * 'vader'        — vaderSentiment (bundled lexicon, offline, fast). Default.
  * 'transformers' — a HuggingFace sentiment model, IF transformers+torch are
                     installed. Selected via get_scorer('transformers') or the
                     GPST_SENTIMENT_BACKEND=transformers env var. Falls back to
                     VADER on any load/inference error so the app never breaks.

VADER is a lexicon/rule model tuned for short social/news text; it does not
understand sarcasm or deep context — a limitation surfaced in the UI.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

# Standard VADER thresholds, expressed on the -100..100 scale.
POS_CUTOFF = 5.0
NEG_CUTOFF = -5.0


def score_to_label(score: float) -> str:
    if score >= POS_CUTOFF:
        return "positive"
    if score <= NEG_CUTOFF:
        return "negative"
    return "neutral"


@dataclass
class SentimentScorer:
    backend: str
    _impl: object

    def score(self, text: str) -> float:
        """Return sentiment of `text` on the -100..+100 scale."""
        if not text or not text.strip():
            return 0.0
        if self.backend == "transformers":
            return self._score_transformers(text)
        return self._score_vader(text)

    def label(self, text: str) -> str:
        return score_to_label(self.score(text))

    # -- VADER --
    def _score_vader(self, text: str) -> float:
        return round(self._impl.polarity_scores(text)["compound"] * 100, 2)

    # -- transformers --
    def _score_transformers(self, text: str) -> float:
        try:
            out = self._impl(text[:512])[0]
            label = out["label"].lower()
            conf = float(out["score"])
            sign = 1.0 if "pos" in label else (-1.0 if "neg" in label else 0.0)
            return round(sign * conf * 100, 2)
        except Exception:
            # fall back to VADER for this call
            from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
            return round(SentimentIntensityAnalyzer()
                         .polarity_scores(text)["compound"] * 100, 2)


_CACHE: dict[str, SentimentScorer] = {}


def get_scorer(backend: str | None = None) -> SentimentScorer:
    """Return a cached scorer. Default backend from env or 'vader'."""
    backend = (backend or os.getenv("GPST_SENTIMENT_BACKEND", "vader")).lower()
    if backend in _CACHE:
        return _CACHE[backend]

    if backend == "transformers":
        try:
            from transformers import pipeline  # type: ignore
            model = os.getenv("GPST_SENTIMENT_MODEL",
                              "cardiffnlp/twitter-roberta-base-sentiment-latest")
            impl = pipeline("sentiment-analysis", model=model)
            scorer = SentimentScorer("transformers", impl)
        except Exception:
            scorer = _vader_scorer()  # graceful fallback
    else:
        scorer = _vader_scorer()

    _CACHE[backend] = scorer
    return scorer


def _vader_scorer() -> SentimentScorer:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    return SentimentScorer("vader", SentimentIntensityAnalyzer())


def available_backends() -> list[str]:
    backends = ["vader"]
    try:
        import transformers  # noqa: F401
        import torch  # noqa: F401
        backends.append("transformers")
    except Exception:
        pass
    return backends
