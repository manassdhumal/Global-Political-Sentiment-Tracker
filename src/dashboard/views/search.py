"""Global search across tracked entities and themes."""
from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from src.analytics import weekly_weighted_series
from src.dashboard import common


def render() -> None:
    scores = common.require_data()
    wl = common.get_watchlist()

    st.subheader("🔍 Search tracked entities & themes")
    st.caption("Find any tracked figure, party or issue by name or alias, and see "
               "its current media-coverage tone at a glance.")

    q = st.text_input("Search", placeholder="e.g. Modi, climate, inflation, party…",
                      key="search_q").strip().lower()

    matches = []
    for e in wl.entities:
        haystack = " ".join([e.id, e.name, e.type] + list(e.aliases)).lower()
        if not q or q in haystack:
            matches.append(e)

    if q and not matches:
        st.warning(f"No tracked entities match “{q}”. "
                   "Add it to config/watchlist.yaml and re-run the pipeline.")
        return

    st.caption(f"{len(matches)} match{'es' if len(matches) != 1 else ''}"
               + (f" for “{q}”" if q else " (showing all)"))

    for e in matches:
        ent = scores[scores["entity_id"] == e.id]
        series = weekly_weighted_series(ent)
        with st.container(border=True):
            c1, c2, c3 = st.columns([3, 2, 4])
            with c1:
                st.markdown(f"**{e.name}**")
                st.caption(f"`{e.type}`"
                           + (f" · home {wl.name_by_gdelt.get(e.home_country, e.home_country)}"
                              if e.home_country else "")
                           + (f" · aka {', '.join(e.aliases)}" if e.aliases else ""))
            if not series.empty:
                latest = float(series["avg_tone"].iloc[-1])
                first = float(series["avg_tone"].iloc[0])
                c2.metric("Latest tone", f"{latest:+.2f}", f"{latest - first:+.2f}")
                spark = go.Figure(go.Scatter(
                    x=series["week_start"], y=series["avg_tone"], mode="lines",
                    line=dict(color=common.tone_color(latest), width=2)))
                spark.update_layout(height=70, margin=dict(t=5, b=5, l=5, r=5),
                                    xaxis=dict(visible=False),
                                    yaxis=dict(visible=False))
                c3.plotly_chart(spark, use_container_width=True,
                                key=f"spark_{e.id}")
            else:
                c2.caption("No data yet")

    st.caption(common.DISCLAIMER)
