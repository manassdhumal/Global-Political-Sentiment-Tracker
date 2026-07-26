"""Storage layer: SQLite schema init + persistence helpers."""
from .db import (  # noqa: F401
    connect,
    init_db,
    sync_entities,
    upsert_articles,
    upsert_aggregated_scores,
    read_aggregated_scores,
    list_entities,
    read_language_summary,
    read_titles,
)
