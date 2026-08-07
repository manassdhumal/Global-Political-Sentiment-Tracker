"""Executive PDF Intelligence Dossier Exporter using fpdf2."""
from __future__ import annotations

import io
from datetime import datetime, timezone
from typing import Any
from fpdf import FPDF

from src.analytics.analyst_agent import generate_geopolitical_dossier
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
    dossier = generate_geopolitical_dossier(topic_id)
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
    pdf.multi_cell(0, 7, f"SPECIAL REPORT: {dossier['topic']['label'].upper()}")
    pdf.ln(2)

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(70, 80, 95)
    pdf.cell(45, 5, f"Date: {now_str}", ln=False)
    pdf.cell(45, 5, f"Category: {topic.category.upper()}", ln=False)
    pdf.cell(45, 5, f"Threat Tier: {dossier['threat_level'].upper()}", ln=False)
    pdf.cell(0, 5, f"Confidence: {dossier['confidence_score']}%", ln=True)
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
    bluf_text = f"\n{dossier['executive_summary']}\n\nKey Focus: {dossier['key_catalysts'][0] if dossier['key_catalysts'] else 'Active geopolitical monitoring'}\n"
    pdf.multi_cell(0, 5, bluf_text, fill=True, border=1)
    pdf.ln(4)

    # Quantitative Telemetry Table
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 6, "1. QUANTITATIVE SENTIMENT & VOLATILITY TELEMETRY", ln=True)
    pdf.ln(1)

    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(241, 245, 249)
    pdf.set_draw_color(203, 213, 225)
    pdf.cell(45, 6, "METRIC", 1, 0, "L", True)
    pdf.cell(35, 6, "VALUE", 1, 0, "C", True)
    pdf.cell(110, 6, "ANALYTICAL INTERPRETATION", 1, 1, "L", True)

    metrics_rows = [
        ("Current Tone", f"{dossier['sentiment_metrics']['tone']:+.2f}", "GDELT media sentiment on a standardized scale (-10 to +10)."),
        ("4-Week Delta", f"{dossier['sentiment_metrics']['momentum_4w']:+.2f}", "Trailing 4-week acceleration in coverage framing."),
        ("Volatility Regime", dossier['sentiment_metrics']['volatility_regime'], "Rolling conditional variance in media reporting."),
        ("Narrative Velocity", f"{dossier['sentiment_metrics']['velocity']} / wk", "Estimated weekly publication frequency index."),
    ]

    pdf.set_font("Helvetica", "", 8)
    for m, v, interp in metrics_rows:
        pdf.cell(45, 6, m, 1, 0, "L")
        pdf.cell(35, 6, v, 1, 0, "C")
        pdf.cell(110, 6, interp, 1, 1, "L")
    pdf.ln(4)

    # Stakeholder Power Matrix
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 6, "2. PRIMARY STAKEHOLDER MATRIX", ln=True)
    pdf.ln(1)

    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(241, 245, 249)
    pdf.cell(45, 6, "STAKEHOLDER", 1, 0, "L", True)
    pdf.cell(30, 6, "INFLUENCE", 1, 0, "C", True)
    pdf.cell(30, 6, "POSTURE", 1, 0, "C", True)
    pdf.cell(85, 6, "STRATEGIC OBJECTIVE", 1, 1, "L", True)

    pdf.set_font("Helvetica", "", 8)
    for s in dossier["stakeholders"]:
        pdf.cell(45, 6, str(s["name"]), 1, 0, "L")
        pdf.cell(30, 6, str(s["power"]), 1, 0, "C")
        pdf.cell(30, 6, str(s["alignment"]), 1, 0, "C")
        pdf.cell(85, 6, str(s["objective"])[:55], 1, 1, "L")
    pdf.ln(4)

    # Scenario Forecast Table
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 6, "3. FORWARD SCENARIOS & PROBABILITY MATRIX", ln=True)
    pdf.ln(1)

    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(241, 245, 249)
    pdf.cell(45, 6, "SCENARIO", 1, 0, "L", True)
    pdf.cell(25, 6, "PROBABILITY", 1, 0, "C", True)
    pdf.cell(120, 6, "POTENTIAL IMPACT & CATALYSTS", 1, 1, "L", True)

    pdf.set_font("Helvetica", "", 8)
    for sc in dossier["scenario_forecasts"]:
        pdf.cell(45, 6, str(sc["scenario"]), 1, 0, "L")
        pdf.cell(25, 6, f"{sc['probability']}%", 1, 0, "C")
        pdf.cell(120, 6, str(sc["impact"])[:75], 1, 1, "L")
    pdf.ln(4)

    # Strategic Recommendation
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 6, "4. STRATEGIC PLAYBOOK & MONITORING ACTIONS", ln=True)
    pdf.ln(1)

    pdf.set_font("Helvetica", "", 8.5)
    for rec in dossier.get("recommendations", []):
        pdf.multi_cell(0, 4.5, f"•  {rec}")
        pdf.ln(1)

    # Return PDF bytes
    return bytes(pdf.output())
