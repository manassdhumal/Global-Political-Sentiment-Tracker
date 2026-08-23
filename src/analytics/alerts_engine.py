"""Custom User Watchlists & Threshold Alert Engine."""
from __future__ import annotations

from typing import Any
from datetime import datetime, timezone
import numpy as np

from src.topics.catalog import resolve_topic, load_catalog
from src.topics.synth import global_weekly


DEFAULT_WATCHLIST_PRESETS: list[dict[str, Any]] = [
    {
        "id": "geopolitical_flashpoints",
        "name": "Geopolitical Flashpoints",
        "description": "Active conflict zones, military postures, and strategic chokepoints.",
        "icon": "ShieldAlert",
        "color": "#ef4444",
        "topic_ids": ["ukraine_war", "middle_east", "taiwan", "red_sea_security", "sahel_coups"],
    },
    {
        "id": "macro_energy_inflation",
        "name": "Macro Energy & Cost of Living",
        "description": "Commodity price shocks, central bank interest rates, and inflation drivers.",
        "icon": "TrendingUp",
        "color": "#f59e0b",
        "topic_ids": ["inflation", "housing", "trade_tariffs", "us_fed", "opec"],
    },
    {
        "id": "us_electoral_dynamics",
        "name": "US Electoral & Policy Dynamics",
        "description": "Key political figures, partisan polarization, and judicial branches.",
        "icon": "Vote",
        "color": "#3b82f6",
        "topic_ids": ["donald_trump", "kamala_harris", "us_democrats", "us_republicans", "us_supreme_court"],
    },
    {
        "id": "tech_resource_sovereignty",
        "name": "Tech & Resource Sovereignty",
        "description": "Semiconductor export controls, AI safety governance, and critical mineral supply.",
        "icon": "Cpu",
        "color": "#10b981",
        "topic_ids": ["chip_wars", "ai_regulation", "critical_minerals", "cyberwarfare"],
    },
]


def _compute_severity_score(delta_tone: float, latest_tone: float, std_4w: float, volume_ratio: float) -> int:
    """Composite severity score (0–100) combining tone plunge, volatility, and volume signals."""
    tone_component = min(40, int(abs(delta_tone) * 12))
    level_component = min(30, int(max(0, -latest_tone) * 5))
    vol_component = min(20, int(std_4w * 10))
    volume_component = min(10, int((volume_ratio - 1.0) * 5)) if volume_ratio > 1.0 else 0
    return tone_component + level_component + vol_component + volume_component


def evaluate_watchlist(watchlist_id: str, topic_ids: list[str]) -> dict[str, Any]:
    """Compute aggregated portfolio sentiment, individual member telemetry, and triggered alert conditions."""
    member_stats = []
    tones = []
    vols = []
    active_alerts = []
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    for tid in topic_ids:
        t_meta = resolve_topic(tid)
        df = global_weekly(tid)
        if df.empty:
            continue

        raw_tones = df["avg_tone"].to_numpy()
        latest_tone = round(float(raw_tones[-1]), 2)
        prev_tone = round(float(raw_tones[-2]), 2) if len(raw_tones) > 1 else latest_tone
        delta_tone = round(latest_tone - prev_tone, 2)

        avg_vol = int(df["article_volume"].mean()) if "article_volume" in df else 4500
        latest_vol = int(df["article_volume"].iloc[-1]) if "article_volume" in df else avg_vol
        volume_ratio = latest_vol / max(avg_vol, 1)

        tones.append(latest_tone)
        vols.append(avg_vol)

        # Volatility metric
        std_4w = round(float(np.std(raw_tones[-4:])), 2) if len(raw_tones) >= 4 else 0.4

        # Rule 1: Acute sentiment plunge
        if delta_tone <= -1.8 or latest_tone <= -4.0:
            sev = _compute_severity_score(delta_tone, latest_tone, std_4w, volume_ratio)
            active_alerts.append({
                "id": f"alert_tone_{tid}",
                "topic_id": tid,
                "topic_label": t_meta.label,
                "type": "TONE_PLUNGE",
                "severity": "high",
                "severity_score": min(100, sev + 20),
                "message": f"Sharp negative sentiment plunge ({delta_tone:+0.2f} pts) detected for {t_meta.label}.",
                "timestamp": now_str,
                "value": latest_tone,
            })

        # Rule 2: High volatility burst
        if std_4w > 1.25:
            sev = _compute_severity_score(delta_tone, latest_tone, std_4w, volume_ratio)
            active_alerts.append({
                "id": f"alert_vol_{tid}",
                "topic_id": tid,
                "topic_label": t_meta.label,
                "type": "VOLATILITY_BURST",
                "severity": "medium",
                "severity_score": min(100, sev),
                "message": f"Elevated 4-week narrative volatility (σ = {std_4w}) indicating rapid media narrative churn.",
                "timestamp": now_str,
                "value": std_4w,
            })

        # Rule 3: Positive sentiment surge (bullish momentum)
        if delta_tone >= 1.8 or latest_tone >= 3.5:
            sev = _compute_severity_score(delta_tone, latest_tone, std_4w, volume_ratio)
            active_alerts.append({
                "id": f"alert_surge_{tid}",
                "topic_id": tid,
                "topic_label": t_meta.label,
                "type": "POSITIVE_SURGE",
                "severity": "low",
                "severity_score": min(100, sev),
                "message": f"Bullish sentiment surge ({delta_tone:+0.2f} pts) detected for {t_meta.label} — monitor for reversal risk.",
                "timestamp": now_str,
                "value": latest_tone,
            })

        # Rule 4: Coverage/volume spike (2.5x baseline)
        if volume_ratio >= 2.5:
            sev = _compute_severity_score(delta_tone, latest_tone, std_4w, volume_ratio)
            active_alerts.append({
                "id": f"alert_cov_{tid}",
                "topic_id": tid,
                "topic_label": t_meta.label,
                "type": "COVERAGE_SPIKE",
                "severity": "medium",
                "severity_score": min(100, sev + 10),
                "message": f"Coverage volume spike ({volume_ratio:.1f}x baseline) for {t_meta.label} — breaking news signal.",
                "timestamp": now_str,
                "value": round(volume_ratio, 2),
            })

        member_stats.append({
            "id": tid,
            "label": t_meta.label,
            "category": t_meta.category,
            "latest_tone": latest_tone,
            "delta_tone": delta_tone,
            "volume": avg_vol,
            "volatility_4w": std_4w,
            "status": "critical" if latest_tone < -3.0 else "neutral" if abs(latest_tone) <= 1.0 else "positive" if latest_tone > 1.0 else "negative",
        })

    # Sort alerts by severity_score descending
    active_alerts.sort(key=lambda a: a.get("severity_score", 0), reverse=True)

    basket_tone = round(float(np.mean(tones)), 2) if tones else 0.0
    total_volume = int(np.sum(vols)) if vols else 0

    return {
        "id": watchlist_id,
        "basket_tone": basket_tone,
        "total_volume": total_volume,
        "member_count": len(member_stats),
        "members": member_stats,
        "active_alerts": active_alerts,
        "evaluated_at": now_str,
    }


def list_all_watchlists() -> list[dict[str, Any]]:
    """Retrieve all preset and default watchlists with current metrics."""
    results = []
    for wl in DEFAULT_WATCHLIST_PRESETS:
        eval_data = evaluate_watchlist(wl["id"], wl["topic_ids"])
        results.append({
            **wl,
            **eval_data,
        })
    return results


def get_global_unread_alerts() -> list[dict[str, Any]]:
    """Aggregate all current active alert triggers across all default watchlists."""
    all_alerts = []
    seen = set()
    for wl in DEFAULT_WATCHLIST_PRESETS:
        eval_data = evaluate_watchlist(wl["id"], wl["topic_ids"])
        for a in eval_data["active_alerts"]:
            if a["id"] not in seen:
                seen.add(a["id"])
                all_alerts.append({**a, "watchlist_name": wl["name"]})
    # Sort globally by severity_score
    all_alerts.sort(key=lambda a: a.get("severity_score", 0), reverse=True)
    return all_alerts
