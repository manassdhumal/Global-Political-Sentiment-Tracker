"""Tests for the shared NLP pipeline: sentiment, entities, aspect, explain."""
from __future__ import annotations

from src.config import load_watchlist
from src.nlp import analyze_text
from src.nlp.sentiment import get_scorer, score_to_label

WL = load_watchlist()


def test_scorer_scale_and_polarity():
    sc = get_scorer("vader")
    pos = sc.score("This is wonderful, a fantastic and brilliant success!")
    neg = sc.score("This is terrible, an awful and disgraceful disaster.")
    assert 0 < pos <= 100
    assert -100 <= neg < 0
    assert score_to_label(pos) == "positive"
    assert score_to_label(neg) == "negative"
    assert sc.score("") == 0.0


def test_aspect_based_scores_are_separate():
    # Same text, opposite sentiment toward two tracked entities.
    text = ("I really admire Narendra Modi, he did a wonderful job. "
            "Donald Trump gave a terrible, disgraceful speech.")
    res = analyze_text(text, WL, use_spacy=False)
    by_id = {a.entity_id: a for a in res.aspects}
    assert "narendra_modi" in by_id and "donald_trump" in by_id
    assert by_id["narendra_modi"].score > 0
    assert by_id["donald_trump"].score < 0
    # not a single blended number
    assert by_id["narendra_modi"].score != by_id["donald_trump"].score


def test_entities_detected_from_watchlist():
    res = analyze_text("Inflation is rising and Macron responded.", WL,
                       use_spacy=False)
    ids = {e.entity_id for e in res.entities if e.tracked}
    assert "inflation" in ids
    assert "emmanuel_macron" in ids


def test_explainability_has_drivers():
    res = analyze_text("A wonderful triumph, but a terrible crisis and outrage.",
                       WL, use_spacy=False)
    assert res.contributions
    assert res.top_positive or res.top_negative
    # positive drivers push up, negative push down
    assert all(c.delta > 0 for c in res.top_positive)
    assert all(c.delta < 0 for c in res.top_negative)
