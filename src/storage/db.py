"""SQLite persistence: connection, schema init, and upserts.

Deliberately thin — plain sqlite3 + pandas. The upgrade path to
PostgreSQL/DuckDB (see project plan) only needs to swap this module.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import pandas as pd

from ..config import DEFAULT_DB_PATH, Watchlist

_SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def connect(db_path: str | Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Open a SQLite connection, creating the parent dir if needed."""
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    """Create tables/indexes if they don't already exist (idempotent)."""
    conn.executescript(_SCHEMA_PATH.read_text(encoding="utf-8"))
    conn.commit()


def sync_entities(conn: sqlite3.Connection, watchlist: Watchlist) -> None:
    """Mirror the config entities into the entities table (upsert)."""
    rows = [
        (e.id, e.name, e.type, e.home_country, e.query)
        for e in watchlist.entities
    ]
    conn.executemany(
        """
        INSERT INTO entities (id, name, type, home_country, query)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            name=excluded.name,
            type=excluded.type,
            home_country=excluded.home_country,
            query=excluded.query
        """,
        rows,
    )
    conn.commit()


def upsert_articles(conn: sqlite3.Connection, articles: pd.DataFrame) -> int:
    """Insert/replace article rows. Expects the cleaned article schema.

    Returns the number of rows written.
    """
    if articles.empty:
        return 0
    cols = ["id", "entity_id", "country", "url", "title",
            "domain", "language", "seen_date", "tone", "source"]
    df = articles.reindex(columns=cols)
    conn.executemany(
        f"""
        INSERT INTO articles ({",".join(cols)})
        VALUES ({",".join("?" for _ in cols)})
        ON CONFLICT(id) DO UPDATE SET
            title=excluded.title,
            tone=excluded.tone,
            seen_date=excluded.seen_date
        """,
        df.itertuples(index=False, name=None),
    )
    conn.commit()
    return len(df)


def upsert_aggregated_scores(conn: sqlite3.Connection, scores: pd.DataFrame) -> int:
    """Insert/replace aggregated (entity x country x week) rows."""
    if scores.empty:
        return 0
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    cols = ["entity_id", "country", "week_start", "avg_tone",
            "article_volume", "source_diversity", "low_confidence"]
    df = scores.reindex(columns=cols).copy()
    df["updated_at"] = now
    conn.executemany(
        """
        INSERT INTO aggregated_scores
            (entity_id, country, week_start, avg_tone, article_volume,
             source_diversity, low_confidence, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(entity_id, country, week_start) DO UPDATE SET
            avg_tone=excluded.avg_tone,
            article_volume=excluded.article_volume,
            source_diversity=excluded.source_diversity,
            low_confidence=excluded.low_confidence,
            updated_at=excluded.updated_at
        """,
        df[cols + ["updated_at"]].itertuples(index=False, name=None),
    )
    conn.commit()
    return len(df)


# ---------------------------------------------------------------------
# Read helpers (used by the dashboard)
# ---------------------------------------------------------------------
def read_aggregated_scores(
    conn: sqlite3.Connection,
    entity_ids: Iterable[str] | None = None,
    countries: Iterable[str] | None = None,
) -> pd.DataFrame:
    """Return aggregated_scores, optionally filtered by entity/country."""
    where, params = [], []
    if entity_ids:
        entity_ids = list(entity_ids)
        where.append(f"entity_id IN ({','.join('?' * len(entity_ids))})")
        params += entity_ids
    if countries:
        countries = list(countries)
        where.append(f"country IN ({','.join('?' * len(countries))})")
        params += countries
    sql = "SELECT * FROM aggregated_scores"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY week_start"
    df = pd.read_sql_query(sql, conn, params=params)
    if not df.empty:
        df["week_start"] = pd.to_datetime(df["week_start"])
    return df


def list_entities(conn: sqlite3.Connection) -> pd.DataFrame:
    """Return the entities table as a DataFrame."""
    return pd.read_sql_query("SELECT * FROM entities ORDER BY type, name", conn)


def read_language_summary(conn: sqlite3.Connection, entity_id: str,
                          w0: str | None = None, w1: str | None = None) -> pd.DataFrame:
    """Per-language article aggregation for an entity (for framing comparison).

    Returns columns: language, n, avg_tone, outlets. w0/w1 are ISO date strings.
    """
    sql = ("SELECT language, COUNT(*) AS n, AVG(tone) AS avg_tone, "
           "COUNT(DISTINCT domain) AS outlets FROM articles WHERE entity_id=?")
    params: list = [entity_id]
    if w0:
        sql += " AND seen_date >= ?"; params.append(w0)
    if w1:
        sql += " AND seen_date <= ?"; params.append(w1)
    sql += " GROUP BY language ORDER BY n DESC"
    return pd.read_sql_query(sql, conn, params=params)


def read_titles(conn: sqlite3.Connection, entity_id: str,
                w0: str | None = None, w1: str | None = None,
                country: str | None = None, limit: int = 2000) -> list[str]:
    """Article titles for an entity in a window (for topic modeling on spikes)."""
    sql = "SELECT title FROM articles WHERE entity_id=?"
    params: list = [entity_id]
    if country:
        sql += " AND country=?"; params.append(country)
    if w0:
        sql += " AND seen_date >= ?"; params.append(w0)
    if w1:
        sql += " AND seen_date <= ?"; params.append(w1)
    sql += " LIMIT ?"; params.append(limit)
    return [r[0] for r in conn.execute(sql, params).fetchall() if r[0]]
