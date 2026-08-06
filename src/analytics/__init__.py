"""Reusable analytics: aggregation, volatility, issue association.

Pure pandas functions over the aggregated_scores frame, kept separate from
the dashboard so they can be unit-tested and reused by later phases.
All 'tone' values are MEDIA COVERAGE TONE, not public opinion.
"""
from .metrics import (  # noqa: F401
    weekly_weighted_series,
    country_tone_summary,
    volatility_index,
    issue_association,
)
from .forecast import forecast_tone, ForecastResult  # noqa: F401
from .anomaly import detect_anomalies, biggest_spike_week  # noqa: F401
from .topics import extract_topics, Topic  # noqa: F401
from .impact import event_impact, ImpactResult  # noqa: F401
from .framing import domestic_vs_foreign, by_language  # noqa: F401
from .compare import (  # noqa: F401
    media_vs_public, media_weekly, public_weekly, divergence_summary)
from .correlation import (  # noqa: F401
    compute_pairwise_correlation, compute_lead_lag, analyze_topic_correlations)
