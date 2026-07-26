-- =====================================================================
-- Global Political Sentiment Tracker — SQLite schema (Phase 1)
-- Grain of the analytical table: entity x country x ISO-week.
-- Reminder: `tone` columns hold MEDIA COVERAGE TONE, not public opinion.
-- =====================================================================

-- Mirror of the config watchlist entities, for FKs + dashboard display.
CREATE TABLE IF NOT EXISTS entities (
    id            TEXT PRIMARY KEY,        -- stable id from watchlist.yaml
    name          TEXT NOT NULL,
    type          TEXT NOT NULL,           -- figure | party | theme
    home_country  TEXT,                    -- GDELT country code or NULL
    query         TEXT NOT NULL            -- GDELT query fragment used
);

-- Per-article coverage metadata.
-- tone: -100..+100. May be a daily-average approximation when the source
-- (GDELT DOC 2.0 artlist) does not expose per-article tone — see
-- src/ingestion/gdelt_client.py for the documented limitation.
CREATE TABLE IF NOT EXISTS articles (
    id             TEXT PRIMARY KEY,       -- hash of (entity_id, country, url)
    entity_id      TEXT NOT NULL,
    country        TEXT NOT NULL,          -- GDELT source country code
    url            TEXT,
    title          TEXT,
    domain         TEXT,                   -- outlet domain (source diversity)
    language       TEXT,
    seen_date      TEXT NOT NULL,          -- UTC ISO-8601 (YYYY-MM-DD)
    tone           REAL,                   -- media coverage tone
    source         TEXT NOT NULL,          -- 'gdelt' | 'synthetic'
    FOREIGN KEY (entity_id) REFERENCES entities(id)
);
CREATE INDEX IF NOT EXISTS idx_articles_eck
    ON articles (entity_id, country, seen_date);

-- Aggregated scores: one row per entity x country x ISO-week.
CREATE TABLE IF NOT EXISTS aggregated_scores (
    entity_id        TEXT NOT NULL,
    country          TEXT NOT NULL,        -- GDELT source country code
    week_start       TEXT NOT NULL,        -- Monday of the ISO week (YYYY-MM-DD)
    avg_tone         REAL,                 -- mean media tone that week
    article_volume   INTEGER NOT NULL,     -- # articles feeding the score
    source_diversity INTEGER NOT NULL,     -- # distinct outlet domains
    low_confidence   INTEGER NOT NULL,     -- 1 if coverage too thin to trust
    updated_at       TEXT NOT NULL,        -- UTC ISO timestamp of last write
    PRIMARY KEY (entity_id, country, week_start),
    FOREIGN KEY (entity_id) REFERENCES entities(id)
);
CREATE INDEX IF NOT EXISTS idx_agg_entity
    ON aggregated_scores (entity_id, week_start);
