"""Topic modeling on article titles, to summarize what a tone spike is about.

Uses scikit-learn (CountVectorizer + LatentDirichletAllocation) — lightweight
and reliable on Python 3.13. For very small corpora it falls back to simple
term-frequency ranking. BERTopic (embeddings + UMAP + HDBSCAN) is a documented
upgrade path for richer topics on real, long-form text.

REMINDER: topics come from the words in HEADLINES OF COVERAGE, not from the
events themselves. On the synthetic dataset the vocabulary is fabricated.
"""
from __future__ import annotations

from dataclasses import dataclass

try:
    from sklearn.decomposition import LatentDirichletAllocation
    from sklearn.feature_extraction.text import (CountVectorizer,
                                                 ENGLISH_STOP_WORDS)
    _SKLEARN = True
except Exception:  # pragma: no cover
    _SKLEARN = False


@dataclass
class Topic:
    words: list[str]
    weight: float   # share of the corpus assigned to this topic (0..1)


def _fallback_terms(titles: list[str], stops: set[str],
                    n_top_words: int) -> list[Topic]:
    from collections import Counter
    counts: Counter[str] = Counter()
    for t in titles:
        for w in t.lower().split():
            w = "".join(ch for ch in w if ch.isalnum())
            if w and w not in stops and not w.isdigit() and len(w) > 2:
                counts[w] += 1
    if not counts:
        return []
    top = [w for w, _ in counts.most_common(n_top_words)]
    return [Topic(words=top, weight=1.0)]


def extract_topics(titles: list[str], *, n_topics: int = 3,
                   n_top_words: int = 6,
                   extra_stopwords: list[str] | None = None) -> list[Topic]:
    """Return up to `n_topics` topics (each a list of top words) from titles."""
    titles = [t for t in titles if isinstance(t, str) and t.strip()]
    stops = set(ENGLISH_STOP_WORDS) if _SKLEARN else set()
    for w in (extra_stopwords or []):
        for tok in str(w).lower().replace("(", " ").replace(")", " ").split():
            stops.add(tok)
    stops.update({"synthetic", "coverage"})

    if not _SKLEARN or len(titles) < 6:
        return _fallback_terms(titles, stops, n_top_words)

    try:
        vec = CountVectorizer(stop_words=list(stops), min_df=2,
                              token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z]+\b")
        dtm = vec.fit_transform(titles)
        vocab = vec.get_feature_names_out()
        if dtm.shape[1] < 3:
            return _fallback_terms(titles, stops, n_top_words)

        k = max(1, min(n_topics, dtm.shape[1] // 2))
        lda = LatentDirichletAllocation(n_components=k, random_state=42,
                                        learning_method="batch", max_iter=25)
        doc_topic = lda.fit_transform(dtm)
        shares = doc_topic.sum(axis=0)
        shares = shares / shares.sum() if shares.sum() else shares

        topics: list[Topic] = []
        for i, comp in enumerate(lda.components_):
            top_idx = comp.argsort()[::-1][:n_top_words]
            topics.append(Topic(words=[vocab[j] for j in top_idx],
                                weight=round(float(shares[i]), 3)))
        return sorted(topics, key=lambda t: t.weight, reverse=True)
    except Exception:
        return _fallback_terms(titles, stops, n_top_words)
