"""Optional lightweight emotion breakdown (beyond polarity).

A small built-in keyword lexicon maps words to coarse emotions. This is an
INDICATIVE signal only — it is not a trained emotion classifier and misses
context, negation and sarcasm. Surfaced as optional, clearly labelled.

Upgrade path: a transformers emotion model (e.g. a GoEmotions/DistilRoBERTa
classifier) can replace `emotion_breakdown` without changing callers.
"""
from __future__ import annotations

import re
from collections import Counter

# Compact, obviously-partial keyword lexicon (stems matched as substrings on
# word tokens). Enough to give an indicative breakdown on political text.
_EMOTION_WORDS = {
    "anger":    ["anger", "angry", "outrage", "furious", "fury", "rage",
                 "backlash", "condemn", "slam", "attack", "hostil"],
    "fear":     ["fear", "afraid", "threat", "danger", "crisis", "risk",
                 "warn", "alarm", "panic", "worr"],
    "joy":      ["joy", "happy", "celebrat", "praise", "welcome", "success",
                 "hope", "optimis", "win", "triumph", "delight"],
    "sadness":  ["sad", "grief", "mourn", "tragedy", "loss", "despair",
                 "disappoint", "suffer"],
    "trust":    ["trust", "support", "confidence", "reliable", "endorse",
                 "back", "ally", "cooperat"],
    "disgust":  ["disgust", "corrupt", "scandal", "shame", "fraud",
                 "betray", "sleaze"],
}

_TOKEN_RE = re.compile(r"\b[\w']+\b")


def emotion_breakdown(text: str) -> dict[str, float]:
    """Return {emotion: proportion} over matched emotion words (sums to ~1).

    Empty dict if no emotion words are found.
    """
    tokens = [t.lower() for t in _TOKEN_RE.findall(text)]
    counts: Counter[str] = Counter()
    for tok in tokens:
        for emo, stems in _EMOTION_WORDS.items():
            if any(stem in tok for stem in stems):
                counts[emo] += 1
                break
    total = sum(counts.values())
    if total == 0:
        return {}
    return {emo: round(counts[emo] / total, 3)
            for emo in sorted(counts, key=counts.get, reverse=True)}
