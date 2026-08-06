"""Multi-Lingual Cross-Cultural Media Framing & Narrative Disparity Engine."""
from __future__ import annotations

from typing import Any
import numpy as np

from src.topics.catalog import resolve_topic
from src.topics.synth import global_weekly


LANGUAGE_SPHERES: list[dict[str, Any]] = [
    {
        "code": "en",
        "name": "Anglosphere (English)",
        "region": "US / UK / Commonwealth",
        "color": "#3b82f6",
        "outlets": ["Reuters", "The New York Times", "BBC News", "Financial Times"],
        "tone_bias_factor": 0.0,
    },
    {
        "code": "zh",
        "name": "Sinosphere (Mandarin)",
        "region": "East Asia / China / Regional Diaspora",
        "color": "#ef4444",
        "outlets": ["Xinhua News", "People's Daily", "Lianhe Zaobao", "Global Times"],
        "tone_bias_factor": -0.8,
    },
    {
        "code": "ar",
        "name": "Arab World (Arabic)",
        "region": "Middle East & North Africa",
        "color": "#10b981",
        "outlets": ["Al Jazeera", "Al Arabiya", "Asharq Al-Awsat", "The National"],
        "tone_bias_factor": +0.4,
    },
    {
        "code": "es",
        "name": "Hispanosphere (Spanish)",
        "region": "Latin America & Spain",
        "color": "#f59e0b",
        "outlets": ["El País", "Infobae", "Clarín", "El Universal"],
        "tone_bias_factor": -0.3,
    },
    {
        "code": "ru",
        "name": "Russosphere (Russian)",
        "region": "Eurasia & Eastern Europe",
        "color": "#8b5cf6",
        "outlets": ["TASS", "Kommersant", "RT", "RIA Novosti"],
        "tone_bias_factor": -1.4,
    },
    {
        "code": "fr",
        "name": "Francosphere (French)",
        "region": "Western Europe & Francophone Africa",
        "color": "#06b6d4",
        "outlets": ["Le Monde", "France 24", "Le Figaro", "Jeune Afrique"],
        "tone_bias_factor": +0.2,
    },
    {
        "code": "de",
        "name": "Germanic (German)",
        "region": "Central Europe (DACH)",
        "color": "#ec4899",
        "outlets": ["Der Spiegel", "FAZ", "Neue Zürcher Zeitung", "Die Zeit"],
        "tone_bias_factor": -0.1,
    },
    {
        "code": "hi",
        "name": "Indosphere (Hindi)",
        "region": "South Asia / India",
        "color": "#f97316",
        "outlets": ["Dainik Bhaskar", "NDTV India", "Amar Ujala", "Navbharat Times"],
        "tone_bias_factor": +0.6,
    },
]

TOPIC_FRAMING_LEXICON: dict[str, dict[str, dict[str, Any]]] = {
    "us_china": {
        "en": {"headline": "Bilateral trade frictions and semiconductor containment dialog.", "framing": "Rules-based international order & technological security."},
        "zh": {"headline": "Opposing unilateral containment and protecting multilateral economic development rights.", "framing": "Mutual respect, non-interference, and sovereign development."},
        "ar": {"headline": "Strategic balancing between Eastern technology partnerships and Western capital markets.", "framing": "Multipolar non-alignment and infrastructure investment."},
        "es": {"headline": "South American agro-export corridors caught in geopolitical tariff crossfire.", "framing": "Commodity trade independence and economic sovereignty."},
        "ru": {"headline": "Accelerating de-dollarization and Eurasian industrial integration against sanctions.", "framing": "Strategic partnership and anti-hegemonic counter-balancing."},
        "fr": {"headline": "European strategic autonomy amidst polarized superpower industrial policies.", "framing": "Industrial sovereignty and balanced diplomatic mediation."},
        "de": {"headline": "Supply chain de-risking risks for automotive and chemical export manufacturers.", "framing": "Economic stability, export exposure, and regulatory caution."},
        "hi": {"headline": "Indo-Pacific maritime security balancing paired with domestic manufacturing push.", "framing": "Strategic autonomy, supply chain diversification, and national self-reliance."},
    },
    "ukraine_war": {
        "en": {"headline": "Allied defense procurement and sovereign defense against territorial aggression.", "framing": "Democratic sovereignty and collective NATO deterrence."},
        "zh": {"headline": "Calling for immediate ceasefire and diplomatic settlement addressing security concerns.", "framing": "Indivisible security and diplomatic negotiation neutrality."},
        "ar": {"headline": "Global grain and fertilizer supply shocks affecting Middle Eastern food security.", "framing": "Humanitarian impact and agricultural commodity inflation."},
        "es": {"headline": "Energy price volatility and multilateral diplomatic resolutions at the UN.", "framing": "Peace negotiations and global South inflation mitigation."},
        "ru": {"headline": "Security operations defending strategic borders and countering Western expansion.", "framing": "National security imperatives and anti-NATO mobilization."},
        "fr": {"headline": "European security architecture transformation and long-term defense spending.", "framing": "Continental defense solidarity and sovereign deterrence."},
        "de": {"headline": "Industrial energy transformation following pipeline decouplings.", "framing": "Energy transition acceleration and refugee integration."},
        "hi": {"headline": "Energy supply security and persistent bilateral diplomatic mediation calls.", "framing": "Pragmatic national interest and diplomatic dialog."},
    },
}


def analyze_multilingual_framing(topic_id: str = "us_china") -> dict[str, Any]:
    """Compute cross-lingual sentiment disparity and narrative framing matrices."""
    t_meta = resolve_topic(topic_id)
    df = global_weekly(topic_id)
    base_tone = round(float(df["avg_tone"].iloc[-1]), 2) if not df.empty else 0.0

    spheres_data = []
    tones = []

    # Check for specific framing lexicon or generate structured default
    lexicon_map = TOPIC_FRAMING_LEXICON.get(topic_id, {})

    for s in LANGUAGE_SPHERES:
        jitter = round(float(np.random.normal(0, 0.15)), 2)
        # Apply sphere-specific geopolitical bias model
        sphere_tone = round(float(np.clip(base_tone + s["tone_bias_factor"] + jitter, -10.0, 10.0)), 2)
        tones.append(sphere_tone)

        lex = lexicon_map.get(s["code"], {
            "headline": f"Regional media coverage on {t_meta.label} with domestic policy emphasis.",
            "framing": f"Focus on {s['region']} economic and strategic interests.",
        })

        spheres_data.append({
            "code": s["code"],
            "name": s["name"],
            "region": s["region"],
            "color": s["color"],
            "outlets": s["outlets"],
            "tone": sphere_tone,
            "headline": lex["headline"],
            "framing": lex["framing"],
        })

    max_tone = max(tones)
    min_tone = min(tones)
    disparity_spread = round(float(max_tone - min_tone), 2)

    # Disparity Tier
    if disparity_spread > 3.0:
        tier = "Acute Cultural Polarization"
    elif disparity_spread > 1.8:
        tier = "Substantial Regional Divergence"
    else:
        tier = "Moderate Global Alignment"

    return {
        "topic": {
            "id": t_meta.id,
            "label": t_meta.label,
            "category": t_meta.category,
        },
        "base_tone": base_tone,
        "disparity_spread": disparity_spread,
        "disparity_tier": tier,
        "spheres": spheres_data,
        "max_sphere": next(s["name"] for s in spheres_data if s["tone"] == max_tone),
        "min_sphere": next(s["name"] for s in spheres_data if s["tone"] == min_tone),
    }
