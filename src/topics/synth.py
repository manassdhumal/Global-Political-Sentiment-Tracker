"""Deterministic on-demand synthetic data for ANY topic query.

Generates weekly series directly (not per-article) so it's fast enough to run
live per request and can span a long history. Each topic has a deterministic
"inception" week, so histories vary in length (some topics are older than
others) — matching "since the topic first arose".

This is the offline fallback; the same shapes are what the live GDELT/social
path would produce. FABRICATED — flagged source='synthetic', never real.
"""
from __future__ import annotations

import hashlib
from datetime import date, timedelta

import numpy as np
import pandas as pd

WEEK = timedelta(weeks=1)
MAX_WEEKS = 156  # ~3 years cap

# Relative media-market size per GDELT country code (drives volume).
COUNTRY_WEIGHT = {
    "US": 1.0, "UK": 0.8, "IN": 0.7, "GM": 0.6, "FR": 0.6, "CH": 0.6, "JA": 0.5,
    "BR": 0.5, "RS": 0.5, "CA": 0.4, "IT": 0.4, "SP": 0.4, "AS": 0.4, "KS": 0.35,
    "TU": 0.3, "MX": 0.3, "ID": 0.3, "NL": 0.3, "PL": 0.3, "UP": 0.35, "SF": 0.25,
    "AR": 0.25, "IS": 0.35, "SA": 0.25, "EG": 0.25, "NI": 0.25,
}
_TOPIC_WORDS = ["policy", "reform", "debate", "summit", "vote", "poll", "budget",
                "plan", "deal", "law", "statement", "report", "meeting"]
_SHOCK_WORDS = ["crisis", "scandal", "backlash", "controversy", "protest",
                "resignation", "investigation", "outrage", "clash", "warning"]


def _seed(*parts: str) -> int:
    return int(hashlib.sha256("|".join(parts).encode()).hexdigest()[:8], 16)


def _rng(*parts: str) -> np.random.Generator:
    return np.random.default_rng(_seed(*parts))


def _monday(d: date) -> date:
    return d - timedelta(days=d.weekday())


def topic_meta(query: str, end: date) -> dict:
    rng = _rng("meta", query)
    end_m = _monday(end)
    age = int(rng.integers(16, MAX_WEEKS + 1))
    return {
        "inception": end_m - age * WEEK,
        "age_weeks": age,
        "base_tone": float(rng.uniform(-6, 5)),
        "trend": float(rng.uniform(-0.04, 0.04)),
        "season_amp": float(rng.uniform(0.4, 2.5)),
        "shock_week": int(rng.integers(int(age * 0.3), max(int(age * 0.9), int(age * 0.3) + 1))),
        "shock_mag": float(rng.uniform(-9, 9)),
        "vol_base": float(rng.uniform(40, 420)),
        "public_bias": float(rng.uniform(-10, 14)),   # public often diverges from press
        "public_vol_base": float(rng.uniform(30, 320)),
    }


def _weeks(meta: dict, end: date) -> list[date]:
    end_m = _monday(end)
    return [meta["inception"] + i * WEEK for i in range(meta["age_weeks"])
            if meta["inception"] + i * WEEK <= end_m]


def _tone_curve(meta: dict, n: int, rng: np.random.Generator, offset: float = 0.0) -> np.ndarray:
    i = np.arange(n)
    mean = meta["base_tone"] + offset + meta["trend"] * i \
        + meta["season_amp"] * np.sin(2 * np.pi * i / 26.0)
    decay = np.clip(1.0 - np.abs(i - meta["shock_week"]) / 8.0, 0, None)
    mean = mean + meta["shock_mag"] * decay
    return np.clip(mean + rng.normal(0, 1.2, n), -100, 100)


def _ramp(n: int) -> np.ndarray:
    # topics start small and grow after inception
    r = np.minimum(1.0, 0.35 + np.arange(n) / 12.0)
    return r


def global_weekly(query: str, end: date | None = None) -> pd.DataFrame:
    if end is None:
        end = date.today()
    meta = topic_meta(query, end)
    weeks = _weeks(meta, end)
    n = len(weeks)
    if n == 0:
        return pd.DataFrame(columns=["week_start", "avg_tone", "article_volume"])
    rng = _rng("gtone", query)
    tone = _tone_curve(meta, n, rng)
    vol = np.maximum(1, (meta["vol_base"] * _ramp(n) * rng.uniform(0.7, 1.3, n)).astype(int))
    return pd.DataFrame({"week_start": pd.to_datetime(weeks), "avg_tone": np.round(tone, 3),
                         "article_volume": vol})


def by_country_weekly(query: str, end: date | None = None, countries: list[str] | None = None) -> pd.DataFrame:
    if end is None:
        end = date.today()
    if countries is None:
        countries = ["US", "UK", "IN", "GM", "FR", "CH"]
    meta = topic_meta(query, end)
    weeks = _weeks(meta, end)
    n = len(weeks)
    rows = []
    for c in countries:
        rng = _rng("country", query, c)
        offset = rng.uniform(-4, 4)
        tone = _tone_curve(meta, n, rng, offset=offset)
        w = COUNTRY_WEIGHT.get(c, 0.2)
        vol = np.maximum(0, (meta["vol_base"] * w * _ramp(n) * rng.uniform(0.5, 1.4, n)).astype(int))
        div = np.clip((vol / 8).astype(int), 0, 6)
        low = ((vol < 5) | (div < 2)).astype(int)
        for i in range(n):
            rows.append({"country": c, "week_start": weeks[i], "avg_tone": round(float(tone[i]), 3),
                         "article_volume": int(vol[i]), "source_diversity": int(div[i]),
                         "low_confidence": int(low[i])})
    df = pd.DataFrame(rows)
    if not df.empty:
        df["week_start"] = pd.to_datetime(df["week_start"])
    return df


def opinion_weekly(query: str, end: date | None = None) -> pd.DataFrame:
    if end is None:
        end = date.today()
    meta = topic_meta(query, end)
    weeks = _weeks(meta, end)
    n = len(weeks)
    rows = []
    for src in ("reddit", "bluesky"):
        rng = _rng("op", query, src)
        # public tracks media loosely but shifted by public_bias + own noise
        tone = _tone_curve(meta, n, rng, offset=meta["public_bias"] + rng.uniform(-3, 3))
        vol = np.maximum(0, (meta["public_vol_base"] * (0.6 if src == "bluesky" else 1.0)
                             * _ramp(n) * rng.uniform(0.6, 1.4, n)).astype(int))
        authors = np.maximum(1, (vol * rng.uniform(0.5, 0.9, n)).astype(int))
        for i in range(n):
            rows.append({"source": src, "week_start": weeks[i], "avg_sentiment": round(float(tone[i]), 3),
                         "post_volume": int(vol[i]), "unique_authors": int(authors[i])})
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    # combined 'all' = volume-weighted per week
    comb = []
    for wk, g in df.groupby("week_start"):
        v = g["post_volume"].to_numpy(); s = g["avg_sentiment"].to_numpy()
        tot = v.sum()
        comb.append({"source": "all", "week_start": wk,
                     "avg_sentiment": round(float((s * v).sum() / tot), 3) if tot else 0.0,
                     "post_volume": int(tot), "unique_authors": int(g["unique_authors"].sum())})
    out = pd.concat([df, pd.DataFrame(comb)], ignore_index=True)
    out["week_start"] = pd.to_datetime(out["week_start"])
    out["low_confidence"] = ((out["post_volume"] < 5) | (out["unique_authors"] < 3)).astype(int)
    return out


def titles(query: str, near_shock: bool = True, n: int = 40) -> list[str]:
    rng = _rng("titles", query, "shock" if near_shock else "calm")
    qwords = [w for w in query.replace('"', "").split() if len(w) > 2][:3] or ["topic"]
    pool = qwords + _TOPIC_WORDS
    out = []
    for _ in range(n):
        k = int(rng.integers(2, 4))
        words = list(rng.choice(pool, size=min(k, len(pool)), replace=False))
        if near_shock:
            words += list(rng.choice(_SHOCK_WORDS, size=2, replace=False))
        rng.shuffle(words)
        out.append(" ".join(words))
    return out


def attention_weekly(query: str, end: date) -> pd.DataFrame:
    """Synthetic Wikipedia attention series fallback."""
    meta = topic_meta(query, end)
    weeks = _weeks(meta, end)
    n = len(weeks)
    rng = _rng("attention", query)
    base_views = int(rng.uniform(5000, 50000))
    views = np.maximum(500, (base_views * _ramp(n) * rng.uniform(0.7, 1.6, n)).astype(int))
    rows = [
        {
            "week_start": weeks[i],
            "pageviews": int(views[i]),
            "daily_avg": round(float(views[i] / 7.0), 1),
        }
        for i in range(n)
    ]
    df = pd.DataFrame(rows)
    if not df.empty:
        df["week_start"] = pd.to_datetime(df["week_start"])
    return df
