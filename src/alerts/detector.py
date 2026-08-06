"""Sentiment shock and anomaly detection engine across topics and entities."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import numpy as np

from src.topics.trending import catalog_stats
from src.topics.analyze import analyze_topic


@dataclass
class SentimentShockAlert:
    topic_id: str
    topic_label: str
    category: str
    alert_type: str  # "sentiment_swing" | "attention_spike" | "divergence_widening" | "news_surge"
    severity: str    # "info" | "warning" | "critical"
    delta: float
    current_value: float
    description: str
    timestamp: str
    details: dict

    def to_dict(self) -> dict:
        return asdict(self)


def scan_catalog_alerts(
    threshold: float = 2.5,
    min_volume: int = 500,
    source: str = "synthetic",
) -> list[SentimentShockAlert]:
    """Scan all catalog topics for sudden sentiment swings, divergence, or volume anomalies."""
    stats = catalog_stats(source=source)
    alerts: list[SentimentShockAlert] = []
    now_iso = datetime.now(timezone.utc).isoformat()

    for item in stats:
        movement = float(item.get("movement", 0.0))
        abs_movement = abs(movement)
        recent_vol = int(item.get("recent_volume", 0))
        gap = item.get("gap")
        latest_tone = float(item.get("latest_tone", 0.0))

        # 1. Sentiment Swing Alert
        if abs_movement >= threshold:
            severity = "critical" if abs_movement >= threshold * 2.0 else "warning"
            direction = "surged upward" if movement > 0 else "plummeted downward"
            desc = (
                f"Topic '{item['label']}' sentiment {direction} by {movement:+.2f} pts "
                f"to a current score of {latest_tone:+.2f}."
            )
            alerts.append(
                SentimentShockAlert(
                    topic_id=item["id"],
                    topic_label=item["label"],
                    category=item["category"],
                    alert_type="sentiment_swing",
                    severity=severity,
                    delta=round(movement, 2),
                    current_value=round(latest_tone, 2),
                    description=desc,
                    timestamp=now_iso,
                    details={
                        "movement": movement,
                        "recent_volume": recent_vol,
                        "spark": item.get("spark", []),
                    },
                )
            )

        # 2. Public vs Media Divergence Widening Alert
        if gap is not None and abs(gap) >= 12.0 and recent_vol >= min_volume:
            div_dir = "public far more optimistic than media" if gap > 0 else "public far more critical than media"
            desc = (
                f"Severe sentiment divergence detected for '{item['label']}': "
                f"public sentiment sits {abs(gap):.1f} pts away from press coverage ({div_dir})."
            )
            alerts.append(
                SentimentShockAlert(
                    topic_id=item["id"],
                    topic_label=item["label"],
                    category=item["category"],
                    alert_type="divergence_widening",
                    severity="warning" if abs(gap) < 20.0 else "critical",
                    delta=round(gap, 2),
                    current_value=round(gap, 2),
                    description=desc,
                    timestamp=now_iso,
                    details={"gap": gap, "latest_tone": latest_tone, "volume": recent_vol},
                )
            )

    # Sort alerts by severity (critical first) then delta magnitude
    severity_order = {"critical": 0, "warning": 1, "info": 2}
    alerts.sort(key=lambda a: (severity_order.get(a.severity, 3), -abs(a.delta)))
    return alerts


def scan_live_topic_alert(query_or_slug: str, source: str | None = None) -> list[SentimentShockAlert]:
    """Perform on-demand deep shock scan for a specific topic query."""
    data = analyze_topic(query_or_slug, source=source)
    alerts: list[SentimentShockAlert] = []
    now_iso = datetime.now(timezone.utc).isoformat()
    topic = data["topic"]

    # Check anomalies from forecast/time-series
    for anom in data.get("anomalies", []):
        tone = float(anom.get("avg_tone", 0.0))
        alerts.append(
            SentimentShockAlert(
                topic_id=topic["id"],
                topic_label=topic["label"],
                category=topic["category"],
                alert_type="sentiment_swing",
                severity="warning",
                delta=tone,
                current_value=tone,
                description=f"Statistical anomaly detected in week {anom['week_start']}: coverage tone shifted to {tone:+.2f}.",
                timestamp=now_iso,
                details=anom,
            )
        )

    # Check Wikipedia attention surge if attention data available
    att_series = data.get("attention_series", [])
    if len(att_series) >= 4:
        views = np.array([row["pageviews"] for row in att_series], dtype=float)
        mean_v = float(views[:-1].mean())
        std_v = float(views[:-1].std() or 1.0)
        latest_v = float(views[-1])
        z_score = (latest_v - mean_v) / std_v

        if z_score >= 2.5:
            delta_pct = round(((latest_v - mean_v) / max(mean_v, 1.0)) * 100, 1)
            alerts.append(
                SentimentShockAlert(
                    topic_id=topic["id"],
                    topic_label=topic["label"],
                    category=topic["category"],
                    alert_type="attention_spike",
                    severity="critical" if z_score >= 4.0 else "warning",
                    delta=round(z_score, 2),
                    current_value=latest_v,
                    description=f"Wikipedia attention spike! Traffic surged +{delta_pct}% ({int(latest_v):,} weekly pageviews, z-score: {z_score:.2f}).",
                    timestamp=now_iso,
                    details={"latest_views": latest_v, "mean_views": mean_v, "z_score": round(z_score, 2)},
                )
            )

    return alerts
