"""Counterfactual Policy Impact & Scenario Simulation Engine."""
from __future__ import annotations

from typing import Any
from datetime import date
import numpy as np
import pandas as pd

from src.topics.catalog import resolve_topic
from src.topics.synth import global_weekly, opinion_weekly


EVENT_PRESETS: dict[str, dict[str, Any]] = {
    "rate_hike": {
        "label": "Central Bank Interest Rate Hike (+50-75bps)",
        "category": "monetary",
        "base_tone_impact": -1.8,
        "public_divergence_impact": -2.4,
        "volume_surge_pct": 35,
        "decay_factor": 0.72,
        "description": "Monetary tightening putting pressure on borrowing, growth commentary, and consumer confidence.",
    },
    "rate_cut": {
        "label": "Central Bank Rate Cut / Monetary Easing",
        "category": "monetary",
        "base_tone_impact": +1.9,
        "public_divergence_impact": +1.5,
        "volume_surge_pct": 25,
        "decay_factor": 0.75,
        "description": "Monetary stimulus driving financial asset optimism and easing household debt burden commentary.",
    },
    "corruption_scandal": {
        "label": "Major Political Corruption / Ethics Investigation",
        "category": "politics",
        "base_tone_impact": -4.2,
        "public_divergence_impact": -5.1,
        "volume_surge_pct": 120,
        "decay_factor": 0.88,
        "description": "Severe reputational shock with persistent negative headlines and heightened voter cynicism.",
    },
    "election_called": {
        "label": "Snap Election / Early General Election Called",
        "category": "politics",
        "base_tone_impact": -0.8,
        "public_divergence_impact": +3.5,
        "volume_surge_pct": 150,
        "decay_factor": 0.80,
        "description": "Massive surge in campaign volume, partisan polarization, and elevated cross-media volatility.",
    },
    "sanctions_imposed": {
        "label": "Broad Economic & Trade Sanctions Enacted",
        "category": "geopolitics",
        "base_tone_impact": -2.8,
        "public_divergence_impact": -3.2,
        "volume_surge_pct": 80,
        "decay_factor": 0.85,
        "description": "Geopolitical retaliation causing supply chain disruption framing and international friction.",
    },
    "military_escalation": {
        "label": "Cross-Border Military Incident / Escalation",
        "category": "geopolitics",
        "base_tone_impact": -5.5,
        "public_divergence_impact": -4.0,
        "volume_surge_pct": 200,
        "decay_factor": 0.90,
        "description": "High-severity geopolitical crisis provoking acute risk-off sentiment and global media alarm.",
    },
    "stimulus_package": {
        "label": "Fiscal Stimulus & Infrastructure Investment Bill",
        "category": "fiscal",
        "base_tone_impact": +2.6,
        "public_divergence_impact": +2.0,
        "volume_surge_pct": 50,
        "decay_factor": 0.70,
        "description": "Expansionary fiscal announcement lifting medium-term growth projections and industrial outlook.",
    },
    "tax_reform": {
        "label": "Major Tax Overhaul / Corporate Levy Hike",
        "category": "fiscal",
        "base_tone_impact": -2.1,
        "public_divergence_impact": -3.8,
        "volume_surge_pct": 60,
        "decay_factor": 0.78,
        "description": "Contested fiscal reform triggering corporate lobbying pushback and partisan voter debate.",
    },
    # ── New presets ──────────────────────────────────────────────────────
    "trade_war": {
        "label": "Trade War / Escalating Tariff Regime",
        "category": "geopolitics",
        "base_tone_impact": -3.1,
        "public_divergence_impact": -2.8,
        "volume_surge_pct": 90,
        "decay_factor": 0.83,
        "description": "Tit-for-tat tariff escalation suppressing trade sentiment, disrupting supply chains, and fuelling domestic cost-of-living anxiety.",
    },
    "climate_accord": {
        "label": "Major Climate Accord / Net-Zero Treaty Signed",
        "category": "policy",
        "base_tone_impact": +2.2,
        "public_divergence_impact": +1.6,
        "volume_surge_pct": 55,
        "decay_factor": 0.68,
        "description": "Landmark multilateral climate agreement boosting green-investment sentiment while splitting industrial sector commentary.",
    },
    "leadership_change": {
        "label": "Governing Coalition Collapse / Leadership Transition",
        "category": "politics",
        "base_tone_impact": -2.5,
        "public_divergence_impact": -3.0,
        "volume_surge_pct": 130,
        "decay_factor": 0.82,
        "description": "Sudden head-of-government departure or coalition break triggering acute political uncertainty and market risk re-pricing.",
    },
}


def simulate_policy_shock(
    topic_id: str,
    event_type: str,
    magnitude: float = 1.0,
    weeks_ahead: int = 6,
    custom_description: str | None = None,
) -> dict[str, Any]:
    """Simulate a hypothetical policy shock on a topic's trajectory."""
    today = date.today()
    topic = resolve_topic(topic_id)
    df_media = global_weekly(topic.label, end=today)
    df_op = opinion_weekly(topic.label, end=today)

    if df_media.empty or len(df_media) < 2:
        df_media = global_weekly("politics", end=today)

    media_tones = df_media["avg_tone"].to_numpy()
    last_media_tone = float(media_tones[-1])
    last_opinion_tone = float(df_op["avg_sentiment"].iloc[-1]) if not df_op.empty else last_media_tone
    last_date = pd.to_datetime(df_media["week_start"].iloc[-1])

    # 2. Get shock profile
    preset = EVENT_PRESETS.get(event_type, {
        "label": "Custom Geopolitical Shock",
        "category": "custom",
        "base_tone_impact": -2.0,
        "public_divergence_impact": -2.5,
        "volume_surge_pct": 50,
        "decay_factor": 0.80,
        "description": custom_description or "User-defined custom counterfactual scenario.",
    })

    tone_impulse = preset["base_tone_impact"] * float(magnitude)
    divergence_impulse = preset["public_divergence_impact"] * float(magnitude)
    decay = float(preset["decay_factor"])

    # 3. Project baseline (status quo) vs simulated shock
    projected_dates = [
        (last_date + pd.Timedelta(weeks=w)).strftime("%Y-%m-%d")
        for w in range(1, weeks_ahead + 1)
    ]

    baseline_media = []
    baseline_public = []
    shocked_media = []
    shocked_public = []
    shocked_upper = []
    shocked_lower = []

    cur_base_m = last_media_tone
    cur_base_p = last_opinion_tone

    for step in range(weeks_ahead):
        # Baseline drift towards neutral 0
        cur_base_m = cur_base_m * 0.95
        cur_base_p = cur_base_p * 0.95
        baseline_media.append(round(float(cur_base_m), 2))
        baseline_public.append(round(float(cur_base_p), 2))

        # Shocked trajectory with impulse decay
        step_impulse = tone_impulse * (decay ** step)
        step_div = divergence_impulse * (decay ** step)

        m_val = cur_base_m + step_impulse
        p_val = cur_base_p + step_impulse + step_div * 0.4
        uncertainty = 0.4 + (step * 0.15) * magnitude

        shocked_media.append(round(float(m_val), 2))
        shocked_public.append(round(float(p_val), 2))
        shocked_upper.append(round(float(m_val + uncertainty), 2))
        shocked_lower.append(round(float(m_val - uncertainty), 2))

    # 4. Synthesize impact metrics
    peak_drawdown = round(float(min(shocked_media) - last_media_tone if tone_impulse < 0 else max(shocked_media) - last_media_tone), 2)
    max_divergence_gap = round(float(max(abs(sm - sp) for sm, sp in zip(shocked_media, shocked_public))), 2)

    # Estimate recovery period in weeks (when impulse < 20% of original)
    recovery_weeks = int(np.ceil(np.log(0.20) / np.log(decay))) if decay < 1.0 else weeks_ahead
    recovery_weeks = min(recovery_weeks, 12)

    # Risk rating
    impact_severity = "Moderate"
    if abs(tone_impulse) >= 4.0 or abs(divergence_impulse) >= 4.5:
        impact_severity = "Critical Systemic Shock"
    elif abs(tone_impulse) >= 2.5:
        impact_severity = "High Market & Political Impact"

    return {
        "topic": {"id": topic.id, "label": topic.label, "category": topic.category},
        "event": {
            "type": event_type,
            "label": preset["label"],
            "magnitude": magnitude,
            "description": custom_description or preset["description"],
            "category": preset["category"],
        },
        "metrics": {
            "initial_tone": round(last_media_tone, 2),
            "peak_delta": peak_drawdown,
            "max_divergence_gap": max_divergence_gap,
            "recovery_weeks": recovery_weeks,
            "volume_surge_pct": int(preset["volume_surge_pct"] * magnitude),
            "severity_assessment": impact_severity,
        },
        "simulation": {
            "dates": projected_dates,
            "baseline_media": baseline_media,
            "baseline_public": baseline_public,
            "shocked_media": shocked_media,
            "shocked_public": shocked_public,
            "shocked_upper": shocked_upper,
            "shocked_lower": shocked_lower,
        },
    }


def batch_simulate(
    topic_id: str,
    magnitude: float = 1.0,
    weeks_ahead: int = 6,
) -> dict[str, Any]:
    """Run all EVENT_PRESETS against a topic and return a ranked impact comparison table.

    Useful for a 'what-if matrix' on the frontend — shows which events would
    have the largest effect on a given topic's sentiment trajectory.
    """
    results = []
    for event_type, preset in EVENT_PRESETS.items():
        sim = simulate_policy_shock(
            topic_id=topic_id,
            event_type=event_type,
            magnitude=magnitude,
            weeks_ahead=weeks_ahead,
        )
        results.append({
            "event_type": event_type,
            "event_label": preset["label"],
            "event_category": preset["category"],
            "peak_delta": sim["metrics"]["peak_delta"],
            "recovery_weeks": sim["metrics"]["recovery_weeks"],
            "volume_surge_pct": sim["metrics"]["volume_surge_pct"],
            "severity_assessment": sim["metrics"]["severity_assessment"],
            "max_divergence_gap": sim["metrics"]["max_divergence_gap"],
        })

    # Sort by absolute peak impact (largest first)
    results.sort(key=lambda r: abs(r["peak_delta"]), reverse=True)

    topic = resolve_topic(topic_id)
    return {
        "topic": {"id": topic.id, "label": topic.label, "category": topic.category},
        "magnitude": magnitude,
        "weeks_ahead": weeks_ahead,
        "ranked_events": results,
    }


def list_presets() -> list[dict[str, Any]]:
    """Return all available event presets with metadata (for frontend dropdowns)."""
    return [
        {
            "id": k,
            "label": v["label"],
            "category": v["category"],
            "description": v["description"],
            "base_tone_impact": v["base_tone_impact"],
            "volume_surge_pct": v["volume_surge_pct"],
        }
        for k, v in EVENT_PRESETS.items()
    ]
