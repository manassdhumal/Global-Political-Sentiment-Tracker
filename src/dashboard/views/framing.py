"""Cross-language framing view — domestic vs foreign, and tone by language."""
from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from src import storage
from src.analytics import domestic_vs_foreign, by_language
from src.dashboard import common


def render() -> None:
    scores = common.require_data()
    common.synthetic_banner(scores)
    wl = common.get_watchlist()

    st.subheader("🗣️ Cross-language framing")
    st.caption("Same entity, different presses. Compares **domestic vs foreign** "
               "coverage and tone **by language**. Differences are in MEDIA "
               "FRAMING across outlets — not in what populations believe. "
               "Translation of non-English coverage can itself shift tone.")

    entity_id = st.sidebar.selectbox(
        "Entity", wl.entity_ids,
        format_func=lambda e: wl.name_by_entity.get(e, e), key="fr_entity")
    weeks = sorted(scores["week_start"].dt.date.unique())
    w0, w1 = (st.sidebar.select_slider(
        "Time window", options=weeks, value=(weeks[0], weeks[-1]), key="fr_win")
        if len(weeks) > 1 else (weeks[0], weeks[0]))

    ent = wl.entity_by_id(entity_id)
    home = ent.home_country if ent else None
    st.markdown(f"**{wl.name_by_entity.get(entity_id, entity_id)}** — framing "
                f"(home country: {wl.name_by_gdelt.get(home, '—') if home else 'none (theme)'})")

    # --- domestic vs foreign (from country-level aggregated_scores) ---
    ent_rows = scores[(scores["entity_id"] == entity_id)
                      & (scores["week_start"].dt.date >= w0)
                      & (scores["week_start"].dt.date <= w1)]
    dvf = domestic_vs_foreign(ent_rows, home)

    c1, c2, c3 = st.columns(3)
    c1.metric("Domestic press tone",
              "—" if dvf["domestic_tone"] is None else f"{dvf['domestic_tone']:+.2f}",
              f"{dvf['domestic_vol']:,} articles")
    c2.metric("Foreign press tone",
              "—" if dvf["foreign_tone"] is None else f"{dvf['foreign_tone']:+.2f}",
              f"{dvf['foreign_vol']:,} articles")
    c3.metric("Framing gap (domestic − foreign)",
              "—" if dvf["gap"] is None else f"{dvf['gap']:+.2f}",
              help="Positive = home press covers this entity more warmly than "
                   "foreign press.")
    if home is None:
        st.info("This is a cross-cutting theme with no home country, so only the "
                "by-language breakdown below applies.")

    # --- by language (from the articles table) ---
    conn = storage.connect(common.db_path())
    try:
        lang = by_language(storage.read_language_summary(
            conn, entity_id, str(w0), str(w1)))
    finally:
        conn.close()

    if lang.empty:
        st.warning("No article-level language data for this selection.")
        return

    st.markdown("**Coverage tone by source language**")
    fig = go.Figure(go.Bar(
        x=lang["avg_tone"], y=lang["language"], orientation="h",
        marker=dict(color=lang["avg_tone"], colorscale="RdBu", cmid=0),
        text=[f"{t:+.1f} (n={n:,})" for t, n in zip(lang["avg_tone"], lang["n"])],
        textposition="outside",
        hovertemplate="%{y}<br>Tone: %{x:+.2f}<extra></extra>"))
    fig.add_vline(x=0, line_dash="dot", line_color=common.NEUTRAL)
    fig.update_layout(height=max(300, 26 * len(lang)), margin=dict(t=10, b=10),
                      xaxis_title="Media coverage tone (−100 … +100)",
                      yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig, use_container_width=True)

    if lang["low_confidence"].any():
        thin = ", ".join(lang.loc[lang["low_confidence"], "language"])
        st.caption(f"⚠ Low-confidence (thin coverage): {thin}")

    st.caption(common.DISCLAIMER)
