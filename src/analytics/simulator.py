"""Counterfactual Policy Impact & Scenario Simulation Engine."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any
import numpy as np
import pandas as pd

from src.topics.analyze import analyze_topic


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
}


def simulate_policy_shock(
    topic_id: str,
    event_type: str,
    magnitude: float = 1.0,
    weeks_ahead: int = 6,
    custom_description: str | None = None,
) -> dict[str, Any]:
    """Simulate a hypothetical policy shock on a topic's trajectory."""
    # 1. Load baseline topic data
    data = analyze_topic(topic_id)
    topic_meta = data["topic"]
    media_series = data["media_series"]
    opinion_series = data["opinion_series"]

    if not media_series:
        raise ValueError(f"No series data found for topic: {topic_id}")

    # Baseline current level
    last_media_tone = float(media_series[-1]["avg_tone"])
    last_opinion_tone = float(opinion_series[-1]["sentiment"]) if opinion_series else last_media_tone
    last_date = pd.to_datetime(media_series[-1]["date"])

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

    # Baseline gentle mean-reversion
    baseline_media = []
    baseline_public = []
    shocked_media = []
    shocked_public = []
    shocked_upper = []
    shocked_lower = []

    cur_base_m = last_media_tone
    cur_base_p = last_opinion_tone
    cur_shock_m = last_media_tone + tone_impulse
    cur_shock_p = last_opinion_tone + (tone_impulse + divergence_impulse * 0.5)

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
        "topic": topic_meta,
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
