"""Tone-over-time view — single entity, with volume and event markers."""
from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from src.analytics import weekly_weighted_series
from src.dashboard import common


def render() -> None:
    scores = common.require_data()
    common.synthetic_banner(scores)
    wl = common.get_watchlist()
    events = common.get_events()

    st.subheader("📈 Tone over time")

    entity_id = st.sidebar.selectbox(
        "Entity", wl.entity_ids,
        format_func=lambda e: wl.name_by_entity.get(e, e), key="tot_entity")
    ent_rows = scores[scores["entity_id"] == entity_id]

    avail = sorted(ent_rows["country"].unique())
    sel = st.sidebar.multiselect(
        "Countries (coverage origin)", avail, default=avail,
        format_func=lambda c: wl.name_by_gdelt.get(c, c), key="tot_countries")
    split = st.sidebar.checkbox("Split by country", value=False, key="tot_split")

    weeks = sorted(ent_rows["week_start"].dt.date.unique())
    w0, w1 = (st.sidebar.select_slider(
        "Time window", options=weeks, value=(weeks[0], weeks[-1]), key="tot_win")
        if len(weeks) > 1 else (weeks[0], weeks[0]))

    view = ent_rows[ent_rows["country"].isin(sel)
                    & (ent_rows["week_start"].dt.date >= w0)
                    & (ent_rows["week_start"].dt.date <= w1)].copy()

    name = wl.name_by_entity.get(entity_id, entity_id)
    etype = ent_rows["entity_type"].iloc[0] if not ent_rows.empty else "entity"
    st.markdown(f"**{name}**  ·  _{etype}_  ·  media coverage tone")

    if view.empty:
        st.warning("No data for the selected countries / window.")
        return

    agg = weekly_weighted_series(view)
    first, last = agg["avg_tone"].iloc[0], agg["avg_tone"].iloc[-1]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Latest weekly tone", f"{last:+.2f}", f"{last - first:+.2f} vs start")
    c2.metric("Articles in window", f"{int(view['article_volume'].sum()):,}")
    c3.metric("Max source diversity", f"{int(view['source_diversity'].max())} outlets")
    c4.metric("Low-confidence weeks", f"{int(view['low_confidence'].sum())}")

    fig = go.Figure()
    if split:
        for country in sel:
            cdf = view[view["country"] == country].sort_values("week_start")
            if not cdf.empty:
                fig.add_trace(go.Scatter(
                    x=cdf["week_start"], y=cdf["avg_tone"], mode="lines+markers",
                    name=wl.name_by_gdelt.get(country, country)))
    else:
        fig.add_trace(go.Scatter(
            x=agg["week_start"], y=agg["avg_tone"], mode="lines+markers",
            name="All selected (volume-weighted)",
            line=dict(color=common.tone_color(last), width=3)))
        lc = agg[agg["low_confidence"] == 1]
        if not lc.empty:
            fig.add_trace(go.Scatter(
                x=lc["week_start"], y=lc["avg_tone"], mode="markers",
                name="Low-confidence week",
                marker=dict(color=common.LOWCONF, size=11, symbol="diamond-open")))

    fig.add_hline(y=0, line_dash="dot", line_color=common.NEUTRAL)
    # event markers: entity-scoped + global (+ country when a single country shown)
    only_country = sel[0] if len(sel) == 1 else None
    common.add_event_markers(fig, events, x_min=agg["week_start"].min(),
                             x_max=agg["week_start"].max(),
                             entity_id=entity_id, country=only_country)
    fig.update_layout(height=430, margin=dict(t=40, b=10),
                      yaxis_title="Media coverage tone (−100 … +100)",
                      xaxis_title="Week", hovermode="x unified",
                      legend=dict(orientation="h", yanchor="bottom", y=1.02))
    st.plotly_chart(fig, use_container_width=True)

    vol = view.groupby("week_start")["article_volume"].sum().reset_index()
    vfig = go.Figure(go.Bar(x=vol["week_start"], y=vol["article_volume"],
                            marker_color="#9ecae1"))
    vfig.update_layout(height=170, margin=dict(t=10, b=10),
                       yaxis_title="Article volume")
    st.plotly_chart(vfig, use_container_width=True)

    st.caption(common.DISCLAIMER)
