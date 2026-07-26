"""Sentiment volatility index — rank the most-swinging entities/countries."""
from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from src.analytics import volatility_index
from src.dashboard import common


_GROUPS = {
    "By entity": "entity",
    "By country": "country",
    "By entity × country": "entity_country",
}


def render() -> None:
    scores = common.require_data()
    common.synthetic_banner(scores)
    wl = common.get_watchlist()

    st.subheader("📊 Sentiment volatility index")
    st.caption("Ranks the most **volatile** coverage — highest week-to-week swing "
               "(standard deviation of weekly tone) over the selected window. "
               "High volatility = coverage tone is unstable, not necessarily bad.")

    group_label = st.sidebar.radio("Group by", list(_GROUPS.keys()), key="vol_group")
    group = _GROUPS[group_label]

    weeks = sorted(scores["week_start"].dt.date.unique())
    w0, w1 = (st.sidebar.select_slider(
        "Time window", options=weeks, value=(weeks[0], weeks[-1]), key="vol_win")
        if len(weeks) > 1 else (weeks[0], weeks[0]))
    min_weeks = st.sidebar.slider("Min weeks required", 2, max(2, len(weeks)),
                                  min(4, len(weeks)), key="vol_minw")
    top_n = st.sidebar.slider("Show top N", 5, 30, 15, key="vol_topn")

    view = scores[(scores["week_start"].dt.date >= w0)
                  & (scores["week_start"].dt.date <= w1)]
    idx = volatility_index(view, group=group, min_weeks=min_weeks)
    if idx.empty:
        st.warning("Not enough data in the window to compute volatility.")
        return

    # readable labels
    def label(row) -> str:
        if group == "entity":
            return wl.name_by_entity.get(row["entity_id"], row["entity_id"])
        if group == "country":
            return wl.name_by_gdelt.get(row["country"], row["country"])
        return (f"{wl.name_by_entity.get(row['entity_id'], row['entity_id'])} · "
                f"{wl.name_by_gdelt.get(row['country'], row['country'])}")

    idx = idx.copy()
    idx["Label"] = idx.apply(label, axis=1)
    ranked = idx.head(top_n)

    fig = go.Figure(go.Bar(
        x=ranked["volatility"], y=ranked["Label"], orientation="h",
        marker_color="#756bb1",
        hovertemplate="%{y}<br>Volatility (σ): %{x:.2f}<extra></extra>"))
    fig.update_layout(height=max(300, 26 * len(ranked)),
                      margin=dict(t=20, b=10),
                      xaxis_title="Volatility — std dev of weekly tone (σ)",
                      yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig, use_container_width=True)

    show = ranked.rename(columns={
        "volatility": "Volatility (σ)", "mean_tone": "Mean tone",
        "tone_range": "Range", "n_weeks": "Weeks", "article_volume": "Articles"})
    display_cols = ["Label", "Volatility (σ)", "Mean tone", "Range",
                    "Weeks", "Articles"]
    st.dataframe(show[display_cols], use_container_width=True, hide_index=True)

    st.caption(common.DISCLAIMER)
