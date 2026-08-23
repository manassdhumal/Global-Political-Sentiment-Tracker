"""Statistical correlation and lead-lag analysis across political topics."""
from __future__ import annotations

from typing import Any
import numpy as np
import pandas as pd

from src.cache import cached


def compute_pairwise_correlation(
    aligned_df: pd.DataFrame,
    method: str = "pearson",
) -> dict[str, Any]:
    """Compute pairwise correlation matrix and ranked pairs for aligned topic series."""
    if aligned_df.empty or len(aligned_df.columns) < 2:
        return {"columns": list(aligned_df.columns), "matrix": [], "pairs": []}

    corr_df = aligned_df.corr(method=method).fillna(0.0)
    cols = list(corr_df.columns)
    n = len(cols)

    # 2D matrix formatted for ECharts heatmap: [i, j, value]
    matrix_cells = []
    for i in range(n):
        for j in range(n):
            val = round(float(corr_df.iloc[i, j]), 3)
            matrix_cells.append([i, j, val])

    # Ranked distinct pairs
    pairs = []
    for i in range(n):
        for j in range(i + 1, n):
            c1, c2 = cols[i], cols[j]
            r_val = round(float(corr_df.iloc[i, j]), 3)
            # Categorize relationship
            if r_val >= 0.6:
                rel = "strong_positive"
            elif r_val >= 0.25:
                rel = "moderate_positive"
            elif r_val <= -0.6:
                rel = "strong_inverse"
            elif r_val <= -0.25:
                rel = "moderate_inverse"
            else:
                rel = "uncorrelated"

            pairs.append({
                "topic_a": c1,
                "topic_b": c2,
                "correlation": r_val,
                "relationship": rel,
            })

    pairs.sort(key=lambda p: abs(p["correlation"]), reverse=True)
    return {
        "columns": cols,
        "matrix": matrix_cells,
        "pairs": pairs,
    }


def compute_lead_lag(
    series_a: pd.Series,
    series_b: pd.Series,
    label_a: str = "Topic A",
    label_b: str = "Topic B",
    max_lag: int = 4,
) -> dict[str, Any]:
    """Compute cross-correlation across temporal lags (-max_lag to +max_lag weeks).

    Positive lag indicates Topic A leads Topic B (changes in A appear in B k weeks later).
    """
    df = pd.DataFrame({"a": series_a, "b": series_b}).dropna()
    if len(df) < max_lag * 2 + 2:
        return {
            "label_a": label_a,
            "label_b": label_b,
            "optimal_lag": 0,
            "max_correlation": 0.0,
            "zero_lag_correlation": 0.0,
            "lags": [],
            "summary": f"Insufficient historical overlap between {label_a} and {label_b} for lead-lag analysis.",
        }

    lags = []
    best_lag = 0
    best_r = -2.0

    for lag in range(-max_lag, max_lag + 1):
        if lag < 0:
            # B leads A
            r = df["a"].iloc[-lag:].corr(df["b"].iloc[:lag])
        elif lag > 0:
            # A leads B
            r = df["a"].iloc[:-lag].corr(df["b"].iloc[lag:])
        else:
            r = df["a"].corr(df["b"])

        # Guard against NaN (e.g. constant sub-series after slicing)
        r_clean = round(float(0.0 if (np.isnan(r) if not isinstance(r, float) else np.isnan(r)) else r), 3)
        lags.append({"lag_weeks": lag, "correlation": r_clean})

        if abs(r_clean) > abs(best_r):
            best_r = r_clean
            best_lag = lag

    zero_r = round(float(df["a"].corr(df["b"])), 3)
    # Guard zero_r NaN
    if np.isnan(zero_r):
        zero_r = 0.0

    if best_lag > 0 and abs(best_r) > abs(zero_r) + 0.1:
        summary = f"{label_a} leads {label_b} by ~{best_lag} week(s) (cross-correlation r = {best_r:+.2f})."
    elif best_lag < 0 and abs(best_r) > abs(zero_r) + 0.1:
        summary = f"{label_b} leads {label_a} by ~{abs(best_lag)} week(s) (cross-correlation r = {best_r:+.2f})."
    else:
        summary = f"{label_a} and {label_b} move synchronously with synchronous correlation r = {zero_r:+.2f}."

    return {
        "label_a": label_a,
        "label_b": label_b,
        "optimal_lag": best_lag,
        "max_correlation": best_r,
        "zero_lag_correlation": zero_r,
        "lags": lags,
        "summary": summary,
    }


@cached(ttl_seconds=300, key_prefix="topic_correlations")
def analyze_topic_correlations(
    topics_data: list[dict],
    metric: str = "media",  # "media" | "public" | "gap" | "attention"
) -> dict[str, Any]:
    """Extract aligned time series across topic analyses and compute correlation matrix + lead-lag."""
    series_map: dict[str, pd.Series] = {}
    label_map: dict[str, str] = {}

    for tdata in topics_data:
        topic_id = tdata["topic"]["id"]
        label = tdata["topic"]["label"]
        label_map[topic_id] = label

        if metric == "media":
            items = tdata.get("media_series", [])
            s = pd.Series(
                {pd.to_datetime(r["week_start"]): r["avg_tone"] for r in items if r.get("avg_tone") is not None}
            )
        elif metric == "public":
            items = tdata.get("opinion_series", [])
            s = pd.Series(
                {pd.to_datetime(r["week_start"]): r["avg_sentiment"] for r in items if r.get("avg_sentiment") is not None}
            )
        elif metric == "attention":
            items = tdata.get("attention_series", [])
            s = pd.Series(
                {pd.to_datetime(r["week_start"]): r["pageviews"] for r in items if r.get("pageviews") is not None}
            )
        else:
            items = tdata.get("media_vs_public", [])
            s = pd.Series(
                {pd.to_datetime(r["week_start"]): r["gap"] for r in items if r.get("gap") is not None}
            )

        if not s.empty:
            series_map[label] = s

    aligned_df = pd.DataFrame(series_map).dropna(how="all").ffill().bfill()
    corr_results = compute_pairwise_correlation(aligned_df)

    # Compute lead-lag for the top pairwise relationships
    lead_lag_results = []
    cols = list(aligned_df.columns)
    for i in range(len(cols)):
        for j in range(i + 1, min(len(cols), i + 3)):
            c1, c2 = cols[i], cols[j]
            ll = compute_lead_lag(aligned_df[c1], aligned_df[c2], label_a=c1, label_b=c2)
            lead_lag_results.append(ll)

    return {
        "metric": metric,
        "n_topics": len(series_map),
        "columns": corr_results["columns"],
        "matrix": corr_results["matrix"],
        "pairs": corr_results["pairs"],
        "lead_lag": lead_lag_results,
    }
