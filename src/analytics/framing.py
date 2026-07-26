"""Cross-language / domestic-vs-foreign framing comparison.

Same entity, coverage tone split by the LANGUAGE and ORIGIN of the press:
  * domestic vs foreign  — home-country coverage vs everywhere else
  * by language          — how outlets in each language frame the entity

Domestic/foreign is computed from the country-level aggregated_scores
(home_country marks "domestic"). By-language uses a per-language aggregation
of the articles table (language isn't in aggregated_scores).

REMINDER: differences here are DIFFERENCES IN MEDIA FRAMING across presses,
not differences in what populations believe. Translation of non-English
coverage can itself shift measured tone.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def domestic_vs_foreign(scores: pd.DataFrame, home_country: str | None) -> dict:
    """scores: entity-filtered aggregated_scores (country, avg_tone, article_volume).

    Returns dict with domestic/foreign tone + volume. If the entity has no
    home country (cross-cutting theme), 'domestic' is None.
    """
    def wmean(df):
        w = df["article_volume"].to_numpy(dtype=float)
        v = df["avg_tone"].to_numpy(dtype=float)
        return float((v * w).sum() / w.sum()) if w.sum() > 0 else float("nan")

    out = {"domestic_tone": None, "domestic_vol": 0,
           "foreign_tone": None, "foreign_vol": 0, "gap": None}
    if home_country:
        dom = scores[scores["country"] == home_country]
        if not dom.empty:
            out["domestic_tone"] = round(wmean(dom), 3)
            out["domestic_vol"] = int(dom["article_volume"].sum())
    foreign = scores[scores["country"] != home_country] if home_country else scores
    if not foreign.empty:
        out["foreign_tone"] = round(wmean(foreign), 3)
        out["foreign_vol"] = int(foreign["article_volume"].sum())
    if out["domestic_tone"] is not None and out["foreign_tone"] is not None:
        out["gap"] = round(out["domestic_tone"] - out["foreign_tone"], 3)
    return out


def by_language(lang_summary: pd.DataFrame, *, min_articles: int = 20) -> pd.DataFrame:
    """Tidy a per-language article summary for display.

    lang_summary: columns language, n, avg_tone, outlets (from storage helper).
    Flags low-volume languages as low-confidence.
    """
    if lang_summary.empty:
        return lang_summary
    df = lang_summary.copy()
    df["low_confidence"] = df["n"] < min_articles
    df["avg_tone"] = df["avg_tone"].round(3)
    return df.sort_values("n", ascending=False).reset_index(drop=True)
