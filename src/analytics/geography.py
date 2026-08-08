"""Geographical intelligence and world sentiment map aggregations."""
from __future__ import annotations

from typing import Any
from datetime import date
import numpy as np
import pandas as pd

from src.topics.synth import global_weekly
from src.topics.catalog import load_catalog


COUNTRY_REGISTRY: list[dict[str, Any]] = [
    {"iso3": "USA", "gdelt": "US", "name": "United States", "flag": "🇺🇸", "groups": ["g7", "nato", "americas"], "leaders": ["Donald Trump", "Joe Biden", "Kamala Harris"]},
    {"iso3": "GBR", "gdelt": "UK", "name": "United Kingdom", "flag": "🇬🇧", "groups": ["g7", "nato", "europe"], "leaders": ["Keir Starmer", "Rishi Sunak", "Labour Party"]},
    {"iso3": "DEU", "gdelt": "GM", "name": "Germany", "flag": "🇩🇪", "groups": ["g7", "nato", "eu", "europe"], "leaders": ["Olaf Scholz", "AfD (Germany)", "CDU/CSU"]},
    {"iso3": "FRA", "gdelt": "FR", "name": "France", "flag": "🇫🇷", "groups": ["g7", "nato", "eu", "europe"], "leaders": ["Emmanuel Macron", "Marine Le Pen", "National Rally"]},
    {"iso3": "IND", "gdelt": "IN", "name": "India", "flag": "🇮🇳", "groups": ["brics", "apac"], "leaders": ["Narendra Modi", "BJP", "Indian National Congress"]},
    {"iso3": "UKR", "gdelt": "UP", "name": "Ukraine", "flag": "🇺🇦", "groups": ["europe"], "leaders": ["Volodymyr Zelenskyy", "War in Ukraine"]},
    {"iso3": "ISR", "gdelt": "IS", "name": "Israel", "flag": "🇮🇱", "groups": ["middle_east"], "leaders": ["Benjamin Netanyahu", "Gaza Conflict"]},
    {"iso3": "CHN", "gdelt": "CH", "name": "China", "flag": "🇨🇳", "groups": ["brics", "apac"], "leaders": ["Xi Jinping", "Taiwan Strait", "US-China Trade"]},
    {"iso3": "JPN", "gdelt": "JA", "name": "Japan", "flag": "🇯🇵", "groups": ["g7", "apac"], "leaders": ["Shigeru Ishiba", "Bank of Japan"]},
    {"iso3": "CAN", "gdelt": "CA", "name": "Canada", "flag": "🇨🇦", "groups": ["g7", "nato", "americas"], "leaders": ["Justin Trudeau", "Conservative Party of Canada"]},
    {"iso3": "AUS", "gdelt": "AS", "name": "Australia", "flag": "🇦🇺", "groups": ["apac"], "leaders": ["Anthony Albanese", "Australian Labor Party"]},
    {"iso3": "BRA", "gdelt": "BR", "name": "Brazil", "flag": "🇧🇷", "groups": ["brics", "latam"], "leaders": ["Luiz Inácio Lula da Silva", "Jair Bolsonaro"]},
    {"iso3": "RUS", "gdelt": "RS", "name": "Russia", "flag": "🇷🇺", "groups": ["brics"], "leaders": ["Vladimir Putin", "Sanctions"]},
    {"iso3": "ZAF", "gdelt": "SF", "name": "South Africa", "flag": "🇿🇦", "groups": ["brics", "africa"], "leaders": ["Cyril Ramaphosa", "ANC"]},
    {"iso3": "ITA", "gdelt": "IT", "name": "Italy", "flag": "🇮🇹", "groups": ["g7", "nato", "eu", "europe"], "leaders": ["Giorgia Meloni", "Brothers of Italy"]},
    {"iso3": "ESP", "gdelt": "SP", "name": "Spain", "flag": "🇪🇸", "groups": ["nato", "eu", "europe"], "leaders": ["Pedro Sánchez", "PSOE", "Vox"]},
    {"iso3": "POL", "gdelt": "PL", "name": "Poland", "flag": "🇵🇱", "groups": ["nato", "eu", "europe"], "leaders": ["Donald Tusk", "PiS"]},
    {"iso3": "TUR", "gdelt": "TU", "name": "Turkey", "flag": "🇹🇷", "groups": ["nato", "middle_east"], "leaders": ["Recep Tayyip Erdogan", "AK Party"]},
    {"iso3": "SAU", "gdelt": "SA", "name": "Saudi Arabia", "flag": "🇸🇦", "groups": ["middle_east", "brics"], "leaders": ["Mohammed bin Salman", "OPEC"]},
    {"iso3": "KOR", "gdelt": "KS", "name": "South Korea", "flag": "🇰🇷", "groups": ["apac"], "leaders": ["Yoon Suk Yeol", "Democratic Party of Korea"]},
    {"iso3": "MEX", "gdelt": "MX", "name": "Mexico", "flag": "🇲🇽", "groups": ["latam", "americas"], "leaders": ["Claudia Sheinbaum", "Morena"]},
    {"iso3": "ARG", "gdelt": "AR", "name": "Argentina", "flag": "🇦🇷", "groups": ["latam"], "leaders": ["Javier Milei", "La Libertad Avanza"]},
    {"iso3": "EGY", "gdelt": "EG", "name": "Egypt", "flag": "🇪🇬", "groups": ["middle_east", "africa", "brics"], "leaders": ["Abdel Fattah el-Sisi", "Suez Canal"]},
    {"iso3": "NGA", "gdelt": "NI", "name": "Nigeria", "flag": "🇳🇬", "groups": ["africa"], "leaders": ["Bola Tinubu", "ECOWAS"]},
    {"iso3": "SWE", "gdelt": "SW", "name": "Sweden", "flag": "🇸🇪", "groups": ["nato", "eu", "europe"], "leaders": ["Ulf Kristersson", "NATO Expansion"]},
    {"iso3": "NLD", "gdelt": "NL", "name": "Netherlands", "flag": "🇳🇱", "groups": ["nato", "eu", "europe"], "leaders": ["Dick Schoof", "PVV"]},
    {"iso3": "CHE", "gdelt": "SZ", "name": "Switzerland", "flag": "🇨🇭", "groups": ["europe"], "leaders": ["Swiss Federal Council", "Neutrality"]},
]


def get_world_sentiment_map(region: str = "all") -> dict[str, Any]:
    """Compute current media tone, public sentiment, and hotspot alerts across world countries."""
    countries_data = []
    hotspot_count = 0
    total_articles = 0
    all_tones = []
    today = date.today()
    timeline_weeks: list[str] = []

    country_histories: list[list[float]] = []

    for c in COUNTRY_REGISTRY:
        if region != "all" and region.lower() not in c["groups"]:
            continue

        # Get deterministic country tone series
        df = global_weekly(c["name"], end=today)
        if df.empty or len(df) < 2:
            continue

        if not timeline_weeks:
            recent_df = df.iloc[-12:]
            timeline_weeks = [d.strftime("%Y-%m-%d") for d in pd.to_datetime(recent_df["week_start"])]

        tones = df["avg_tone"].to_numpy()
        vols = df["article_volume"].to_numpy()
        
        latest_tone = round(float(tones[-1]), 2)
        prev_tone = round(float(np.mean(tones[-5:-1])), 2) if len(tones) >= 5 else latest_tone
        movement = round(float(latest_tone - prev_tone), 2)
        volume = int(vols[-4:].sum())
        total_articles += volume
        all_tones.append(latest_tone)

        # Estimate public sentiment based on domestic framing bias
        public_sentiment = round(float(latest_tone * 0.85 + (1.5 if latest_tone > 0 else -1.5)), 2)
        gap = round(float(public_sentiment - latest_tone), 2)

        # Hotspot condition: substantial tone swing or large divergence
        is_hotspot = abs(movement) >= 2.0 or abs(gap) >= 4.0
        if is_hotspot:
            hotspot_count += 1

        spark = [round(float(x), 2) for x in tones[-12:]]
        country_histories.append(spark)

        # Top local narrative theme
        status_label = "Neutral"
        if latest_tone >= 2.5:
            status_label = "Strongly Positive"
        elif latest_tone >= 0.8:
            status_label = "Moderately Favorable"
        elif latest_tone <= -2.5:
            status_label = "Severe Tension / Crisis"
        elif latest_tone <= -0.8:
            status_label = "Elevated Criticism"

        countries_data.append({
            "iso3": c["iso3"],
            "gdelt": c["gdelt"],
            "name": c["name"],
            "flag": c["flag"],
            "groups": c["groups"],
            "leaders": c["leaders"],
            "latest_tone": latest_tone,
            "public_sentiment": public_sentiment,
            "gap": gap,
            "movement": movement,
            "volume": volume,
            "is_hotspot": is_hotspot,
            "status_label": status_label,
            "spark": spark,
            "history": spark,
        })

    # Sort countries by volume / prominence
    countries_data.sort(key=lambda x: (x["is_hotspot"], x["volume"]), reverse=True)

    global_avg_tone = round(float(np.mean(all_tones)), 2) if all_tones else 0.0

    # Compute timeline average tones
    weekly_global_tones = []
    if country_histories and timeline_weeks:
        arr = np.array(country_histories)
        weekly_global_tones = [round(float(m), 2) for m in np.mean(arr, axis=0)]

    return {
        "region": region,
        "timeline_weeks": timeline_weeks,
        "summary": {
            "country_count": len(countries_data),
            "hotspot_count": hotspot_count,
            "global_avg_tone": global_avg_tone,
            "total_articles": total_articles,
            "weekly_global_tones": weekly_global_tones,
        },
        "countries": countries_data,
    }
