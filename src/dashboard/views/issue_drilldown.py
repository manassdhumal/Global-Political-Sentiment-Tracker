"""Issue drill-down — which countries are most associated with a theme, and how."""
from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from src.analytics import issue_association
from src.dashboard import common


def render() -> None:
    scores = common.require_data()
    common.synthetic_banner(scores)
    wl = common.get_watchlist()

    st.subheader("🔎 Issue drill-down")
    st.caption("For an issue, which countries cover it most — and with what "
               "tone? Volume shows attention; tone shows how it's framed.")

    themes = [e.id for e in wl.entities if e.type == "theme"] or wl.entity_ids
    theme_id = st.sidebar.selectbox(
        "Issue / theme", themes,
        format_func=lambda e: wl.name_by_entity.get(e, e), key="id_theme")

    weeks = sorted(scores["week_start"].dt.date.unique())
    w0, w1 = (st.sidebar.select_slider(
        "Time window", options=weeks, value=(weeks[0], weeks[-1]), key="id_win")
        if len(weeks) > 1 else (weeks[0], weeks[0]))
    top_n = st.sidebar.slider("Show top N countries", 5, 26, 12, key="id_topn")

    view = scores[(scores["entity_id"] == theme_id)
                  & (scores["week_start"].dt.date >= w0)
                  & (scores["week_start"].dt.date <= w1)]
    st.markdown(f"**{wl.name_by_entity.get(theme_id, theme_id)}** — coverage by country")

    if view.empty:
        st.warning("No data for the current selection.")
        return

    summary = issue_association(view)
    summary["Country"] = summary["country"].map(wl.name_by_gdelt)
    ranked = summary.head(top_n)

    # Ranked by mention volume, bars colored by tone (red neg / blue pos)
    fig = go.Figure(go.Bar(
        x=ranked["article_volume"], y=ranked["Country"], orientation="h",
        marker=dict(color=ranked["avg_tone"], colorscale="RdBu", cmid=0,
                    colorbar=dict(title="Tone")),
        text=[f"{t:+.1f}" for t in ranked["avg_tone"]], textposition="outside",
        hovertemplate="%{y}<br>Articles: %{x:,}<br>Tone: %{marker.color:+.2f}"
                      "<extra></extra>"))
    fig.update_layout(height=max(300, 26 * len(ranked)),
                      margin=dict(t=20, b=10, l=10),
                      xaxis_title="Article volume (attention)",
                      yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig, use_container_width=True)

    c1, c2 = st.columns(2)
    c1.metric("Countries covering this issue", f"{summary['country'].notna().sum()}")
    c2.metric("Total articles (window)", f"{int(summary['article_volume'].sum()):,}")

    with st.expander("Full ranking table"):
        show = summary.rename(columns={
            "avg_tone": "Avg tone", "article_volume": "Articles",
            "source_diversity": "Outlets", "low_conf_weeks": "Low-conf weeks"})
        st.dataframe(
            show[["Country", "Articles", "Avg tone", "Outlets", "Low-conf weeks"]],
            use_container_width=True, hide_index=True)

    st.caption(common.DISCLAIMER)
