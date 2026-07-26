"""Entity/aspect detection in submitted text.

Strongest-available backend, layered:
  1. Watchlist matching (always on): matches configured entity names + aliases
     with word boundaries. These map to tracked entity ids, so their aspect
     sentiment can be compared against the aggregated trend.
  2. spaCy NER (optional): if spaCy + an English model are installed, also
     surfaces untracked PERSON/ORG/GPE mentions (entity_id = None).

Returns spans so the UI can highlight mentions and aspect scoring can isolate
the sentences that mention each entity.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from ..config import Watchlist


@dataclass
class DetectedEntity:
    name: str
    tracked: bool
    entity_id: str | None = None
    entity_type: str | None = None      # figure | party | theme | (spaCy label)
    spans: list[tuple[int, int]] = field(default_factory=list)

    @property
    def mentions(self) -> int:
        return len(self.spans)


def _find_spans(text: str, term: str) -> list[tuple[int, int]]:
    if not term:
        return []
    pattern = r"\b" + re.escape(term) + r"\b"
    return [(m.start(), m.end()) for m in re.finditer(pattern, text, re.IGNORECASE)]


def detect_watchlist_entities(text: str, wl: Watchlist) -> list[DetectedEntity]:
    found: list[DetectedEntity] = []
    for e in wl.entities:
        # match the display name, any aliases, AND the id as words (the
        # canonical keyword, e.g. id 'inflation' catches "inflation" even
        # when the display name is "Inflation & cost of living").
        terms = [e.name, e.id.replace("_", " ")] + list(e.aliases)
        spans: list[tuple[int, int]] = []
        for t in terms:
            spans.extend(_find_spans(text, t))
        # de-overlap: sort + drop spans contained in an earlier one
        spans = sorted(set(spans))
        deduped: list[tuple[int, int]] = []
        for s in spans:
            if not any(s[0] >= d[0] and s[1] <= d[1] for d in deduped):
                deduped.append(s)
        if deduped:
            found.append(DetectedEntity(
                name=e.name, tracked=True, entity_id=e.id,
                entity_type=e.type, spans=deduped))
    return found


def detect_spacy_entities(text: str, exclude_spans: list[tuple[int, int]]
                          ) -> list[DetectedEntity]:
    """Optional: untracked named entities via spaCy, if installed."""
    try:
        import spacy  # type: ignore
    except Exception:
        return []
    try:
        nlp = _load_spacy()
        if nlp is None:
            return []
        doc = nlp(text)
    except Exception:
        return []

    keep = {"PERSON", "ORG", "GPE", "NORP"}
    by_name: dict[str, DetectedEntity] = {}
    for ent in doc.ents:
        if ent.label_ not in keep:
            continue
        span = (ent.start_char, ent.end_char)
        if any(span[0] >= x[0] and span[1] <= x[1] for x in exclude_spans):
            continue
        key = ent.text.lower()
        if key not in by_name:
            by_name[key] = DetectedEntity(
                name=ent.text, tracked=False, entity_id=None,
                entity_type=ent.label_, spans=[])
        by_name[key].spans.append(span)
    return list(by_name.values())


_SPACY = {"loaded": False, "nlp": None}


def _load_spacy():
    if _SPACY["loaded"]:
        return _SPACY["nlp"]
    _SPACY["loaded"] = True
    try:
        import spacy  # type: ignore
        for model in ("en_core_web_sm", "en_core_web_md"):
            try:
                _SPACY["nlp"] = spacy.load(model)
                return _SPACY["nlp"]
            except Exception:
                continue
    except Exception:
        pass
    return None


def detect_entities(text: str, wl: Watchlist, *, use_spacy: bool = True
                    ) -> list[DetectedEntity]:
    tracked = detect_watchlist_entities(text, wl)
    if not use_spacy:
        return tracked
    exclude = [s for e in tracked for s in e.spans]
    return tracked + detect_spacy_entities(text, exclude)


def spacy_available() -> bool:
    return _load_spacy() is not None
