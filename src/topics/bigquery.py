"""GDELT BigQuery media source — real, rate-limit-free weekly tone + volume.

Queries GDELT's public GKG table on BigQuery for a topic's weekly average tone
and article volume. Unlike the DOC API this has no rate limit and full history,
but BigQuery bills by bytes scanned, so this module is **cost-guarded**:
  * queries the DATE-partitioned GKG table with a date filter,
  * selects only the columns it needs,
  * caps the query with `maximum_bytes_billed`.

Opt-in and untested where BigQuery isn't configured — everything is lazy and
guarded, returning None so callers fall back to the DOC API or synthetic data.

Setup: `pip install google-cloud-bigquery`, authenticate (ADC or a service
account via GOOGLE_APPLICATION_CREDENTIALS), and set GPST_BQ_PROJECT.
"""
from __future__ import annotations

import logging
import os
from datetime import date

import pandas as pd

log = logging.getLogger(__name__)

# DATE-partitioned public GKG table (partition column: _PARTITIONTIME).
_TABLE = "gdelt-bq.gdeltv2.gkg_partitioned"
_DEFAULT_MAX_GB = float(os.getenv("GPST_BQ_MAX_GB", "8"))
# Cap the window scanned per query to keep bytes/cost bounded (weeks).
_MAX_WINDOW_WEEKS = int(os.getenv("GPST_BQ_MAX_WEEKS", "104"))


def bq_available() -> bool:
    try:
        import google.cloud.bigquery  # noqa: F401
    except Exception:
        return False
    return bool(os.getenv("GPST_BQ_PROJECT"))


def bq_media_weekly(query: str, start: date, end: date, *,
                    project: str | None = None,
                    max_gb: float = _DEFAULT_MAX_GB) -> pd.DataFrame | None:
    """Weekly (week_start, avg_tone, article_volume) for a topic, or None.

    `query` is matched (case-insensitive) against the GKG entity/theme/name
    fields. Returns None on any misconfiguration or failure.
    """
    try:
        from google.cloud import bigquery
    except Exception:
        return None
    project = project or os.getenv("GPST_BQ_PROJECT")
    if not project:
        return None

    # bound the window to cap cost
    if (end - start).days > _MAX_WINDOW_WEEKS * 7:
        start = end - pd.Timedelta(weeks=_MAX_WINDOW_WEEKS).to_pytimedelta()

    phrase = query.replace('"', "").strip().lower()
    if not phrase:
        return None

    sql = f"""
    DECLARE q STRING DEFAULT @phrase;
    SELECT
      DATE_TRUNC(DATE(PARSE_TIMESTAMP('%Y%m%d%H%M%S', CAST(DATE AS STRING))), WEEK(MONDAY)) AS week_start,
      AVG(SAFE_CAST(SPLIT(V2Tone, ',')[SAFE_OFFSET(0)] AS FLOAT64)) AS avg_tone,
      COUNT(*) AS article_volume
    FROM `{_TABLE}`
    WHERE _PARTITIONTIME BETWEEN TIMESTAMP(@start) AND TIMESTAMP(@end)
      AND V2Tone IS NOT NULL
      AND (
        LOWER(V2Persons) LIKE CONCAT('%', q, '%')
        OR LOWER(V2Organizations) LIKE CONCAT('%', q, '%')
        OR LOWER(AllNames) LIKE CONCAT('%', q, '%')
        OR LOWER(V2Themes) LIKE CONCAT('%', q, '%')
      )
    GROUP BY week_start
    ORDER BY week_start
    """
    try:
        client = bigquery.Client(project=project)
        job_config = bigquery.QueryJobConfig(
            maximum_bytes_billed=int(max_gb * 1e9),
            query_parameters=[
                bigquery.ScalarQueryParameter("phrase", "STRING", phrase),
                bigquery.ScalarQueryParameter("start", "STRING", start.isoformat()),
                bigquery.ScalarQueryParameter("end", "STRING", end.isoformat()),
            ],
        )
        df = client.query(sql, job_config=job_config).to_dataframe()
    except Exception as exc:  # cost cap exceeded, auth, network, schema drift…
        log.warning("BigQuery media query failed for %r: %s", query, exc)
        return None
    if df.empty:
        return None
    df["week_start"] = pd.to_datetime(df["week_start"])
    df["avg_tone"] = df["avg_tone"].round(3)
    df["article_volume"] = df["article_volume"].astype(int)
    df["low_confidence"] = (df["article_volume"] < 5).astype(int)
    return df.reset_index(drop=True)
