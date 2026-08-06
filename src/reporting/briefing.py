"""Executive Intelligence Briefing Generator for Geopolitical & Sentiment Analysis."""
from __future__ import annotations

from datetime import datetime, timezone
import numpy as np

from src.topics.analyze import analyze_topic
from src.topics.trending import global_snapshot, catalog_stats


def _calculate_risk_rating(data: dict) -> tuple[str, str, str]:
    """Calculate executive risk rating, badge color, and rationale from sentiment metrics."""
    avg_gap = abs(data.get("avg_gap") or 0.0)
    anomalies_count = len(data.get("anomalies", []))
    fc_points = data.get("forecast", {}).get("points", [])
    
    # Calculate historical variance
    hist = [r["avg_tone"] for r in data.get("media_series", []) if r.get("avg_tone") is not None]
    hist_std = float(np.std(hist)) if len(hist) > 1 else 1.0

    risk_score = (anomalies_count * 1.5) + (avg_gap * 0.4) + (hist_std * 0.8)

    if risk_score >= 8.0:
        return "HIGH RISK / CRITICAL VOLATILITY", "#ef4444", "Severe public-media divergence, multiple detected anomalies, and elevated sentiment variance."
    elif risk_score >= 5.0:
        return "ELEVATED RISK / ACTIVE SHIFT", "#f59e0b", "Noticeable sentiment shifts and moderate divergence between media framing and public opinion."
    elif risk_score >= 3.0:
        return "MODERATE VOLATILITY", "#38bdf8", "Normal cyclical coverage fluctuations within expected confidence bounds."
    else:
        return "LOW RISK / STABLE", "#10b981", "Consistent sentiment trajectory with minimal divergence and low volatility."


def generate_topic_briefing_markdown(data: dict) -> str:
    """Produce an executive-ready Markdown intelligence briefing."""
    topic = data["topic"]
    stats = data["stats"]
    narrative = data["narrative"]
    risk_label, _, risk_rationale = _calculate_risk_rating(data)
    now_str = datetime.now(timezone.utc).strftime("%B %d, %Y - %H:%M UTC")

    md = []
    md.append(f"# 🛡️ GEOPOLITICAL INTELLIGENCE BRIEFING: {topic['label'].upper()}")
    md.append(f"**Classification:** Open Source Intelligence (OSINT) • **Generated:** {now_str}")
    md.append(f"**Tracking Inception:** {data['inception']} ({data['age_weeks']} weeks of history) | **Category:** {topic['category']}")
    md.append("\n---\n")

    # 1. Executive Summary & Risk Status
    md.append("## 1. Executive Summary & Volatility Rating")
    md.append(f"**Strategic Risk Rating:** `{risk_label}`")
    md.append(f"> {risk_rationale}\n")
    md.append(f"**Headline:** {narrative['headline']}")
    md.append(f"\n{narrative['summary']}\n")

    if narrative.get("points"):
        md.append("### Key Takeaways")
        for pt in narrative["points"]:
            md.append(f"* {pt}")
        md.append("")

    # 2. Key Metrics Table
    md.append("## 2. Quantitative Sentiment Indicators")
    md.append("| Metric | Value | Reference / Benchmark |")
    md.append("| :--- | :--- | :--- |")
    md.append(f"| **Average Media Tone** | `{data.get('avg_media', 0):+.2f}` | Global Media Coverage Tone |")
    md.append(f"| **Average Public Sentiment** | `{data.get('avg_public', 0):+.2f}` | Social Sentiment (Bluesky/Reddit) |")
    md.append(f"| **Media ↔ Public Gap** | `{data.get('avg_gap', 0):+.2f}` | Divergence Index |")
    md.append(f"| **Wikipedia Pageviews** | `{stats.get('total_pageviews', 0):,}` | Public Attention Volume |")
    md.append(f"| **Monitored Articles** | `{stats.get('total_articles', 0):,}` | Coverage Depth |")
    md.append(f"| **Anomalous Spikes** | `{len(data.get('anomalies', []))}` | Statistical Outliers |")
    md.append("")

    # 3. Narrative Drivers & Spike Analysis
    drivers = data.get("drivers", {})
    md.append("## 3. Narrative Drivers & Topical Decomposition")
    if drivers.get("spike_week"):
        md.append(f"Primary swing occurred around **{drivers['spike_week']}**.")
        for idx, tp in enumerate(drivers.get("topics", []), 1):
            words = ", ".join(tp["words"])
            md.append(f"* **Theme {idx} (Weight {tp['weight']:.2f}):** `{words}`")
    else:
        md.append("Steady narrative stream without localized clustering.")
    md.append("")

    # 4. 30-Day Scenario Outlook
    fc = data.get("forecast", {})
    md.append("## 4. 30-Day Predictive Trajectory & Scenarios")
    md.append(f"* **Forecasting Methodology:** {fc.get('method', 'Time-series model')}")
    md.append(f"* **Note:** {fc.get('note', '')}")
    if fc.get("points"):
        last_fc = fc["points"][-1]
        md.append(f"* **Projected 4-Week Tone:** `{last_fc['forecast']:+.2f}` (95% Confidence Interval: `[{last_fc['lower']:+.2f}, {last_fc['upper']:+.2f}]`)")
    md.append("")

    # 5. Live News Coverage Wire
    live_news = data.get("live_articles", [])
    if live_news:
        md.append("## 5. Recent Wire Headlines")
        for art in live_news[:5]:
            md.append(f"* **[{art['outlet']}]** [{art['title']}]({art['link']}) — *Sentiment: {art['sentiment']:+.2f} ({art['label']})*")
        md.append("")

    md.append("\n---\n*Report compiled by the Global Political Sentiment Tracker OSINT Pipeline.*")
    return "\n".join(md)


def generate_topic_briefing_html(data: dict) -> str:
    """Produce a styled HTML intelligence briefing suitable for browser view or PDF rendering."""
    topic = data["topic"]
    stats = data["stats"]
    narrative = data["narrative"]
    risk_label, risk_color, risk_rationale = _calculate_risk_rating(data)
    now_str = datetime.now(timezone.utc).strftime("%B %d, %Y - %H:%M UTC")

    points_html = "".join(f"<li>{p}</li>" for p in narrative.get("points", []))
    news_html = "".join(
        f'<div class="news-item"><span class="outlet">{art["outlet"]}</span> <a href="{art["link"]}" target="_blank">{art["title"]}</a> <span class="score">({art["sentiment"]:+.2f})</span></div>'
        for art in data.get("live_articles", [])[:5]
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Intelligence Briefing: {topic['label']}</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      line-height: 1.6;
      color: #1e293b;
      background: #ffffff;
      max-width: 840px;
      margin: 40px auto;
      padding: 0 24px;
    }}
    .header {{ border-bottom: 2px solid #0f172a; padding-bottom: 16px; margin-bottom: 24px; }}
    .badge {{ display: inline-block; padding: 4px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-transform: uppercase; color: #fff; }}
    .risk-box {{ background: #f8fafc; border-left: 4px solid {risk_color}; padding: 14px 18px; margin: 18px 0; border-radius: 0 6px 6px 0; }}
    h1 {{ font-size: 26px; margin: 0 0 6px 0; color: #0f172a; }}
    h2 {{ font-size: 18px; border-bottom: 1px solid #e2e8f0; padding-bottom: 6px; margin-top: 28px; color: #334155; }}
    .meta {{ font-size: 13px; color: #64748b; margin-bottom: 8px; }}
    table {{ width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 14px; }}
    th, td {{ text-align: left; padding: 10px 12px; border-bottom: 1px solid #e2e8f0; }}
    th {{ background: #f1f5f9; color: #475569; }}
    .news-item {{ margin-bottom: 8px; font-size: 13px; }}
    .outlet {{ font-weight: bold; color: #2563eb; }}
    .score {{ color: #64748b; font-size: 12px; }}
    .footer {{ margin-top: 40px; font-size: 12px; color: #94a3b8; border-top: 1px solid #e2e8f0; padding-top: 12px; }}
  </style>
</head>
<body>
  <div class="header">
    <div class="meta">GLOBAL POLITICAL SENTIMENT TRACKER • OSINT INTELLIGENCE BRIEFING</div>
    <h1>{topic['label'].upper()}</h1>
    <div class="meta">Generated: {now_str} | Category: {topic['category']} | Tracked since: {data['inception']}</div>
  </div>

  <div class="risk-box">
    <span class="badge" style="background-color: {risk_color};">{risk_label}</span>
    <p style="margin: 8px 0 0 0; font-size: 14px;"><strong>Assessment:</strong> {risk_rationale}</p>
  </div>

  <h2>1. Executive Summary</h2>
  <p><strong>{narrative['headline']}</strong></p>
  <p>{narrative['summary']}</p>
  {f'<ul>{points_html}</ul>' if points_html else ''}

  <h2>2. Sentiment & Attention Metrics</h2>
  <table>
    <thead><tr><th>Metric</th><th>Value</th><th>Interpretation</th></tr></thead>
    <tbody>
      <tr><td>Average Media Tone</td><td><strong>{data.get('avg_media', 0):+.2f}</strong></td><td>Press coverage tone</td></tr>
      <tr><td>Average Public Sentiment</td><td><strong>{data.get('avg_public', 0):+.2f}</strong></td><td>Social post sentiment</td></tr>
      <tr><td>Media↔Public Gap</td><td><strong>{data.get('avg_gap', 0):+.2f}</strong></td><td>Divergence index</td></tr>
      <tr><td>Wikipedia Attention</td><td><strong>{stats.get('total_pageviews', 0):,}</strong></td><td>Total article pageviews</td></tr>
      <tr><td>Monitored Articles</td><td><strong>{stats.get('total_articles', 0):,}</strong></td><td>Volume analyzed</td></tr>
    </tbody>
  </table>

  <h2>3. Live Wire Influx</h2>
  <div class="news-list">
    {news_html or '<p style="color: #64748b; font-size: 13px;">No recent wire headlines captured.</p>'}
  </div>

  <div class="footer">
    Global Political Sentiment Tracker • Open Source Intelligence Analysis Platform
  </div>
</body>
</html>"""


def generate_topic_briefing(topic_query: str, format: str = "markdown") -> tuple[str, str, str]:
    """Generate topic briefing. Returns (content_str, media_type, filename)."""
    data = analyze_topic(topic_query)
    safe_slug = "".join(c if c.isalnum() else "_" for c in data["topic"]["label"]).strip("_").lower()
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")

    if format == "html":
        content = generate_topic_briefing_html(data)
        return content, "text/html", f"briefing_{safe_slug}_{date_str}.html"
    elif format == "pdf":
        # Check if we can convert HTML to PDF
        html_content = generate_topic_briefing_html(data)
        try:
            from weasyprint import HTML
            pdf_bytes = HTML(string=html_content).write_pdf()
            return pdf_bytes, "application/pdf", f"briefing_{safe_slug}_{date_str}.pdf"
        except ImportError:
            # Fallback to rich HTML with print instruction or Markdown
            content = generate_topic_briefing_markdown(data)
            return content, "text/markdown", f"briefing_{safe_slug}_{date_str}.md"
    else:
        content = generate_topic_briefing_markdown(data)
        return content, "text/markdown", f"briefing_{safe_slug}_{date_str}.md"
