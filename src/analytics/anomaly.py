"""Anomaly / early-warning detection on weekly tone series.

Flags two kinds of statistically unusual weeks:
  * LEVEL anomalies  — tone far from the series' typical level
  * SHIFT anomalies  — a sudden week-over-week jump (early-warning signal)

Uses robust statistics (median + MAD) so a single outlier week doesn't
inflate the baseline. No heavy dependencies.

REMINDER: an anomaly is an unusual movement in NEWS-COVERAGE TONE — a prompt
to investigate, not proof that something happened. Thin-coverage weeks can
look anomalous purely from small samples.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

_ROBUST_K = 0.6745  # scales MAD to a std-equivalent for the normal case


def _robust_z(x: np.ndarray) -> np.ndarray:
    med = np.median(x)
    mad = np.median(np.abs(x - med))
    if mad == 0:
        std = np.std(x)
        if std == 0:
            return np.zeros_like(x)
        return (x - med) / std
    return _ROBUST_K * (x - med) / mad


def detect_anomalies(history: pd.DataFrame, *, z_thresh: float = 3.0) -> pd.DataFrame:
    """Return the history with anomaly flags.

    history: columns week_start (datetime), avg_tone.
    Output adds: level_z, shift, shift_z, is_anomaly, kind, direction.
    """
    h = history[["week_start", "avg_tone"]].dropna().sort_values("week_start").copy()
    if len(h) < 4:
        h["level_z"] = 0.0
        h["shift"] = 0.0
        h["shift_z"] = 0.0
        h["is_anomaly"] = False
        h["kind"] = ""
        h["direction"] = ""
        return h.reset_index(drop=True)

    vals = h["avg_tone"].to_numpy(dtype=float)
    level_z = _robust_z(vals)

    shift = np.diff(vals, prepend=vals[0])
    shift_z = _robust_z(shift)

    level_flag = np.abs(level_z) > z_thresh
    shift_flag = np.abs(shift_z) > z_thresh
    is_anom = level_flag | shift_flag

    kind = np.where(shift_flag & level_flag, "level+shift",
                    np.where(shift_flag, "shift",
                             np.where(level_flag, "level", "")))
    direction = np.where(is_anom,
                         np.where(shift >= 0, "up", "down"), "")

    h["level_z"] = np.round(level_z, 2)
    h["shift"] = np.round(shift, 3)
    h["shift_z"] = np.round(shift_z, 2)
    h["is_anomaly"] = is_anom
    h["kind"] = kind
    h["direction"] = direction
    return h.reset_index(drop=True)


def biggest_spike_week(history: pd.DataFrame) -> pd.Timestamp | None:
    """Return the week of the largest absolute week-over-week tone shift."""
    h = history[["week_start", "avg_tone"]].dropna().sort_values("week_start")
    if len(h) < 2:
        return None
    vals = h["avg_tone"].to_numpy(dtype=float)
    shift = np.abs(np.diff(vals, prepend=vals[0]))
    return h["week_start"].iloc[int(np.argmax(shift))]
