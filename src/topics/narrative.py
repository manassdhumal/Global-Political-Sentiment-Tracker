"""Generated narrative — turns a topic's numbers into an explained analysis.

Reads the analyze_topic bundle (tone, media-vs-public gap, trend, forecast,
anomalies, drivers, geography, confidence) and composes a plain-English
explanation: a headline, a short summary, and key points.

Two backends, pluggable like the sentiment engine:
  * 'rules'     -- deterministic, offline, honest (DEFAULT).
  * 'anthropic' -- optional LLM for richer prose (needs ANTHROPIC_API_KEY +
                   the `anthropic` package); set GPST_NARRATIVE=anthropic.
                   Falls back to rules on any failure.

Framing is preserved: this describes MEDIA & SOCIAL sentiment, hedged, never
stated as public opinion or fact.
"""
from __future__ import annotations

import os


# ---------------------------------------------------------------------
# interpretation helpers
# ---------------------------------------------------------------------
def _tone_word(v: float | None) -> str:
    if v is None:
        return "unclear"
    if v >= 15:
        return "strongly positive"
    if v >= 5:
        return "positive"
    if v > -5:
        return "broadly neutral"
    if v > -15:
        return "negative"
    return "strongly negative"


def _gap_phrase(gap: float | None) -> str:
    if gap is None:
        return "with no comparable public signal"
    if gap >= 6:
        return "with the public markedly warmer than the press"
    if gap >= 2:
        return "with the public somewhat warmer than the press"
    if gap <= -6:
        return "with the public markedly harsher than the press"
    if gap <= -2:
        return "with the public somewhat harsher than the press"
    return "with public sentiment broadly in line with the press"


def _dir_word(delta: float, flat: float = 0.5) -> str:
    if delta > flat:
        return "rising"
    if delta < -flat:
        return "falling"
    return "roughly flat"


def _fmt(v: float | None, d: int = 1) -> str:
    return "—" if v is None else f"{v:+.{d}f}"


# ---------------------------------------------------------------------
# rule-based composer
# ---------------------------------------------------------------------
def _rule_based(b: dict) -> dict:
    label = b.get("topic", {}).get("label", "This topic")
    media = b.get("media_series") or []
    avg_media = b.get("avg_media")
    avg_public = b.get("avg_public")
    gap = b.get("avg_gap")
    stats = b.get("stats", {})

    if not media:
        return {"headline": f"Not enough data to analyse {label} yet.",
                "summary": "No coverage was found for this topic in the window.",
                "points": []}

    first = media[0]["avg_tone"]
    last = media[-1]["avg_tone"]
    trend = last - first

    # forecast direction (last projected vs last observed)
    fpts = (b.get("forecast") or {}).get("points") or []
    fdir = None
    if fpts:
        fdir = _dir_word(fpts[-1]["forecast"] - last)

    tone_w = _tone_word(avg_media)

    # --- headline ---
    headline = (f"Media coverage of {label} is {tone_w}"
                + (f", {_gap_phrase(gap)}." if gap is not None else "."))

    # --- summary paragraph ---
    age = b.get("age_weeks", len(media))
    parts = [
        f"Over {age} weeks (since {b.get('inception', 'inception')}), coverage of "
        f"{label} has averaged {_fmt(avg_media)} on the −100…+100 tone scale — {tone_w}.",
    ]
    if avg_public is not None:
        parts.append(
            f"Public/social sentiment sits at {_fmt(avg_public)} (a {_fmt(gap)} gap), "
            f"{_gap_phrase(gap)}.")
    trend_sentence = f"The recent trend is {_dir_word(trend)} ({_fmt(trend)} over the window)"
    if fdir:
        trend_sentence += f", and the short-term forecast points {fdir}"
    parts.append(trend_sentence + ".")
    summary = " ".join(parts)

    # --- key points ---
    points: list[str] = []
    points.append(f"Overall media tone: {_fmt(avg_media)} ({tone_w}).")
    if gap is not None:
        points.append(f"Media↔public gap: {_fmt(gap)} — {_gap_phrase(gap)}.")

    anomalies = b.get("anomalies") or []
    if anomalies:
        big = max(anomalies, key=lambda a: abs(a.get("shift", 0)))
        points.append(
            f"A statistically unusual {big.get('direction', '')} shift occurred around "
            f"{big.get('week_start')} — worth a closer look.")
    else:
        points.append("No statistically unusual weekly shifts were detected.")

    drv = b.get("drivers") or {}
    if drv.get("spike_week") and drv.get("topics"):
        words = ", ".join(drv["topics"][0]["words"][:4])
        points.append(f"Around the biggest swing ({drv['spike_week']}), coverage "
                      f"centred on: {words}.")

    bc = b.get("by_country") or []
    if len(bc) >= 2:
        neg, pos = bc[0], bc[-1]  # sorted ascending by tone
        points.append(
            f"Geographically, coverage is most negative in {neg['country_name']} "
            f"({_fmt(neg['avg_tone'])}) and most positive in {pos['country_name']} "
            f"({_fmt(pos['avg_tone'])})"
            + (" (modelled distribution)." if stats.get("geo_modelled") else "."))

    # confidence / provenance
    lcw, nw = stats.get("low_conf_weeks", 0), stats.get("n_weeks", len(media))
    prov = f"Based on {stats.get('source_media', 'synthetic')} media"
    if stats.get("source_opinion"):
        prov += f" + {stats['source_opinion']} social"
    prov += f" data; {lcw} of {nw} weeks had thin, low-confidence coverage."
    points.append(prov)

    return {"headline": headline, "summary": summary, "points": points}


# ---------------------------------------------------------------------
# optional LLM backend (guarded)
# ---------------------------------------------------------------------
def _metrics_digest(b: dict) -> str:
    s = b.get("stats", {})
    drv = b.get("drivers") or {}
    bc = b.get("by_country") or []
    lines = [
        f"topic: {b.get('topic', {}).get('label')}",
        f"weeks_of_history: {b.get('age_weeks')}",
        f"avg_media_tone: {b.get('avg_media')}",
        f"avg_public_sentiment: {b.get('avg_public')}",
        f"media_public_gap: {b.get('avg_gap')}",
        f"anomalies_flagged: {len(b.get('anomalies') or [])}",
        f"spike_week: {drv.get('spike_week')}",
        f"spike_topics: {[t['words'][:4] for t in (drv.get('topics') or [])[:2]]}",
        f"most_negative_country: {bc[0]['country_name'] if bc else None} "
        f"({bc[0]['avg_tone'] if bc else None})",
        f"most_positive_country: {bc[-1]['country_name'] if bc else None} "
        f"({bc[-1]['avg_tone'] if bc else None})",
        f"data_source: media={s.get('source_media')} social={s.get('source_opinion')}",
        f"low_confidence_weeks: {s.get('low_conf_weeks')}/{s.get('n_weeks')}",
    ]
    return "\n".join(lines)


def _llm_narrative(b: dict) -> dict | None:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    try:
        import json
        import anthropic
        model = os.getenv("GPST_NARRATIVE_MODEL", "claude-haiku-4-5-20251001")
        client = anthropic.Anthropic(api_key=api_key)
        system = (
            "You are a careful political-media analyst. From the metrics, write a "
            "brief, hedged explanation of what the coverage looks like. This is "
            "MEDIA and SOCIAL sentiment, NOT public opinion — never present it as "
            "fact or a poll. Return ONLY JSON: {\"headline\": str, \"summary\": "
            "str (2-4 sentences), \"points\": [str, ...] (3-5 bullets)}.")
        msg = client.messages.create(
            model=model, max_tokens=600, system=system,
            messages=[{"role": "user", "content": _metrics_digest(b)}])
        text = "".join(blk.text for blk in msg.content if getattr(blk, "type", "") == "text")
        data = json.loads(text[text.find("{"): text.rfind("}") + 1])
        if isinstance(data, dict) and data.get("summary"):
            return {"headline": data.get("headline", ""),
                    "summary": data["summary"],
                    "points": list(data.get("points", []))}
    except Exception:
        return None
    return None


def generate_narrative(bundle: dict, *, backend: str | None = None) -> dict:
    backend = (backend or os.getenv("GPST_NARRATIVE", "rules")).lower()
    if backend in ("anthropic", "llm"):
        llm = _llm_narrative(bundle)
        if llm:
            return {**llm, "backend": "anthropic"}
    return {**_rule_based(bundle), "backend": "rules"}
