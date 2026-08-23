"""Media Polarization & Editorial Framing Spectrum Analytics."""
from __future__ import annotations

from typing import Any
from datetime import date
import numpy as np
import pandas as pd

from src.topics.synth import global_weekly
from src.topics.catalog import resolve_topic


MEDIA_SPECTRUM_REGISTRY: dict[str, dict[str, Any]] = {
    "center_left": {
        "id": "center_left",
        "name": "Center-Left / Progressive",
        "color": "#3b82f6",
        "outlets": ["The Guardian", "The New York Times", "The Washington Post", "Le Monde", "CNN", "MSNBC"],
        "tone_offset": -0.8,
        "keywords": ["humanitarian impact", "social equity", "systemic reform", "climate urgency", "wealth inequality", "regulatory oversight"],
    },
    "center_right": {
        "id": "center_right",
        "name": "Center-Right / Conservative",
        "color": "#ef4444",
        "outlets": ["The Telegraph", "The Wall Street Journal", "Fox News", "National Review", "The Times (UK)", "Daily Mail"],
        "tone_offset": +0.9,
        "keywords": ["fiscal discipline", "border security", "tax burden", "individual liberty", "defense deterrence", "deregulation"],
    },
    "centrist_wires": {
        "id": "centrist_wires",
        "name": "Centrist / Wire Services",
        "color": "#10b981",
        "outlets": ["Reuters", "Associated Press", "Bloomberg News", "AFP", "BBC News"],
        "tone_offset": 0.0,
        "keywords": ["market consensus", "bilateral negotiations", "official statement", "quarterly data", "diplomatic protocol", "parliamentary vote"],
    },
    "state_international": {
        "id": "state_international",
        "name": "State-Affiliated / International",
        "color": "#8b5cf6",
        "outlets": ["Xinhua News", "Al Jazeera", "RT", "TASS", "DW (Deutsche Welle)"],
        "tone_offset": -1.2,
        "keywords": ["multipolar order", "sanctions blowback", "sovereign autonomy", "global south solidarity", "western hegemony", "strategic partnership"],
    },
}


def analyze_media_polarization(topic_id: str = "inflation") -> dict[str, Any]:
    """Compute editorial polarization, framing gap, and keyword divergence across the ideological spectrum."""
    topic = resolve_topic(topic_id)
    today = date.today()
    df_base = global_weekly(topic.label, end=today)

    if df_base.empty or len(df_base) < 5:
        df_base = global_weekly("politics", end=today)

    dates = [d.strftime("%Y-%m-%d") for d in pd.to_datetime(df_base["week_start"])]
    base_tones = df_base["avg_tone"].to_numpy()
    n = len(dates)

    spectrum_results = []
    spread_series = []

    # Generate aligned synthetic spectrum series
    spectrum_series_map: dict[str, list[float]] = {}

    for s_id, meta in MEDIA_SPECTRUM_REGISTRY.items():
        rng = np.random.default_rng(abs(hash(f"{topic.id}_{s_id}")) % (2**32))
        noise = rng.normal(0, 0.45, n)
        spec_tones = np.clip(base_tones + meta["tone_offset"] + noise, -10.0, 10.0)
        spec_tones_clean = [round(float(x), 2) for x in spec_tones]
        spectrum_series_map[s_id] = spec_tones_clean

        latest = spec_tones_clean[-1]
        prev = spec_tones_clean[-5] if len(spec_tones_clean) >= 5 else latest
        vol = int(rng.integers(1200, 8500))

        spectrum_results.append({
            "id": s_id,
            "name": meta["name"],
            "color": meta["color"],
            "outlets": meta["outlets"],
            "latest_tone": latest,
            "movement": round(float(latest - prev), 2),
            "volume": vol,
            "keywords": meta["keywords"],
            "series": spec_tones_clean[-16:],
        })

    # Calculate Polarization Spread (Left vs. Right divergence)
    left_series = spectrum_series_map["center_left"]
    right_series = spectrum_series_map["center_right"]

    for d, l_val, r_val in zip(dates, left_series, right_series):
        spread_series.append({
            "date": d,
            "spread": round(float(abs(r_val - l_val)), 2),
            "left_tone": l_val,
            "right_tone": r_val,
        })

    latest_spread = spread_series[-1]["spread"] if spread_series else 1.5
    mean_spread = round(float(np.mean([s["spread"] for s in spread_series])), 2)

    # Convergence trend: compare mean spread of last 8 weeks vs prior 8 weeks
    convergence_trend = "stable"
    if len(spread_series) >= 16:
        recent_mean = float(np.mean([s["spread"] for s in spread_series[-8:]]))
        prior_mean = float(np.mean([s["spread"] for s in spread_series[-16:-8]]))
        delta_spread = round(recent_mean - prior_mean, 2)
        if delta_spread > 0.15:
            convergence_trend = "widening"
        elif delta_spread < -0.15:
            convergence_trend = "narrowing"
    elif len(spread_series) >= 4:
        # Simpler early-detection with fewer points
        recent_mean = float(np.mean([s["spread"] for s in spread_series[-2:]]))
        prior_mean = float(np.mean([s["spread"] for s in spread_series[:2]]))
        delta_spread = round(recent_mean - prior_mean, 2)
        convergence_trend = "widening" if delta_spread > 0.15 else "narrowing" if delta_spread < -0.15 else "stable"
    else:
        delta_spread = 0.0

    # Polarization Severity Assessment
    if latest_spread >= 3.0:
        polarization_tier = "Severe Echo Chamber Fragmentation"
        tier_code = "severe"
    elif latest_spread >= 1.8:
        polarization_tier = "Elevated Partisan Framing Divergence"
        tier_code = "elevated"
    else:
        polarization_tier = "Bipartisan / High Consensus Framing"
        tier_code = "consensus"

    return {
        "topic": {"id": topic.id, "label": topic.label, "category": topic.category},
        "summary": {
            "latest_polarization_spread": latest_spread,
            "mean_polarization_spread": mean_spread,
            "polarization_tier": polarization_tier,
            "tier_code": tier_code,
            "convergence_trend": convergence_trend,
            "spread_delta_8w": round(delta_spread, 2) if 'delta_spread' in dir() else 0.0,
        },
        "spectra": spectrum_results,
        "timeline": spread_series[-26:],
    }
