"""On-demand analysis bundle for any topic — reuses the analytics layer."""
from __future__ import annotations

import os
from datetime import date, datetime, timezone

import pandas as pd

from ..config import load_watchlist
from ..ingestion.synthetic import _LANG
from ..analytics import (weekly_weighted_series, country_tone_summary,
                         forecast_tone, detect_anomalies, biggest_spike_week,
                         extract_topics)
from . import synth, live
from .catalog import Topic, resolve_topic

_LIVE_SOURCES = {"auto", "live", "gdelt"}


def _media_pack(query: str, start: date, end: date, source: str,
                countries: list[str]) -> dict:
    """Media weekly series + geography + driver titles, from live or synthetic.

    Geography (by_country/by_language) is always modelled — per-country live
    pulls are too many GDELT calls for an on-demand request.
    """
    by_country = synth.by_country_weekly(query, end, countries)  # modelled geo
    if source in _LIVE_SOURCES:
        lm = live.live_media(query, start, end)
        if lm:
            titles = lm["titles"] or synth.titles(query)
            return {"media": lm["media"], "by_country": by_country, "titles": titles,
                    "source": "gdelt", "geo_modelled": True}
    return {"media": weekly_weighted_series(by_country), "by_country": by_country,
            "titles": synth.titles(query), "source": "synthetic", "geo_modelled": False}


def _opinion_pack(query: str, start: date, end: date, source: str) -> dict:
    if source in _LIVE_SOURCES:
        lo = live.live_opinion(query, start, end)
        if lo is not None and not lo.empty:
            return {"opinion": lo, "source": "reddit+bluesky"}
    return {"opinion": synth.opinion_weekly(query, end), "source": "synthetic"}


def _recs(df: pd.DataFrame, cols: list[str]) -> list[dict]:
    if df is None or df.empty:
        return []
    d = df[cols].copy()
    if "week_start" in d.columns:
        d["week_start"] = pd.to_datetime(d["week_start"]).dt.strftime("%Y-%m-%d")
    return d.where(pd.notna(d), None).to_dict("records")


def analyze_topic(query: str, *, end: date | None = None,
                  source: str | None = None) -> dict:
    topic: Topic = resolve_topic(query)
    end = end or datetime.now(timezone.utc).date()
    source = (source or os.getenv("GPST_TOPIC_SOURCE", "synthetic")).lower()
    wl = load_watchlist()
    countries = wl.gdelt_country_codes
    meta = synth.topic_meta(topic.query, end)

    mp = _media_pack(topic.query, meta["inception"], end, source, countries)
    op = _opinion_pack(topic.query, meta["inception"], end, source)
    by_country = mp["by_country"]
    titles = mp["titles"]
    opinion = op["opinion"]

    # --- media global series (live or synthetic) ---
    media = mp["media"]  # week_start, avg_tone, article_volume, low_confidence
    # --- opinion combined ---
    opin_all = opinion[opinion["source"] == "all"].sort_values("week_start") if not opinion.empty else opinion

    # --- media vs public ---
    mvp = pd.DataFrame()
    if not media.empty and not opin_all.empty:
        mvp = pd.merge(
            media[["week_start", "avg_tone", "article_volume"]].rename(columns={"avg_tone": "media_tone"}),
            opin_all[["week_start", "avg_sentiment", "post_volume"]].rename(columns={"avg_sentiment": "public_sentiment"}),
            on="week_start", how="outer").sort_values("week_start")
        mvp["gap"] = (mvp["public_sentiment"] - mvp["media_tone"]).round(3)

    both = mvp.dropna(subset=["media_tone", "public_sentiment"]) if not mvp.empty else pd.DataFrame()

    # --- forecast + anomalies on media global ---
    fc = forecast_tone(media, periods=4) if not media.empty else None
    an = detect_anomalies(media) if not media.empty else pd.DataFrame()
    flagged = an[an["is_anomaly"]] if not an.empty else pd.DataFrame()

    # --- drivers (topic modeling on titles around the spike) ---
    spike = biggest_spike_week(media) if not media.empty else None
    drv = extract_topics(titles, n_topics=3, extra_stopwords=topic.label.split())

    # --- per country + per language ---
    csum = country_tone_summary(by_country)
    if not csum.empty:
        csum["country_name"] = csum["country"].map(wl.name_by_gdelt)
        csum["iso3"] = csum["country"].map(wl.iso3_by_gdelt)
    lang_rows = []
    if not by_country.empty:
        tmp = by_country.copy()
        tmp["language"] = tmp["country"].map(lambda c: _LANG.get(c, "English"))
        for lang, g in tmp.groupby("language"):
            v = g["article_volume"].to_numpy(); t = g["avg_tone"].to_numpy()
            tot = v.sum()
            lang_rows.append({"language": lang, "volume": int(tot),
                              "avg_tone": round(float((t * v).sum() / tot), 3) if tot else 0.0})
    lang_df = pd.DataFrame(lang_rows).sort_values("volume", ascending=False) if lang_rows else pd.DataFrame()

    return {
        "topic": {"id": topic.id, "label": topic.label, "query": topic.query,
                  "category": topic.category, "custom": topic.custom},
        "inception": meta["inception"].strftime("%Y-%m-%d"),
        "age_weeks": meta["age_weeks"],
        "window": {"start": media["week_start"].min().strftime("%Y-%m-%d") if not media.empty else None,
                   "end": media["week_start"].max().strftime("%Y-%m-%d") if not media.empty else None},
        "media_series": _recs(media, ["week_start", "avg_tone", "article_volume"]),
        "opinion_series": _recs(opin_all, ["week_start", "avg_sentiment", "post_volume"]) if not opin_all.empty else [],
        "media_vs_public": _recs(mvp, ["week_start", "media_tone", "public_sentiment", "gap"]) if not mvp.empty else [],
        "avg_media": round(float(both["media_tone"].mean()), 2) if not both.empty else None,
        "avg_public": round(float(both["public_sentiment"].mean()), 2) if not both.empty else None,
        "avg_gap": round(float(both["gap"].mean()), 2) if not both.empty else None,
        "forecast": {
            "method": fc.method if fc else "none",
            "note": fc.note if fc else "",
            "points": _recs(fc.forecast, ["week_start", "forecast", "lower", "upper"]) if fc else [],
        },
        "anomalies": _recs(flagged, ["week_start", "avg_tone", "kind", "direction", "shift"]),
        "drivers": {"spike_week": spike.strftime("%Y-%m-%d") if spike is not None else None,
                    "topics": [{"words": t.words, "weight": t.weight} for t in drv]},
        "by_country": _recs(csum, ["country", "country_name", "iso3", "avg_tone",
                                   "article_volume", "source_diversity", "low_conf_weeks", "n_weeks"]),
        "by_language": _recs(lang_df, ["language", "avg_tone", "volume"]),
        "stats": {
            "total_articles": int(by_country["article_volume"].sum()) if not by_country.empty else 0,
            "total_posts": int(opinion[opinion["source"] != "all"]["post_volume"].sum()) if not opinion.empty else 0,
            "max_diversity": int(by_country["source_diversity"].max()) if not by_country.empty else 0,
            "low_conf_weeks": int(media["low_confidence"].sum()) if "low_confidence" in media and not media.empty else 0,
            "n_weeks": int(media["week_start"].nunique()) if not media.empty else 0,
            "source_media": mp["source"], "source_opinion": op["source"],
            "geo_modelled": mp["geo_modelled"],
        },
    }
