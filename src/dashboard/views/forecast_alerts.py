"""Forecast & anomalies view — projection, early-warning flags, spike topics.

Combines Phase 3 steps 15 (forecast), 16 (anomaly detection) and 17 (topic
modeling on the biggest spike).
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src import storage
from src.analytics import (weekly_weighted_series, forecast_tone,
                           detect_anomalies, biggest_spike_week, extract_topics)
from src.dashboard import common


def render() -> None:
    scores = common.require_data()
    common.synthetic_banner(scores)
    wl = common.get_watchlist()

    st.subheader("🔮 Forecast & early-warning alerts")
    st.caption("Short-term projection of coverage tone, statistically flagged "
               "anomalies, and what the biggest recent swing is about. "
               "Projections indicate the **trend of coverage tone** — not future "
               "events or public opinion.")

    entity_id = st.sidebar.selectbox(
        "Entity", wl.entity_ids,
        format_func=lambda e: wl.name_by_entity.get(e, e), key="fc_entity")
    ent_rows = scores[scores["entity_id"] == entity_id]

    countries = ["__all__"] + sorted(ent_rows["country"].unique(),
                                     key=lambda c: wl.name_by_gdelt.get(c, c))
    country = st.sidebar.selectbox(
        "Coverage origin", countries,
        format_func=lambda c: "All countries (combined)"
        if c == "__all__" else wl.name_by_gdelt.get(c, c), key="fc_country")
    horizon = st.sidebar.slider("Forecast horizon (weeks)", 2, 8, 4, key="fc_h")
    z_thresh = st.sidebar.slider("Anomaly sensitivity (lower = more flags)",
                                 2.0, 4.0, 3.0, 0.5, key="fc_z")

    view = ent_rows if country == "__all__" else ent_rows[ent_rows["country"] == country]
    hist = weekly_weighted_series(view)
    scope = ("all countries" if country == "__all__"
             else wl.name_by_gdelt.get(country, country))
    st.markdown(f"**{wl.name_by_entity.get(entity_id, entity_id)}** · {scope}")

    if hist.empty or len(hist) < 3:
        st.warning("Not enough history for this selection.")
        return

    # --- forecast + anomalies ---
    fc = forecast_tone(hist, periods=horizon)
    anoms = detect_anomalies(hist, z_thresh=z_thresh)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hist["week_start"], y=hist["avg_tone"],
                             mode="lines+markers", name="Observed tone",
                             line=dict(color=common.TONE_POS, width=2)))
    if not fc.forecast.empty:
        # connect last observed point to the forecast for visual continuity
        bridge = pd.concat([hist.iloc[[-1]].rename(columns={"avg_tone": "forecast"})[
            ["week_start", "forecast"]], fc.forecast[["week_start", "forecast"]]])
        fig.add_trace(go.Scatter(
            x=fc.forecast["week_start"], y=fc.forecast["upper"], mode="lines",
            line=dict(width=0), showlegend=False, hoverinfo="skip"))
        fig.add_trace(go.Scatter(
            x=fc.forecast["week_start"], y=fc.forecast["lower"], mode="lines",
            line=dict(width=0), fill="tonexty",
            fillcolor="rgba(120,120,120,0.2)", name="95% interval",
            hoverinfo="skip"))
        fig.add_trace(go.Scatter(
            x=bridge["week_start"], y=bridge["forecast"], mode="lines+markers",
            name=f"Forecast ({fc.method})",
            line=dict(color="#e6550d", width=2, dash="dash")))

    flagged = anoms[anoms["is_anomaly"]]
    if not flagged.empty:
        fig.add_trace(go.Scatter(
            x=flagged["week_start"], y=flagged["avg_tone"], mode="markers",
            name="Anomaly", marker=dict(color=common.TONE_NEG, size=13,
                                        symbol="x")))
    fig.add_hline(y=0, line_dash="dot", line_color=common.NEUTRAL)
    fig.update_layout(height=430, margin=dict(t=30, b=10),
                      yaxis_title="Media coverage tone (−100 … +100)",
                      xaxis_title="Week", hovermode="x unified",
                      legend=dict(orientation="h", yanchor="bottom", y=1.02))
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"Forecast method: **{fc.method}** — {fc.note} "
               "Short news series are noisy; read the interval, not just the line.")

    # --- alerts list ---
    if flagged.empty:
        st.success("No statistically unusual weeks at this sensitivity.")
    else:
        st.markdown("**⚠ Early-warning flags** (unusual weekly movements):")
        show = flagged.assign(
            Week=flagged["week_start"].dt.date,
            Tone=flagged["avg_tone"].round(2),
            Move=flagged["direction"], Kind=flagged["kind"],
            **{"Δ vs prev": flagged["shift"].round(2)})
        st.dataframe(show[["Week", "Tone", "Move", "Kind", "Δ vs prev"]],
                     use_container_width=True, hide_index=True)

    # --- topic modeling on the biggest spike ---
    st.markdown("---")
    st.markdown("**🧩 What's driving the biggest swing?**")
    spike = biggest_spike_week(hist)
    if spike is None:
        st.info("Not enough data to locate a spike.")
        return
    w0 = (spike - pd.Timedelta(weeks=1)).strftime("%Y-%m-%d")
    w1 = (spike + pd.Timedelta(weeks=1)).strftime("%Y-%m-%d")
    conn = storage.connect(common.db_path())
    try:
        titles = storage.read_titles(
            conn, entity_id, w0, w1,
            country=None if country == "__all__" else country)
    finally:
        conn.close()
    st.caption(f"Largest week-over-week swing around **{spike.date()}** "
               f"({len(titles):,} headlines in ±1 week). Topics from coverage "
               "headlines (LDA):")
    ent = wl.entity_by_id(entity_id)
    stop = list((ent.name.split() if ent else []) + (ent.aliases if ent else []))
    topics = extract_topics(titles, n_topics=3, extra_stopwords=stop)
    if not topics:
        st.info("Not enough headline text to model topics for this window.")
    else:
        for i, t in enumerate(topics, 1):
            st.markdown(f"- **Topic {i}** ({t.weight:.0%}): "
                        + ", ".join(f"`{w}`" for w in t.words))

    st.caption(common.DISCLAIMER)
