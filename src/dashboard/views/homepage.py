"""'Political mood' homepage — global snapshot + biggest movers + alerts."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.analytics import weekly_weighted_series, detect_anomalies
from src.dashboard import common


@st.cache_data(show_spinner=False)
def _movers_and_alerts(mtime: float):
    """Per-entity latest-week tone, week-over-week delta, and anomaly flag."""
    scores = common.load_scores(mtime)
    rows = []
    for eid, g in scores.groupby("entity_id"):
        series = weekly_weighted_series(g)
        if series.empty:
            continue
        latest = float(series["avg_tone"].iloc[-1])
        prev = float(series["avg_tone"].iloc[-2]) if len(series) > 1 else latest
        anoms = detect_anomalies(series, z_thresh=2.5)
        recent_anom = bool(anoms["is_anomaly"].iloc[-1]) if not anoms.empty else False
        rows.append({"entity_id": eid, "latest": round(latest, 2),
                     "delta": round(latest - prev, 2),
                     "volume": int(g["article_volume"].sum()),
                     "anomaly": recent_anom})
    return pd.DataFrame(rows)


def render() -> None:
    scores = common.require_data()
    common.synthetic_banner(scores)
    wl = common.get_watchlist()

    st.subheader("🏠 Political mood — global snapshot")
    st.caption("A weekly read on the **tone of world news coverage** across all "
               "tracked entities and countries. Media sentiment, not public opinion.")

    # --- global snapshot ---
    latest_week = scores["week_start"].max()
    glob = (scores["avg_tone"] * scores["article_volume"]).sum() / max(
        scores["article_volume"].sum(), 1)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Global coverage tone", f"{glob:+.2f}")
    c2.metric("Articles tracked", f"{int(scores['article_volume'].sum()):,}")
    c3.metric("Entities × countries",
              f"{scores['entity_id'].nunique()} × {scores['country'].nunique()}")
    c4.metric("Latest week", f"{latest_week.date()}")

    md = _movers_and_alerts(common.db_mtime())
    md["name"] = md["entity_id"].map(wl.name_by_entity)

    # --- biggest movers of the week ---
    st.markdown("### 📈 Biggest movers this week")
    st.caption("Largest week-over-week change in coverage tone (latest week vs prior).")
    movers = md[md["delta"].abs() > 0].sort_values("delta", ascending=False)
    gain = movers.head(5)
    loss = movers.sort_values("delta").head(5)

    colu, cold = st.columns(2)
    with colu:
        st.markdown("**Improving coverage ▲**")
        for r in gain.itertuples():
            st.metric(r.name, f"{r.latest:+.2f}", f"{r.delta:+.2f}")
    with cold:
        st.markdown("**Worsening coverage ▼**")
        for r in loss.itertuples():
            st.metric(r.name, f"{r.latest:+.2f}", f"{r.delta:+.2f}")

    # --- overall ranking bar ---
    st.markdown("### 🌡️ Where each entity stands (latest week)")
    rank = md.sort_values("latest")
    fig = go.Figure(go.Bar(
        x=rank["latest"], y=rank["name"], orientation="h",
        marker=dict(color=rank["latest"], colorscale="RdBu", cmid=0),
        hovertemplate="%{y}<br>Tone: %{x:+.2f}<extra></extra>"))
    fig.add_vline(x=0, line_dash="dot", line_color=common.NEUTRAL)
    fig.update_layout(height=max(320, 22 * len(rank)), margin=dict(t=10, b=10),
                      xaxis_title="Latest weekly coverage tone (−100 … +100)",
                      yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig, use_container_width=True)

    # --- alerts ---
    alerts = md[md["anomaly"]]
    if not alerts.empty:
        st.markdown("### ⚠ Early-warning flags")
        st.caption("Entities whose latest week was a statistical anomaly — worth "
                   "a look on the Forecast & alerts page.")
        for r in alerts.sort_values("delta").itertuples():
            st.write(f"- **{r.name}**: {r.latest:+.2f} "
                     f"({r.delta:+.2f} vs prior week)")
    else:
        st.info("No statistical anomalies in the latest week.")

    st.caption(common.DISCLAIMER)
