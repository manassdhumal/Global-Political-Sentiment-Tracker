"""World map view — choropleth of average media coverage tone per country."""
from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from src.analytics import country_tone_summary
from src.dashboard import common


def _window_slider(scores):
    weeks = sorted(scores["week_start"].dt.date.unique())
    if len(weeks) > 1:
        return st.select_slider("Date range", options=weeks,
                                value=(weeks[0], weeks[-1]))
    return (weeks[0], weeks[0])


def render() -> None:
    scores = common.require_data()
    common.synthetic_banner(scores)
    wl = common.get_watchlist()

    st.subheader("🗺️ World map — average media coverage tone")
    st.caption("Choropleth colored by the volume-weighted average **tone of news "
               "coverage** per country for the selected entity and date range. "
               "Blue = more positive coverage, red = more negative.")

    # --- controls ---
    c1, c2 = st.columns([2, 3])
    with c1:
        entity_opts = ["__all__"] + wl.entity_ids
        entity_id = st.selectbox(
            "Entity", entity_opts,
            format_func=lambda e: "All entities (combined)"
            if e == "__all__" else wl.name_by_entity.get(e, e))
    with c2:
        w0, w1 = _window_slider(scores)

    view = scores[(scores["week_start"].dt.date >= w0)
                  & (scores["week_start"].dt.date <= w1)]
    if entity_id != "__all__":
        view = view[view["entity_id"] == entity_id]

    if view.empty:
        st.warning("No data for the current selection.")
        return

    summary = country_tone_summary(view)
    summary["country_name"] = summary["country"].map(wl.name_by_gdelt)
    summary["iso3"] = summary["country"].map(wl.iso3_by_gdelt)

    # symmetric color scale centered on neutral (0)
    clip = max(1.0, float(summary["avg_tone"].abs().max()))

    hover = [
        f"<b>{r.country_name}</b><br>"
        f"Avg tone: {r.avg_tone:+.2f}<br>"
        f"Articles: {r.article_volume:,}<br>"
        f"Outlets: {r.source_diversity}<br>"
        f"Low-confidence weeks: {r.low_conf_weeks}/{r.n_weeks}"
        for r in summary.itertuples(index=False)
    ]
    fig = go.Figure(go.Choropleth(
        locations=summary["iso3"], z=summary["avg_tone"], locationmode="ISO-3",
        colorscale="RdBu", zmid=0, zmin=-clip, zmax=clip,
        marker_line_color="white", marker_line_width=0.4,
        colorbar_title="Tone", text=hover, hoverinfo="text"))
    fig.update_layout(height=520, margin=dict(t=10, b=0, l=0, r=0),
                      geo=dict(showframe=False, projection_type="natural earth"))
    st.plotly_chart(fig, use_container_width=True)

    # --- summary metrics + extremes ---
    glob = (view["avg_tone"] * view["article_volume"]).sum() / max(
        view["article_volume"].sum(), 1)
    m1, m2, m3 = st.columns(3)
    m1.metric("Global avg tone (selection)", f"{glob:+.2f}")
    most_neg = summary.iloc[0]
    most_pos = summary.iloc[-1]
    m2.metric("Most negative coverage", most_neg["country_name"],
              f"{most_neg['avg_tone']:+.2f}", delta_color="inverse")
    m3.metric("Most positive coverage", most_pos["country_name"],
              f"{most_pos['avg_tone']:+.2f}")

    with st.expander("Per-country table"):
        show = summary.rename(columns={
            "country_name": "Country", "avg_tone": "Avg tone",
            "article_volume": "Articles", "source_diversity": "Outlets",
            "low_conf_weeks": "Low-conf weeks", "n_weeks": "Weeks"})
        st.dataframe(
            show[["Country", "Avg tone", "Articles", "Outlets",
                  "Low-conf weeks", "Weeks"]].sort_values("Avg tone"),
            use_container_width=True, hide_index=True)

    st.caption(common.DISCLAIMER)
