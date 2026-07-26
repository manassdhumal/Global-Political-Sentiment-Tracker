"""Shared dashboard helpers: cached data loading, colors, event markers.

Every view imports from here so data is loaded once (cached) and the
"media sentiment, not public opinion" framing is applied consistently.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Make `src` importable when Streamlit runs a view file directly.
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.config import (  # noqa: E402
    DEFAULT_DB_PATH, load_watchlist, load_events, Watchlist, Event)
from src import storage  # noqa: E402

# --- shared palette ---
TONE_POS = "#2c7fb8"     # blue = positive coverage tone
TONE_NEG = "#d7301f"     # red  = negative coverage tone
NEUTRAL = "#8a8a8a"
LOWCONF = "#f0a202"      # amber for low-confidence markers

DISCLAIMER = (
    "Scores are **media sentiment (the tone of news _coverage_), not public "
    "opinion.** Coverage can be sparse for smaller countries/languages; thin "
    "weeks are flagged low-confidence. Translation, sarcasm and outlet bias "
    "all affect tone.")


def db_path() -> str:
    return str(DEFAULT_DB_PATH)


def db_mtime() -> float:
    p = Path(db_path())
    return p.stat().st_mtime if p.exists() else 0.0


@st.cache_resource
def get_watchlist() -> Watchlist:
    return load_watchlist()


@st.cache_data(show_spinner=False)
def get_events() -> list[Event]:
    return load_events()


@st.cache_data(show_spinner=False)
def load_scores(mtime: float) -> pd.DataFrame:
    """Aggregated scores enriched with entity + country display fields.

    `mtime` is part of the cache key so a fresh pipeline run busts the cache.
    """
    wl = get_watchlist()
    conn = storage.connect(db_path())
    try:
        scores = storage.read_aggregated_scores(conn)
        entities = storage.list_entities(conn)
        row = conn.execute(
            "SELECT COUNT(*) FROM articles WHERE source='synthetic'").fetchone()
        n_synth = row[0] if row else 0
    finally:
        conn.close()

    if not scores.empty:
        scores = scores.merge(
            entities[["id", "name", "type"]].rename(
                columns={"name": "entity_name", "type": "entity_type"}),
            left_on="entity_id", right_on="id", how="left").drop(columns=["id"])
        scores["country_name"] = scores["country"].map(wl.name_by_gdelt)
        scores["iso3"] = scores["country"].map(wl.iso3_by_gdelt)
    scores.attrs["n_synth"] = n_synth
    return scores


def require_data() -> pd.DataFrame:
    """Load scores or stop the page with a helpful message if empty."""
    if db_mtime() == 0.0:
        st.warning("No database yet. Run:\n\n"
                   "`python scripts/run_pipeline.py --source synthetic`")
        st.stop()
    scores = load_scores(db_mtime())
    if scores.empty:
        st.warning("No aggregated scores yet. Run:\n\n"
                   "`python scripts/run_pipeline.py --source synthetic`")
        st.stop()
    return scores


def synthetic_banner(scores: pd.DataFrame) -> None:
    if scores.attrs.get("n_synth", 0) > 0:
        st.info("⚠ **Synthetic (fabricated) data** loaded — a stand-in for the "
                "GDELT feed when the live API is unavailable. Not real coverage.")


def add_event_markers(fig: go.Figure, events: list[Event], *,
                      x_min, x_max, entity_id=None, country=None) -> None:
    """Draw vertical dashed lines for events applicable to this chart."""
    x_min = pd.to_datetime(x_min)
    x_max = pd.to_datetime(x_max)
    for ev in events:
        if not ev.applies_to(entity_id=entity_id, country=country):
            continue
        d = pd.to_datetime(ev.date)
        if d < x_min or d > x_max:
            continue
        fig.add_vline(x=d, line_width=1, line_dash="dash", line_color=NEUTRAL)
        fig.add_annotation(x=d, y=1.0, yref="paper", text=ev.label,
                           showarrow=False, textangle=-90, xanchor="left",
                           font=dict(size=9, color=NEUTRAL), opacity=0.9)


def tone_color(value: float) -> str:
    return TONE_POS if value >= 0 else TONE_NEG
