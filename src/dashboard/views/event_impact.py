"""Event impact view — before/after coverage-tone delta around an event."""
from __future__ import annotations

import datetime as dt

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.analytics import weekly_weighted_series, event_impact
from src.dashboard import common


def render() -> None:
    scores = common.require_data()
    common.synthetic_banner(scores)
    wl = common.get_watchlist()
    events = common.get_events()

    st.subheader("🎯 Event impact scoring")
    st.caption("How did coverage tone move **before vs after** an event? This is "
               "an association around a date, not proof of causation — and short "
               "windows are noisy.")

    # --- choose event ---
    labels = [f"{e.date} — {e.label}" for e in events] + ["Custom date…"]
    pick = st.sidebar.selectbox("Event", range(len(labels)),
                                format_func=lambda i: labels[i], key="ei_event")
    if pick < len(events):
        ev = events[pick]
        event_date = pd.to_datetime(ev.date)
        default_entity = ev.scope_id if ev.scope_type == "entity" else None
        default_country = ev.scope_id if ev.scope_type == "country" else None
    else:
        event_date = pd.to_datetime(st.sidebar.date_input(
            "Event date", value=dt.date(2026, 6, 1), key="ei_date"))
        default_entity = default_country = None

    entity_ids = wl.entity_ids
    e_default = entity_ids.index(default_entity) if default_entity in entity_ids else 0
    entity_id = st.sidebar.selectbox(
        "Measure impact on entity", entity_ids, index=e_default,
        format_func=lambda e: wl.name_by_entity.get(e, e), key="ei_entity")

    ent_rows = scores[scores["entity_id"] == entity_id]
    countries = ["__all__"] + sorted(ent_rows["country"].unique(),
                                     key=lambda c: wl.name_by_gdelt.get(c, c))
    c_default = countries.index(default_country) if default_country in countries else 0
    country = st.sidebar.selectbox(
        "Coverage origin", countries, index=c_default,
        format_func=lambda c: "All countries (combined)"
        if c == "__all__" else wl.name_by_gdelt.get(c, c), key="ei_country")

    window = st.sidebar.slider("Window (weeks each side)", 1, 6, 3, key="ei_win")

    view = ent_rows if country == "__all__" else ent_rows[ent_rows["country"] == country]
    hist = weekly_weighted_series(view)
    scope = ("all countries" if country == "__all__"
             else wl.name_by_gdelt.get(country, country))
    st.markdown(f"**{wl.name_by_entity.get(entity_id, entity_id)}** · {scope} · "
                f"event **{event_date.date()}**")

    if hist.empty:
        st.warning("No data for this selection.")
        return

    res = event_impact(hist, event_date, window_weeks=window)

    c1, c2, c3 = st.columns(3)
    c1.metric(f"Tone before ({res.n_before} wks)",
              "—" if pd.isna(res.before_tone) else f"{res.before_tone:+.2f}",
              f"{res.vol_before:,} articles")
    c2.metric(f"Tone after ({res.n_after} wks)",
              "—" if pd.isna(res.after_tone) else f"{res.after_tone:+.2f}",
              f"{res.vol_after:,} articles")
    c3.metric("Δ tone (after − before)",
              "—" if pd.isna(res.delta) else f"{res.delta:+.2f}")

    if res.p_value is not None:
        sig = "likely meaningful" if res.p_value < 0.05 else "not statistically clear"
        st.caption(f"Welch t-test p = {res.p_value:.3f} — the shift is **{sig}** "
                   "given weekly variability.")
    if res.note:
        st.warning(res.note)

    # --- chart with event line + shaded windows ---
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hist["week_start"], y=hist["avg_tone"],
                             mode="lines+markers", name="Coverage tone",
                             line=dict(color=common.TONE_POS, width=2)))
    fig.add_vline(x=event_date, line_color=common.TONE_NEG, line_width=2)
    fig.add_vrect(x0=event_date - pd.Timedelta(weeks=window), x1=event_date,
                  fillcolor="gray", opacity=0.10, line_width=0)
    fig.add_vrect(x0=event_date, x1=event_date + pd.Timedelta(weeks=window),
                  fillcolor="orange", opacity=0.12, line_width=0)
    fig.add_hline(y=0, line_dash="dot", line_color=common.NEUTRAL)
    fig.add_annotation(x=event_date, y=1.0, yref="paper", text="event",
                       showarrow=False, font=dict(color=common.TONE_NEG))
    fig.update_layout(height=400, margin=dict(t=30, b=10),
                      yaxis_title="Media coverage tone (−100 … +100)",
                      xaxis_title="Week", hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

    st.caption(common.DISCLAIMER)
