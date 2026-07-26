"""Entity-vs-entity comparison — multiple entities' tone on one chart."""
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

    st.subheader("⚖️ Entity vs. entity")
    st.caption("Compare the coverage tone of several figures/parties/issues "
               "side by side, globally or within one country.")

    sel_entities = st.sidebar.multiselect(
        "Entities to compare", wl.entity_ids,
        default=wl.entity_ids[:3],
        format_func=lambda e: wl.name_by_entity.get(e, e), key="ee_entities")

    countries = ["__all__"] + sorted(scores["country"].unique(),
                                     key=lambda c: wl.name_by_gdelt.get(c, c))
    country = st.sidebar.selectbox(
        "Coverage origin", countries,
        format_func=lambda c: "All countries (combined)"
        if c == "__all__" else wl.name_by_gdelt.get(c, c), key="ee_country")

    weeks = sorted(scores["week_start"].dt.date.unique())
    w0, w1 = (st.sidebar.select_slider(
        "Time window", options=weeks, value=(weeks[0], weeks[-1]), key="ee_win")
        if len(weeks) > 1 else (weeks[0], weeks[0]))

    if not sel_entities:
        st.warning("Pick at least one entity.")
        return

    base = scores[(scores["week_start"].dt.date >= w0)
                  & (scores["week_start"].dt.date <= w1)]
    if country != "__all__":
        base = base[base["country"] == country]

    scope = ("all countries" if country == "__all__"
             else wl.name_by_gdelt.get(country, country))
    st.markdown(f"Coverage tone · **{scope}**")

    fig = go.Figure()
    rows = []
    for eid in sel_entities:
        edf = base[base["entity_id"] == eid]
        if edf.empty:
            continue
        series = weekly_weighted_series(edf)
        fig.add_trace(go.Scatter(
            x=series["week_start"], y=series["avg_tone"], mode="lines+markers",
            name=wl.name_by_entity.get(eid, eid)))
        rows.append({"Entity": wl.name_by_entity.get(eid, eid),
                     "Avg tone": round(series["avg_tone"].mean(), 2),
                     "Articles": int(series["article_volume"].sum())})

    if not rows:
        st.warning("No data for the current selection.")
        return

    fig.add_hline(y=0, line_dash="dot", line_color=common.NEUTRAL)
    common.add_event_markers(fig, events, x_min=base["week_start"].min(),
                             x_max=base["week_start"].max(),
                             country=None if country == "__all__" else country)
    fig.update_layout(height=460, margin=dict(t=40, b=10),
                      yaxis_title="Media coverage tone (−100 … +100)",
                      xaxis_title="Week", hovermode="x unified",
                      legend=dict(orientation="h", yanchor="bottom", y=1.02))
    st.plotly_chart(fig, use_container_width=True)

    import pandas as pd
    st.dataframe(pd.DataFrame(rows).sort_values("Avg tone", ascending=False),
                 use_container_width=True, hide_index=True)
    st.caption(common.DISCLAIMER)
