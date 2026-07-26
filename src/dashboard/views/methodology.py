"""Methodology & limitations page — what this tool measures, and what it doesn't."""
from __future__ import annotations

import streamlit as st

from src.dashboard import common


def render() -> None:
    scores = common.require_data()
    wl = common.get_watchlist()
    synthetic = scores.attrs.get("n_synth", 0) > 0

    st.subheader("📚 Methodology & limitations")

    st.markdown("""
### What this measures — and what it does **not**

This system measures the **tone of news _coverage_** — how positively or
negatively the media writes about a figure, party or issue. It is expressed on
a **−100 … +100** scale (GDELT's tone convention).

> **It is _not_ a measure of public opinion.** A score of “−4 for Entity X in
> France” means French-origin *coverage* of X leaned negative — **not** that
> French *people* dislike X. There is no polling here. Throughout the app,
> results are labelled **media sentiment / coverage tone** for this reason.
""")

    if synthetic:
        st.info("⚠ **This instance is running on synthetic (fabricated) data** — a "
                "deterministic stand-in for the GDELT feed used when the live API "
                "is unavailable. The numbers you see are for demonstrating the "
                "system, and are **not real coverage**.")

    st.markdown("""
### How a score is built

1. **Ingestion** — coverage is pulled from **GDELT** (Global Database of Events,
   Language & Tone), which spans news media in 100+ languages. GDELT supplies a
   pre-computed *tone* per item, so this tool aggregates an existing signal
   rather than re-scoring every article.
2. **Cleaning** — de-duplication, country-code and date normalization.
3. **Aggregation** — tone and article volume are rolled up to
   **entity × country × ISO-week**, with tone volume-weighted across articles.

### Data-integrity signals (shown throughout)

- **Source diversity** — the number of *distinct outlets* behind a weekly score.
  A score from many outlets is more robust than one from a single source.
- **Low-confidence flag** — weeks with **too few articles** (< 5) or **only one
  outlet** are flagged. GDELT coverage is genuinely sparse for smaller countries
  and non-English languages, so treat flagged cells with caution.
""")

    st.markdown("""
### Known limitations

- **Coverage ≠ opinion.** Media tone reflects how outlets frame a subject, which
  is shaped by editorial choices, not a representative public.
- **Selection & outlet bias.** Which stories get covered, and by whom, skews the
  signal. Outlet-level bias is not corrected for.
- **Translation artifacts.** Non-English coverage is machine-processed; tone can
  shift in translation.
- **Sarcasm & irony.** Tone scoring (GDELT's, and the VADER engine used for
  user-submitted text) misreads sarcasm and heavy context.
- **Sparse coverage.** Small countries/languages produce noisy, low-volume
  series — hence the low-confidence flags.
- **Correlation ≠ causation.** Event-impact deltas show tone moved *around* a
  date, not that the event *caused* it.
- **Forecasts are indicative.** Short, noisy news series make projections
  uncertain — always read the confidence interval, not just the line.

### The user-text analysis engine

The **Analyze text** page scores pasted text with a **pluggable** engine:
**VADER** (a lexicon/rule model, offline, the default) with an optional
**HuggingFace transformers** backend if installed. Entity detection matches the
tracked watchlist (plus optional spaCy NER). Per-entity *aspect* scores come from
the sentences mentioning each entity; explainability uses a backend-agnostic
leave-one-out method. The same **−100 … +100** scale is used so submitted text is
comparable to the aggregates — with the same caveats above.

### Upgrade paths

GDELT tone → true per-article tone via GDELT GKG/BigQuery; VADER → transformers
(RoBERTa); sklearn-LDA → BERTopic; ARIMA → Prophet. These were deliberately kept
lean for a robust, Python-3.13-friendly install.
""")

    st.caption(f"Currently tracking **{len(wl.entities)} entities** across "
               f"**{len(wl.countries)} countries**. Watchlist is fully "
               "config-driven (`config/watchlist.yaml`).")
