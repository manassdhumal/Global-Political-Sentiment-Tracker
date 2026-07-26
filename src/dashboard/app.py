"""Global Political Sentiment Tracker — Streamlit dashboard (Phase 2).

Multipage app (st.navigation). Run from the project root:
    streamlit run src/dashboard/app.py

Views:
    World map (choropleth) · Tone over time · Cross-country · Entity vs entity
    · Issue drill-down · Volatility index

FRAMING: every score shown is the TONE OF NEWS COVERAGE (-100..+100), i.e.
MEDIA SENTIMENT — not public opinion. Stated consistently across views.
"""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

st.set_page_config(page_title="Global Political Sentiment Tracker",
                   page_icon="🌍", layout="wide")

from src.dashboard.views import (  # noqa: E402
    homepage, search, overview, tone_over_time, cross_country,
    entity_vs_entity, issue_drilldown, volatility,
    forecast_alerts, event_impact, framing,
    analyze_text, reports, methodology)


def main() -> None:
    st.title("🌍 Global Political Sentiment Tracker")
    st.caption("Tracks the **tone of news coverage** toward political figures, "
               "parties and issues — across countries, over time. Scores are "
               "**media sentiment (coverage tone), not public opinion.**")

    pages_by_section = {
        "Overview": [
            st.Page(homepage.render, title="Political mood", icon="🏠",
                    url_path="home", default=True),
            st.Page(search.render, title="Search", icon="🔍", url_path="search"),
        ],
        "Explore": [
            st.Page(overview.render, title="World map", icon="🗺️",
                    url_path="world-map"),
            st.Page(tone_over_time.render, title="Tone over time", icon="📈",
                    url_path="tone-over-time"),
            st.Page(cross_country.render, title="Cross-country", icon="🌐",
                    url_path="cross-country"),
            st.Page(entity_vs_entity.render, title="Entity vs entity", icon="⚖️",
                    url_path="entity-vs-entity"),
            st.Page(issue_drilldown.render, title="Issue drill-down", icon="🔎",
                    url_path="issue-drilldown"),
            st.Page(volatility.render, title="Volatility index", icon="📊",
                    url_path="volatility"),
        ],
        "Intelligence": [
            st.Page(forecast_alerts.render, title="Forecast & alerts", icon="🔮",
                    url_path="forecast-alerts"),
            st.Page(event_impact.render, title="Event impact", icon="🎯",
                    url_path="event-impact"),
            st.Page(framing.render, title="Cross-language framing", icon="🗣️",
                    url_path="framing"),
        ],
        "Your text & reports": [
            st.Page(analyze_text.render, title="Analyze text", icon="📝",
                    url_path="analyze-text"),
            st.Page(reports.render, title="Reports", icon="📄",
                    url_path="reports"),
            st.Page(methodology.render, title="Methodology", icon="📚",
                    url_path="methodology"),
        ],
    }
    st.navigation(pages_by_section).run()


if __name__ == "__main__":
    main()
