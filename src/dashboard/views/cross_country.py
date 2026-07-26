"""Cross-country comparison — same entity/theme across countries on one chart."""
from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from src.dashboard import common


def render() -> None:
    scores = common.require_data()
    common.synthetic_banner(scores)
    wl = common.get_watchlist()
    events = common.get_events()

    st.subheader("🌐 Cross-country comparison")
    st.caption("How does coverage tone for one entity/issue differ **across "
               "countries**? (Domestic vs foreign framing often diverges.)")

    entity_id = st.sidebar.selectbox(
        "Entity / issue", wl.entity_ids,
        format_func=lambda e: wl.name_by_entity.get(e, e), key="cc_entity")
    ent_rows = scores[scores["entity_id"] == entity_id]

    avail = sorted(ent_rows["country"].unique(),
                   key=lambda c: wl.name_by_gdelt.get(c, c))
    # default: the entity's home country + a few high-volume others
    home = wl.entity_by_id(entity_id).home_country if wl.entity_by_id(entity_id) else None
    top = (ent_rows.groupby("country")["article_volume"].sum()
           .sort_values(ascending=False).index.tolist())
    default = [c for c in ([home] if home in avail else []) if c]
    default += [c for c in top if c not in default][:5 - len(default)]
    sel = st.sidebar.multiselect(
        "Countries", avail, default=default or avail[:4],
        format_func=lambda c: wl.name_by_gdelt.get(c, c), key="cc_countries")

    weeks = sorted(ent_rows["week_start"].dt.date.unique())
    w0, w1 = (st.sidebar.select_slider(
        "Time window", options=weeks, value=(weeks[0], weeks[-1]), key="cc_win")
        if len(weeks) > 1 else (weeks[0], weeks[0]))

    view = ent_rows[ent_rows["country"].isin(sel)
                    & (ent_rows["week_start"].dt.date >= w0)
                    & (ent_rows["week_start"].dt.date <= w1)]
    st.markdown(f"**{wl.name_by_entity.get(entity_id, entity_id)}** — coverage tone by country")

    if view.empty or not sel:
        st.warning("Pick at least one country with data.")
        return

    fig = go.Figure()
    for country in sel:
        cdf = view[view["country"] == country].sort_values("week_start")
        if not cdf.empty:
            fig.add_trace(go.Scatter(
                x=cdf["week_start"], y=cdf["avg_tone"], mode="lines+markers",
                name=wl.name_by_gdelt.get(country, country)))
    fig.add_hline(y=0, line_dash="dot", line_color=common.NEUTRAL)
    common.add_event_markers(fig, events, x_min=view["week_start"].min(),
                             x_max=view["week_start"].max(), entity_id=entity_id)
    fig.update_layout(height=460, margin=dict(t=40, b=10),
                      yaxis_title="Media coverage tone (−100 … +100)",
                      xaxis_title="Week", hovermode="x unified",
                      legend=dict(orientation="h", yanchor="bottom", y=1.02))
    st.plotly_chart(fig, use_container_width=True)

    # compact per-country summary (mean tone in window)
    summ = (view.groupby("country").apply(
        lambda g: (g["avg_tone"] * g["article_volume"]).sum()
        / max(g["article_volume"].sum(), 1), include_groups=False)
        .rename("Avg tone").reset_index())
    summ["Country"] = summ["country"].map(wl.name_by_gdelt)
    st.dataframe(summ[["Country", "Avg tone"]].sort_values("Avg tone").round(2),
                 use_container_width=True, hide_index=True)

    st.caption(common.DISCLAIMER)
