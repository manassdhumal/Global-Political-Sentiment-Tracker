"""Executive PDF Intelligence Dossier Exporter using fpdf2."""
from __future__ import annotations

import io
from datetime import datetime, timezone
from typing import Any
from fpdf import FPDF

from src.analytics.analyst_agent import generate_analyst_dossier
from src.topics.catalog import resolve_topic
from src.topics.synth import global_weekly


class IntelligenceMemoPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(120, 120, 130)
        self.cell(0, 5, "GLOBAL POLITICAL SENTIMENT TRACKER // EXECUTIVE INTELLIGENCE MEMORANDUM", ln=True, align="L")
        self.set_draw_color(200, 200, 210)
        self.line(10, 15, 200, 15)
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(140, 140, 150)
        self.cell(0, 4, "STRICTLY ANALYTICAL · MEDIA/SOCIAL TONE TELEMETRY · NOT PUBLIC OPINION", ln=True, align="C")
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
    pdf.cell(0, 7, "  CLASSIFICATION: OPEN-SOURCE QUANTITATIVE INTELLIGENCE", ln=True, fill=True)
    pdf.ln(3)

    # Memo Meta Table
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(15, 23, 42)
    pdf.multi_cell(0, 7, f"SPECIAL BRIEFING: {dossier['topic']['label'].upper()}")
    pdf.ln(2)

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(70, 80, 95)
    pdf.cell(50, 5, f"Date: {now_str}", ln=False)
    pdf.cell(50, 5, f"Category: {topic.category.upper()}", ln=False)
    pdf.cell(50, 5, f"Net Tone: {dossier['latest_tone']:+.2f}", ln=False)
    pdf.cell(0, 5, f"Engine: {dossier['source'].upper()}", ln=True)
    pdf.ln(4)

    # BLUF Box
    pdf.set_fill_color(238, 242, 255)  # Light Indigo
    pdf.set_draw_color(99, 102, 241)   # Indigo border
    pdf.set_line_width(0.4)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(67, 56, 202)
    pdf.cell(0, 6, "  BOTTOM LINE UP FRONT (BLUF)", ln=True, fill=True, border=1)
    
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(30, 41, 59)
    pdf.set_fill_color(248, 250, 252)
    bluf_text = f"\n{dossier['bluf']}\n"
    pdf.multi_cell(0, 5, bluf_text, fill=True, border=1)
    pdf.ln(4)

    # Causal Drivers Table
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 6, "1. CAUSAL DRIVERS & MEDIA NARRATIVE PRESSURES", ln=True)
    pdf.ln(1)

    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(241, 245, 249)
    pdf.set_draw_color(203, 213, 225)
    pdf.cell(55, 6, "DRIVER TITLE", 1, 0, "L", True)
    pdf.cell(25, 6, "IMPACT", 1, 0, "C", True)
    pdf.cell(110, 6, "ANALYTICAL DESCRIPTION", 1, 1, "L", True)

    pdf.set_font("Helvetica", "", 8)
    for drv in dossier.get("drivers", []):
        pdf.cell(55, 6, str(drv["title"])[:30], 1, 0, "L")
        pdf.cell(25, 6, str(drv["impact"]), 1, 0, "C")
        pdf.cell(110, 6, str(drv["description"])[:70], 1, 1, "L")
    pdf.ln(4)

    # Stakeholder Power Matrix
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 6, "2. PRIMARY STAKEHOLDER MATRIX", ln=True)
    pdf.ln(1)

    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(241, 245, 249)
    pdf.cell(50, 6, "STAKEHOLDER", 1, 0, "L", True)
    pdf.cell(30, 6, "POWER", 1, 0, "C", True)
    pdf.cell(30, 6, "STANCE", 1, 0, "C", True)
    pdf.cell(80, 6, "LEVERAGE & TACTICS", 1, 1, "L", True)

    pdf.set_font("Helvetica", "", 8)
    for s in dossier.get("stakeholders", []):
        pdf.cell(50, 6, str(s["actor"])[:28], 1, 0, "L")
        pdf.cell(30, 6, str(s["power"]), 1, 0, "C")
        pdf.cell(30, 6, str(s["stance"])[:18], 1, 0, "C")
        pdf.cell(80, 6, str(s["leverage"])[:48], 1, 1, "L")
    pdf.ln(4)

    # Scenario Forecast Table
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 6, "3. FORWARD SCENARIOS (NEXT 4-6 WEEKS)", ln=True)
    pdf.ln(1)

    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(241, 245, 249)
    pdf.cell(55, 6, "SCENARIO", 1, 0, "L", True)
    pdf.cell(25, 6, "PROBABILITY", 1, 0, "C", True)
    pdf.cell(30, 6, "PROJ. TONE", 1, 0, "C", True)
    pdf.cell(80, 6, "SCENARIO DESCRIPTION", 1, 1, "L", True)

    pdf.set_font("Helvetica", "", 8)
    for sc in dossier.get("scenarios", []):
        pdf.cell(55, 6, str(sc["name"])[:32], 1, 0, "L")
        pdf.cell(25, 6, f"{sc['probability']}%", 1, 0, "C")
        pdf.cell(30, 6, f"{sc['tone_projection']:+.2f}", 1, 0, "C")
        pdf.cell(80, 6, str(sc["description"])[:48], 1, 1, "L")
    pdf.ln(4)

    # Strategic Vulnerabilities
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 6, "4. KEY VULNERABILITIES & SYSTEMIC RISKS", ln=True)
    pdf.ln(1)

    pdf.set_font("Helvetica", "", 8.5)
    for v in dossier.get("vulnerabilities", []):
        pdf.multi_cell(0, 4.5, f"•  {v}")
        pdf.ln(1)

    # Return PDF bytes
    return bytes(pdf.output())
