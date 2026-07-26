"""Exportable reports — markdown + PDF summary for an entity or country."""
from __future__ import annotations

import streamlit as st

from src.reporting import build_summary, to_markdown, to_pdf_bytes
from src.dashboard import common


def render() -> None:
    scores = common.require_data()
    common.synthetic_banner(scores)
    wl = common.get_watchlist()
    events = common.get_events()
    synthetic = scores.attrs.get("n_synth", 0) > 0

    st.subheader("📄 Exportable reports")
    st.caption("Generate a shareable media-sentiment summary for an entity or a "
               "country over a date range — as Markdown or PDF.")

    scope = st.sidebar.radio("Report scope", ["Entity", "Country"], key="rp_scope")
    if scope == "Entity":
        scope_key = "entity"
        sid = st.sidebar.selectbox("Entity", wl.entity_ids,
                                   format_func=lambda e: wl.name_by_entity.get(e, e),
                                   key="rp_entity")
        label = wl.name_by_entity.get(sid, sid)
    else:
        scope_key = "country"
        sid = st.sidebar.selectbox("Country", wl.gdelt_country_codes,
                                   format_func=lambda c: wl.name_by_gdelt.get(c, c),
                                   key="rp_country")
        label = wl.name_by_gdelt.get(sid, sid)

    weeks = sorted(scores["week_start"].dt.date.unique())
    w0, w1 = (st.sidebar.select_slider("Date range", options=weeks,
                                       value=(weeks[0], weeks[-1]), key="rp_win")
              if len(weeks) > 1 else (weeks[0], weeks[0]))

    summary = build_summary(
        scores, scope=scope_key, scope_id=sid, scope_label=label, w0=w0, w1=w1,
        name_by_gdelt=wl.name_by_gdelt, name_by_entity=wl.name_by_entity,
        events=events, synthetic=synthetic)

    md = to_markdown(summary)
    st.markdown("#### Preview")
    st.markdown(md)

    safe = "".join(c if c.isalnum() else "_" for c in label).strip("_").lower()
    fname = f"report_{scope_key}_{safe}_{w0}_{w1}"
    c1, c2 = st.columns(2)
    c1.download_button("⬇ Download Markdown", md, file_name=f"{fname}.md",
                       mime="text/markdown", use_container_width=True)
    try:
        pdf = to_pdf_bytes(summary)
        c2.download_button("⬇ Download PDF", pdf, file_name=f"{fname}.pdf",
                           mime="application/pdf", use_container_width=True)
    except Exception as exc:
        c2.warning(f"PDF unavailable ({type(exc).__name__}). Markdown works.")
