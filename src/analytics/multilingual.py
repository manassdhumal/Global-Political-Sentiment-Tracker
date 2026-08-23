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
    # ── New framing topics ────────────────────────────────────────────────
    "inflation": {
        "en": {"headline": "Central banks navigate stubborn core inflation with cautious forward guidance.", "framing": "Monetary credibility, interest rate stability, and consumer purchasing power."},
        "zh": {"headline": "Deflationary pressures and export competitiveness challenges dominate domestic discourse.", "framing": "Industrial output support and strategic price stability."},
        "ar": {"headline": "Food import inflation threatens household budgets across MENA import-dependent economies.", "framing": "Energy subsidies, bread price controls, and social stability."},
        "es": {"headline": "Wage-price spirals and central bank independence pressures in Latin America.", "framing": "Cost of living crisis, trade union bargaining, and dollarization debates."},
        "ru": {"headline": "Sanctions-driven import substitution fuels structural price pressures.", "framing": "Sanctions resilience, domestic production subsidies, and currency defense."},
        "fr": {"headline": "ECB rate policy creates tension between inflation control and growth in Southern Europe.", "framing": "European solidarity, energy price governance, and purchasing power protection."},
        "de": {"headline": "Export sector cost pressures from energy transition and wage inflation.", "framing": "Competitive exports, Bundesbank orthodoxy, and fiscal discipline."},
        "hi": {"headline": "RBI tightening cycle balances rupee stability against domestic growth imperatives.", "framing": "Food price management, rural household budgets, and monsoon-driven volatility."},
    },
    "ai_regulation": {
        "en": {"headline": "Washington and Brussels race to establish AI governance frameworks before election cycles.", "framing": "Innovation competitiveness, safety standards, and democratic accountability."},
        "zh": {"headline": "State-guided AI development balances technological sovereignty with global standards alignment.", "framing": "National AI champion strategy, data sovereignty, and economic modernization."},
        "ar": {"headline": "Gulf sovereign wealth funds accelerate AI infrastructure investment amid regulatory vacuum.", "framing": "Economic diversification, digital sovereignty, and technology transfer."},
        "es": {"headline": "Latin American nations navigate AI governance between US and EU regulatory models.", "framing": "Technology access equity, digital colonialism concerns, and innovation capacity."},
        "ru": {"headline": "Russia accelerates domestic AI development to circumvent Western export controls.", "framing": "Technological sovereignty, military AI applications, and sanctions circumvention."},
        "fr": {"headline": "EU AI Act enforcement creates compliance burdens for European tech sector.", "framing": "Human rights protection, algorithmic transparency, and French digital industry competitiveness."},
        "de": {"headline": "German engineering sector seeks AI integration clarity under strict EU liability rules.", "framing": "Industrial automation, precision engineering applications, and legal certainty."},
        "hi": {"headline": "India positions as AI services hub while debating domestic regulatory framework.", "framing": "IT sector competitiveness, data localization, and digital public infrastructure."},
    },
    "climate_change": {
        "en": {"headline": "Record temperatures and extreme weather events accelerate net-zero policy momentum.", "framing": "Science-based transition, green investment, and intergenerational equity."},
        "zh": {"headline": "China leads renewable capacity buildout while defending coal transition timeline sovereignty.", "framing": "Developing nation transition rights, green technology export leadership."},
        "ar": {"headline": "Oil-producing nations balance hydrocarbon revenue defense with sovereign wealth fund green diversification.", "framing": "Economic transition fairness, energy security, and climate finance equity."},
        "es": {"headline": "Amazon deforestation and extreme drought events dominate Latin American climate narrative.", "framing": "Biodiversity protection, climate debt, and indigenous territorial rights."},
        "ru": {"headline": "Arctic resource access and reduced shipping costs reframe Russia's climate change calculus.", "framing": "Energy resource sovereignty and strategic Arctic development."},
        "fr": {"headline": "Nuclear power rebranded as climate solution amid French energy sovereignty debate.", "framing": "Energy mix independence, industrial decarbonization, and EU taxonomy battles."},
        "de": {"headline": "Energiewende costs and deindustrialization risks dominate German green transition debate.", "framing": "Industrial competitiveness, energy security, and Mittelstand resilience."},
        "hi": {"headline": "India demands climate finance equity and defends coal transition timeline at COP negotiations.", "framing": "Development rights, climate justice, and renewable energy leapfrogging."},
    },
}


def analyze_multilingual_framing(topic_id: str = "us_china") -> dict[str, Any]:
    """Compute cross-lingual sentiment disparity and narrative framing matrices."""
    t_meta = resolve_topic(topic_id)
    df = global_weekly(topic_id)
    base_tone = round(float(df["avg_tone"].iloc[-1]), 2) if not df.empty else 0.0

    # Use a seeded RNG keyed to the topic for reproducible per-topic jitter.
    # This prevents the page returning different values on each reload.
    rng = np.random.default_rng(seed=abs(hash(topic_id)) % (2 ** 31))

    spheres_data = []
    tones = []

    # Check for specific framing lexicon or generate structured default
    lexicon_map = TOPIC_FRAMING_LEXICON.get(topic_id, {})

    for s in LANGUAGE_SPHERES:
        jitter = round(float(rng.normal(0, 0.15)), 2)
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
