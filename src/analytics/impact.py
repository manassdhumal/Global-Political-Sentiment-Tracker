"""Event impact scoring — before/after tone delta around a known event date.

Compares the volume-weighted average coverage tone in the N weeks BEFORE an
event to the N weeks AFTER, and reports the delta. When scipy is available a
Welch t-test on the weekly values gives a rough significance read.

REMINDER: this is an association (tone moved around the same time), not proof
of causation, and short windows are noisy.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class ImpactResult:
    before_tone: float
    after_tone: float
    delta: float
    n_before: int          # weeks with data before
    n_after: int
    vol_before: int        # article volume before
    vol_after: int
    p_value: float | None  # Welch t-test on weekly tone, if computable
    note: str = ""


def _wmean(df: pd.DataFrame) -> float:
    w = df["article_volume"].to_numpy(dtype=float)
    v = df["avg_tone"].to_numpy(dtype=float)
    return float((v * w).sum() / w.sum()) if w.sum() > 0 else float("nan")


def event_impact(history: pd.DataFrame, event_date, *,
                 window_weeks: int = 3) -> ImpactResult:
    """history: columns week_start (datetime), avg_tone, article_volume."""
    ev = pd.to_datetime(event_date)
    h = history.dropna(subset=["avg_tone"]).sort_values("week_start")
    lo = ev - pd.Timedelta(weeks=window_weeks)
    hi = ev + pd.Timedelta(weeks=window_weeks)

    before = h[(h["week_start"] < ev) & (h["week_start"] >= lo)]
    after = h[(h["week_start"] >= ev) & (h["week_start"] <= hi)]

    b_tone = _wmean(before) if not before.empty else float("nan")
    a_tone = _wmean(after) if not after.empty else float("nan")
    delta = a_tone - b_tone

    p_value = None
    if len(before) >= 2 and len(after) >= 2:
        try:
            from scipy import stats
            p_value = float(stats.ttest_ind(
                after["avg_tone"], before["avg_tone"],
                equal_var=False).pvalue)
        except Exception:
            p_value = None

    note = ""
    if before.empty or after.empty:
        note = "Insufficient data on one side of the event for a reliable delta."

    return ImpactResult(
        before_tone=round(b_tone, 3) if before.size else float("nan"),
        after_tone=round(a_tone, 3) if after.size else float("nan"),
        delta=round(delta, 3) if before.size and after.size else float("nan"),
        n_before=int(before["week_start"].nunique()),
        n_after=int(after["week_start"].nunique()),
        vol_before=int(before["article_volume"].sum()) if not before.empty else 0,
        vol_after=int(after["article_volume"].sum()) if not after.empty else 0,
        p_value=p_value, note=note,
    )
