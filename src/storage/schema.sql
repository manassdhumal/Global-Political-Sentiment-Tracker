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

-- =====================================================================
-- PUBLIC / SOCIAL OPINION layer (v2)
-- Posts from social platforms (Reddit, Bluesky) scored with a sentiment
-- MODEL (RoBERTa) — distinct from GDELT media tone. This is SOCIAL
-- sentiment (vocal, non-representative users), NOT representative public
-- opinion. Author handles are HASHED for privacy; raw text is kept short.
-- Opinion is aggregated per entity x source x week (global — social posts
-- rarely carry reliable country geo).
-- =====================================================================
CREATE TABLE IF NOT EXISTS opinion_posts (
    id            TEXT PRIMARY KEY,        -- hash of (source, entity_id, url/text)
    entity_id     TEXT NOT NULL,
    source        TEXT NOT NULL,           -- reddit | bluesky | synthetic
    community     TEXT,                     -- subreddit / feed (optional)
    lang          TEXT,
    text          TEXT,                     -- short snippet (for topic/QA)
    created_date  TEXT NOT NULL,            -- UTC ISO YYYY-MM-DD
    sentiment     REAL,                     -- model sentiment, -100..+100
    author_hash   TEXT,                     -- hashed author (privacy)
    url           TEXT,
    FOREIGN KEY (entity_id) REFERENCES entities(id)
);
CREATE INDEX IF NOT EXISTS idx_opinion_posts_esd
    ON opinion_posts (entity_id, source, created_date);

CREATE TABLE IF NOT EXISTS opinion_scores (
    entity_id       TEXT NOT NULL,
    source          TEXT NOT NULL,          -- reddit | bluesky | synthetic | all
    week_start      TEXT NOT NULL,          -- Monday (YYYY-MM-DD)
    avg_sentiment   REAL,                   -- mean model sentiment that week
    post_volume     INTEGER NOT NULL,       -- # posts feeding the score
    unique_authors  INTEGER NOT NULL,       -- distinct authors (diversity)
    low_confidence  INTEGER NOT NULL,       -- 1 if too few posts/authors
    updated_at      TEXT NOT NULL,
    PRIMARY KEY (entity_id, source, week_start),
    FOREIGN KEY (entity_id) REFERENCES entities(id)
);
CREATE INDEX IF NOT EXISTS idx_opinion_scores_entity
    ON opinion_scores (entity_id, week_start);
