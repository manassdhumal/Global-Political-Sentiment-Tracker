"""Analyze-text view — on-demand sentiment/entity analysis of user input.

Runs the shared src.nlp pipeline (steps 20-23): overall score, detected
entities/themes, per-entity aspect sentiment, explainability highlighting,
comparison against the current aggregate trend, and optional emotions.
"""
from __future__ import annotations

import html

import plotly.graph_objects as go
import streamlit as st

from src.analytics import weekly_weighted_series
from src.nlp import analyze_text
from src.nlp.sentiment import available_backends
from src.dashboard import common

_EXAMPLE = ("I really admire how Narendra Modi handled the summit — it was a "
            "triumph. But rising inflation and the cost-of-living crisis are "
            "causing real anger and hardship. Donald Trump gave a controversial "
            "speech that sparked outrage and backlash.")


def _gauge(score: float) -> go.Figure:
    color = common.tone_color(score)
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=score,
        number={"suffix": "", "font": {"size": 34}},
        gauge={"axis": {"range": [-100, 100]},
               "bar": {"color": color},
               "steps": [{"range": [-100, -5], "color": "rgba(215,48,31,0.15)"},
                         {"range": [-5, 5], "color": "rgba(140,140,140,0.15)"},
                         {"range": [5, 100], "color": "rgba(44,127,184,0.15)"}],
               "threshold": {"line": {"color": color, "width": 4},
                             "value": score}}))
    fig.update_layout(height=230, margin=dict(t=20, b=10, l=20, r=20))
    return fig


def _highlight(text: str, contribs) -> str:
    """Wrap scored tokens in colored spans (green=positive, red=negative)."""
    spans = sorted(contribs, key=lambda c: c.start)
    out, cursor = [], 0
    for c in spans:
        if c.start < cursor:
            continue
        out.append(html.escape(text[cursor:c.start]))
        alpha = min(0.85, abs(c.delta) / 10.0 + 0.15)
        rgb = "44,127,184" if c.delta > 0 else "215,48,31"
        tok = html.escape(text[c.start:c.end])
        out.append(f'<span style="background:rgba({rgb},{alpha:.2f});'
                   f'border-radius:3px;padding:0 2px" title="{c.delta:+.1f}">'
                   f'{tok}</span>')
        cursor = c.end
    out.append(html.escape(text[cursor:]))
    return "".join(out)


def render() -> None:
    wl = common.get_watchlist()
    scores = common.load_scores(common.db_mtime()) if common.db_mtime() else None

    st.subheader("📝 Analyze your own text")
    st.caption("Runs the same sentiment/entity engine on text you paste. Scores "
               "use the **same −100…+100 media-tone scale**. This measures the "
               "sentiment of the *text*, framed like coverage tone — not truth "
               "or public opinion.")

    backends = available_backends()
    with st.sidebar:
        backend = st.selectbox("Sentiment engine", backends, key="at_backend",
                               help="VADER is offline/lightweight. 'transformers' "
                                    "appears only if installed.")
        use_spacy = st.checkbox("Use spaCy NER (if installed)", value=True,
                                key="at_spacy")
        with_emotion = st.checkbox("Show emotion breakdown", value=True,
                                   key="at_emotion")

    text = st.text_area("Text to analyze", value=_EXAMPLE, height=150,
                        key="at_text")
    # VADER is fast, so analyze the current text on each run (no submit needed).
    if not text.strip():
        st.info("Enter some text above to analyze it.")
        return

    res = analyze_text(text, wl, backend=backend, use_spacy=use_spacy,
                       with_emotion=with_emotion)

    # --- overall ---
    left, right = st.columns([1, 1])
    with left:
        st.plotly_chart(_gauge(res.overall_score), use_container_width=True)
        st.markdown(f"**Overall:** {res.overall_score:+.1f} "
                    f"· _{res.overall_label}_ · engine: `{res.backend}`")
    with right:
        st.markdown("**Explainability — what drove the score**")
        st.markdown(
            '<div style="line-height:1.9">' + _highlight(text, res.contributions)
            + "</div>", unsafe_allow_html=True)
        st.caption("Blue = pushed positive, red = pushed negative "
                   "(leave-one-out; hover a word for its impact).")

    # --- aspect-based sentiment + comparison vs aggregate trend ---
    st.markdown("---")
    st.markdown("**Per-entity sentiment (aspect-based)** — a separate score for "
                "each entity, plus how it compares to the live coverage trend.")
    if not res.aspects:
        st.info("No entities detected to break down.")
    else:
        rows = []
        for a in res.aspects:
            agg_tone = None
            if a.tracked and a.entity_id and scores is not None:
                ent = scores[scores["entity_id"] == a.entity_id]
                series = weekly_weighted_series(ent)
                if not series.empty:
                    agg_tone = round(float(series["avg_tone"].iloc[-1]), 2)
            rows.append({
                "Entity": a.name + ("" if a.tracked else " (untracked)"),
                "Your text": a.score,
                "Current coverage trend": agg_tone if agg_tone is not None else "—",
                "Δ (text − trend)": round(a.score - agg_tone, 2)
                if agg_tone is not None else "—",
                "Mentions": a.mentions,
            })
        import pandas as pd
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        st.caption("‘Current coverage trend’ is the latest weekly aggregate tone "
                   "for that tracked entity across all countries.")

    # --- emotions ---
    if res.emotions:
        st.markdown("**Emotion breakdown** (indicative, keyword-based — not a "
                    "trained classifier)")
        emo = res.emotions
        fig = go.Figure(go.Bar(x=list(emo.values()), y=list(emo.keys()),
                               orientation="h", marker_color="#756bb1"))
        fig.update_layout(height=max(180, 30 * len(emo)),
                          margin=dict(t=10, b=10), xaxis_title="share")
        st.plotly_chart(fig, use_container_width=True)

    for n in res.notes:
        st.caption("ℹ " + n)
    st.caption(common.DISCLAIMER)
