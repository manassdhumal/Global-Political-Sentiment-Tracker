"""Executive PDF Intelligence Dossier Exporter using fpdf2."""
from __future__ import annotations

import io
import unicodedata
from datetime import datetime, timezone
from typing import Any
from fpdf import FPDF
from fpdf.enums import XPos, YPos

from src.analytics.analyst_agent import generate_analyst_dossier
from src.topics.catalog import resolve_topic


def _sanitize_pdf_text(text: Any) -> str:
    """Normalize and encode unicode strings into standard latin-1 compatible ASCII text."""
    if text is None:
        return ""
    s = str(text)
    replacements = {
        "—": " - ",
        "–": "-",
        "―": "-",
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "•": "*",
        "…": "...",
        "→": "->",
        "←": "<-",
    }
    for old, new in replacements.items():
        s = s.replace(old, new)

    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    return s


class IntelligenceMemoPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(120, 120, 130)
        self.cell(0, 5, "GLOBAL POLITICAL SENTIMENT TRACKER // EXECUTIVE INTELLIGENCE MEMORANDUM", align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_draw_color(200, 200, 210)
        self.line(10, 15, 200, 15)
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(140, 140, 150)
        self.cell(0, 4, "STRICTLY ANALYTICAL · MEDIA/SOCIAL TONE TELEMETRY · NOT PUBLIC OPINION", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.cell(0, 4, f"Page {self.page_no()}/{{nb}}", align="R")


def generate_topic_pdf_dossier(topic_id: str = "us_china") -> bytes:
    """Generate a clean, multi-page PDF briefing document for a topic."""
    dossier = generate_analyst_dossier(topic_id)
    topic = resolve_topic(topic_id)
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    pdf = IntelligenceMemoPDF(orientation="P", unit="mm", format="A4")
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    # Classification Banner
    pdf.set_fill_color(240, 243, 246)
    pdf.set_text_color(30, 41, 59)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, "  CLASSIFICATION: OPEN-SOURCE QUANTITATIVE INTELLIGENCE", fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(3)

    # Memo Meta Table
    pdf.set_font("Helvetica", "B", 15)
    pdf.set_text_color(15, 23, 42)
    label_clean = _sanitize_pdf_text(dossier["topic"]["label"]).upper()
    pdf.multi_cell(0, 7, f"SPECIAL BRIEFING: {label_clean}")
    pdf.ln(2)

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(70, 80, 95)
    pdf.cell(50, 5, f"Date: {now_str}")
    pdf.cell(50, 5, f"Category: {_sanitize_pdf_text(topic.category).upper()}")
    pdf.cell(50, 5, f"Net Tone: {dossier['latest_tone']:+.2f}")
    pdf.cell(0, 5, f"Engine: {_sanitize_pdf_text(dossier['source']).upper()}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)

    # BLUF Box
    pdf.set_fill_color(238, 242, 255)  # Light Indigo
    pdf.set_draw_color(99, 102, 241)   # Indigo border
    pdf.set_line_width(0.4)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(67, 56, 202)
    pdf.cell(0, 6, "  BOTTOM LINE UP FRONT (BLUF)", fill=True, border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(30, 41, 59)
    pdf.set_fill_color(248, 250, 252)
    bluf_clean = _sanitize_pdf_text(dossier["bluf"])
    pdf.multi_cell(0, 5, f"\n{bluf_clean}\n", fill=True, border=1)
    pdf.ln(4)

    # Causal Drivers Table
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 6, "1. CAUSAL DRIVERS & MEDIA NARRATIVE PRESSURES", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(1)

    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(241, 245, 249)
    pdf.set_draw_color(203, 213, 225)
    pdf.cell(55, 6, "DRIVER TITLE", border=1, fill=True)
    pdf.cell(25, 6, "IMPACT", border=1, align="C", fill=True)
    pdf.cell(110, 6, "ANALYTICAL DESCRIPTION", border=1, fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_font("Helvetica", "", 8)
    for drv in dossier.get("drivers", []):
        t_clean = _sanitize_pdf_text(drv["title"])[:30]
        i_clean = _sanitize_pdf_text(drv["impact"])
        d_clean = _sanitize_pdf_text(drv["description"])[:70]
        pdf.cell(55, 6, t_clean, border=1)
        pdf.cell(25, 6, i_clean, border=1, align="C")
        pdf.cell(110, 6, d_clean, border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)

    # Stakeholder Power Matrix
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 6, "2. PRIMARY STAKEHOLDER MATRIX", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(1)

    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(241, 245, 249)
    pdf.cell(50, 6, "STAKEHOLDER", border=1, fill=True)
    pdf.cell(30, 6, "POWER", border=1, align="C", fill=True)
    pdf.cell(30, 6, "STANCE", border=1, align="C", fill=True)
    pdf.cell(80, 6, "LEVERAGE & TACTICS", border=1, fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_font("Helvetica", "", 8)
    for s in dossier.get("stakeholders", []):
        act = _sanitize_pdf_text(s["actor"])[:28]
        pow_val = _sanitize_pdf_text(s["power"])
        stn = _sanitize_pdf_text(s["stance"])[:18]
        lev = _sanitize_pdf_text(s["leverage"])[:48]
        pdf.cell(50, 6, act, border=1)
        pdf.cell(30, 6, pow_val, border=1, align="C")
        pdf.cell(30, 6, stn, border=1, align="C")
        pdf.cell(80, 6, lev, border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)

    # Scenario Forecast Table
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 6, "3. FORWARD SCENARIOS (NEXT 4-6 WEEKS)", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(1)

    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(241, 245, 249)
    pdf.cell(55, 6, "SCENARIO", border=1, fill=True)
    pdf.cell(25, 6, "PROBABILITY", border=1, align="C", fill=True)
    pdf.cell(30, 6, "PROJ. TONE", border=1, align="C", fill=True)
    pdf.cell(80, 6, "SCENARIO DESCRIPTION", border=1, fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_font("Helvetica", "", 8)
    for sc in dossier.get("scenarios", []):
        sc_name = _sanitize_pdf_text(sc["name"])[:32]
        sc_prob = f"{sc['probability']}%"
        sc_tone = f"{sc['tone_projection']:+.2f}"
        sc_desc = _sanitize_pdf_text(sc["description"])[:48]
        pdf.cell(55, 6, sc_name, border=1)
        pdf.cell(25, 6, sc_prob, border=1, align="C")
        pdf.cell(30, 6, sc_tone, border=1, align="C")
        pdf.cell(80, 6, sc_desc, border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)

    # Strategic Vulnerabilities
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 6, "4. KEY VULNERABILITIES & SYSTEMIC RISKS", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(1)

    pdf.set_font("Helvetica", "", 8.5)
    for v in dossier.get("vulnerabilities", []):
        v_clean = _sanitize_pdf_text(v)
        pdf.multi_cell(0, 4.5, f"*  {v_clean}")
        pdf.ln(1)

    # Return PDF bytes
    return bytes(pdf.output())
