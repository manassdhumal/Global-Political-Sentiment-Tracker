"""Build exportable summaries (markdown + PDF) for an entity or a country.

A summary is a plain dict so both renderers work from the same data. PDF uses
fpdf2 (pure-Python). Every report repeats the media-sentiment framing + caveats.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from ..analytics import weekly_weighted_series, country_tone_summary

_FRAMING = ("This report measures the TONE OF NEWS COVERAGE (GDELT-style, "
            "-100..+100) — i.e. media sentiment, NOT public opinion. Coverage "
            "can be sparse for smaller countries/languages (flagged "
            "low-confidence); translation, sarcasm and outlet bias affect tone.")


def build_summary(scores: pd.DataFrame, *, scope: str, scope_id: str,
                  scope_label: str, w0, w1,
                  name_by_gdelt: dict, name_by_entity: dict,
                  events: list | None = None, synthetic: bool = False) -> dict:
    """scope: 'entity' or 'country'. scores must already be the enriched frame."""
    win = scores[(scores["week_start"].dt.date >= w0)
                 & (scores["week_start"].dt.date <= w1)]
    if scope == "entity":
        sub = win[win["entity_id"] == scope_id]
    else:
        sub = win[win["country"] == scope_id]

    series = weekly_weighted_series(sub)
    if series.empty:
        return {"empty": True, "scope": scope, "scope_label": scope_label,
                "window": (str(w0), str(w1))}

    first, last = series["avg_tone"].iloc[0], series["avg_tone"].iloc[-1]
    overall = float((sub["avg_tone"] * sub["article_volume"]).sum()
                    / max(sub["article_volume"].sum(), 1))

    # breakdown: entity -> by country; country -> by entity
    if scope == "entity":
        bd = country_tone_summary(sub)
        bd["label"] = bd["country"].map(name_by_gdelt)
    else:
        rows = []
        for eid, g in sub.groupby("entity_id"):
            rows.append({"label": name_by_entity.get(eid, eid),
                         "avg_tone": float((g["avg_tone"] * g["article_volume"]).sum()
                                           / max(g["article_volume"].sum(), 1)),
                         "article_volume": int(g["article_volume"].sum())})
        bd = pd.DataFrame(rows).sort_values("avg_tone")

    ev_in = []
    for e in (events or []):
        d = pd.to_datetime(e.date).date()
        if w0 <= d <= w1:
            ev_in.append((e.date, e.label))

    return {
        "empty": False,
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "scope": scope, "scope_label": scope_label,
        "window": (str(w0), str(w1)),
        "overall_tone": round(overall, 2),
        "trend_delta": round(float(last - first), 2),
        "latest_tone": round(float(last), 2),
        "total_articles": int(sub["article_volume"].sum()),
        "max_diversity": int(sub["source_diversity"].max()),
        "low_conf_weeks": int(sub["low_confidence"].sum()),
        "n_weeks": int(sub["week_start"].nunique()),
        "most_positive": (bd.iloc[-1]["label"], round(float(bd.iloc[-1]["avg_tone"]), 2)),
        "most_negative": (bd.iloc[0]["label"], round(float(bd.iloc[0]["avg_tone"]), 2)),
        "breakdown": bd[["label", "avg_tone", "article_volume"]].to_dict("records"),
        "events": ev_in,
        "synthetic": synthetic,
    }


def to_markdown(s: dict) -> str:
    if s.get("empty"):
        return (f"# {s['scope_label']} — media sentiment report\n\n"
                f"No data in window {s['window'][0]} → {s['window'][1]}.\n")
    L = [f"# {s['scope_label']} — media sentiment report",
         f"_Generated {s['generated']} · window {s['window'][0]} → {s['window'][1]}_",
         ""]
    if s["synthetic"]:
        L.append("> ⚠ **Synthetic (fabricated) data** — demo only, not real coverage.\n")
    L += [
        "## Summary",
        f"- **Average coverage tone:** {s['overall_tone']:+.2f}",
        f"- **Latest week:** {s['latest_tone']:+.2f} "
        f"(**{s['trend_delta']:+.2f}** over the window)",
        f"- **Articles:** {s['total_articles']:,} over {s['n_weeks']} weeks",
        f"- **Max source diversity:** {s['max_diversity']} outlets",
        f"- **Low-confidence weeks:** {s['low_conf_weeks']} (thin coverage)",
        f"- **Most positive:** {s['most_positive'][0]} ({s['most_positive'][1]:+.2f})",
        f"- **Most negative:** {s['most_negative'][0]} ({s['most_negative'][1]:+.2f})",
        "",
        "## Breakdown",
        "| " + ("Country" if s["scope"] == "entity" else "Entity")
        + " | Avg tone | Articles |",
        "|---|---:|---:|",
    ]
    for r in s["breakdown"]:
        L.append(f"| {r['label']} | {r['avg_tone']:+.2f} | {int(r['article_volume']):,} |")
    if s["events"]:
        L += ["", "## Events in window"]
        L += [f"- {d}: {lab}" for d, lab in s["events"]]
    L += ["", "## Methodology & limitations", _FRAMING, ""]
    return "\n".join(L)


def to_pdf_bytes(s: dict) -> bytes:
    """Render the summary to a simple PDF via fpdf2."""
    from fpdf import FPDF
    from fpdf.enums import XPos, YPos

    def clean(t: str) -> str:
        # fpdf core fonts are latin-1; drop unsupported glyphs safely.
        return str(t).encode("latin-1", "replace").decode("latin-1")

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    def mc(text: str, h: float = 6) -> None:
        # full-width line that resets to the left margin on the next line
        pdf.multi_cell(0, h, clean(text),
                       new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_font("Helvetica", "B", 16)
    mc(f"{s.get('scope_label','')} - media sentiment report", 9)
    pdf.set_font("Helvetica", "", 9)
    if s.get("empty"):
        mc(f"No data in window {s['window'][0]} -> {s['window'][1]}.")
        return bytes(pdf.output())

    mc(f"Generated {s['generated']} | window {s['window'][0]} -> {s['window'][1]}")
    if s["synthetic"]:
        pdf.set_text_color(180, 60, 0)
        mc("SYNTHETIC (fabricated) data - demo only.")
        pdf.set_text_color(0, 0, 0)
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 12); mc("Summary", 8)
    pdf.set_font("Helvetica", "", 10)
    for line in [
        f"Average coverage tone: {s['overall_tone']:+.2f}",
        f"Latest week: {s['latest_tone']:+.2f} ({s['trend_delta']:+.2f} over window)",
        f"Articles: {s['total_articles']:,} over {s['n_weeks']} weeks",
        f"Max source diversity: {s['max_diversity']} outlets",
        f"Low-confidence weeks: {s['low_conf_weeks']}",
        f"Most positive: {s['most_positive'][0]} ({s['most_positive'][1]:+.2f})",
        f"Most negative: {s['most_negative'][0]} ({s['most_negative'][1]:+.2f})",
    ]:
        mc("- " + line)

    pdf.ln(1); pdf.set_font("Helvetica", "B", 12); mc("Breakdown", 8)
    pdf.set_font("Helvetica", "", 9)
    head = "Country" if s["scope"] == "entity" else "Entity"
    pdf.cell(90, 6, clean(head), border=1)
    pdf.cell(35, 6, "Avg tone", border=1)
    pdf.cell(35, 6, "Articles", border=1,
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    for r in s["breakdown"]:
        pdf.cell(90, 6, clean(r["label"])[:45], border=1)
        pdf.cell(35, 6, f"{r['avg_tone']:+.2f}", border=1)
        pdf.cell(35, 6, f"{int(r['article_volume']):,}", border=1,
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    if s["events"]:
        pdf.ln(1); pdf.set_font("Helvetica", "B", 12); mc("Events in window", 8)
        pdf.set_font("Helvetica", "", 10)
        for d, lab in s["events"]:
            mc(f"- {d}: {lab}")

    pdf.ln(2); pdf.set_font("Helvetica", "I", 8)
    mc(_FRAMING, 5)
    return bytes(pdf.output())
