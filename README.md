# 🌍 Global Political Sentiment Tracker

Tracks the **tone of news coverage** toward political figures, parties, and
issues — over time and across countries — using [GDELT](https://www.gdeltproject.org/)
as the primary signal.

> **What this measures — read this first.**
> This system measures **media sentiment (the tone of news _coverage_)**, **not
> public opinion**. A score of “−4 for Entity X in France” means French-origin
> coverage of X leaned negative — it is **not** a poll of French people. Known
> limitations: translation artifacts, sarcasm/irony, and outlet bias all affect
> tone; GDELT coverage is sparse for smaller countries and languages. These
> caveats are surfaced throughout the UI on purpose.

---

## Status

| Phase | Scope | State |
|-------|-------|-------|
| **Phase 1** | MVP pipeline: config → GDELT ingest → clean → SQLite → weekly aggregate → tone-over-time dashboard | ✅ complete |
| **Phase 2** | Scale (26 countries / 22 entities) + comparison: choropleth world map, cross-country, entity-vs-entity, issue drill-down, volatility index, event annotation layer | ✅ complete |
| **Phase 3** | Intelligence layer: ARIMA forecasting, anomaly/early-warning detection, LDA topic modeling on spikes, event impact scoring, cross-language framing | ✅ complete |
| **Phase 4** | User text analysis (aspect-based + explainability), political-mood homepage, global search, exportable reports (MD/PDF), data-integrity + methodology page, tests | ✅ complete |

## Architecture

Modules are cleanly separated so later phases slot in without rewrites:

```
config/
  watchlist.yaml          # SINGLE SOURCE OF TRUTH — what we track (no hardcoded names)
  events.csv              # event annotation layer (markers on timelines)
src/
  config.py               # load + validate watchlist + events
  ingestion/
    gdelt_client.py       # GDELT DOC 2.0 API client (retry/backoff)
    synthetic.py          # deterministic offline FALLBACK (fabricated data)
    ingest.py             # orchestrator — one interface over both sources
  processing/
    clean.py              # dedupe, standardize country codes + dates
    aggregate.py          # roll up to entity × country × ISO-week
  storage/
    schema.sql            # articles / entities / aggregated_scores
    db.py                 # SQLite connection + upserts + read helpers
  analytics/              # reusable pandas analytics (Phase 2-3)
    metrics.py            # weighted series, country summary, volatility, issue association
    forecast.py           # ARIMA + linear-fallback tone forecasting
    anomaly.py            # robust anomaly / early-warning detection
    topics.py             # sklearn LDA topic modeling on spikes
    impact.py             # before/after event impact + t-test
    framing.py            # domestic-vs-foreign + by-language framing
  nlp/                    # shared user-text engine (Phase 4)
    sentiment.py          # pluggable scorer: VADER default, transformers optional
    entities.py           # watchlist/alias match + optional spaCy NER
    aspect.py             # per-entity aspect sentiment
    explain.py            # leave-one-out explainability
    emotion.py            # optional keyword emotion breakdown
    pipeline.py           # analyze_text() orchestrator
  reporting/
    report.py             # entity/country summary -> markdown + PDF (fpdf2)
  dashboard/
    app.py                # Streamlit multipage shell (st.navigation, 14 pages)
    common.py             # cached data loading + shared helpers + event markers
    views/                # one module per page (see below)
scripts/
  run_pipeline.py         # end-to-end: ingest → clean → store → aggregate
tests/                    # pytest: ingestion, processing, analytics, sentiment
data/sentiment.db         # SQLite DB (git-ignored, created on first run)
```

### Dashboard views (Phase 2)

- **World map** — Plotly choropleth, average coverage tone per country for a
  chosen entity/issue + date range (blue = positive, red = negative).
- **Tone over time** — single entity, volume + low-confidence markers + events.
- **Cross-country** — same entity/issue across countries (domestic vs foreign framing).
- **Entity vs entity** — several entities compared, globally or within one country.
- **Issue drill-down** — for a theme, which countries cover it most and with what tone.
- **Volatility index** — most-swinging entities/countries by std-dev of weekly tone.

Known events in `config/events.csv` (date, scope_type, scope_id, label) render as
markers on all timeline charts.

### Intelligence views (Phase 3)

- **Forecast & alerts** — ARIMA short-term tone projection with a 95% band
  (numpy linear fallback for short series), robust anomaly/early-warning flags,
  and LDA topic modeling on the biggest recent swing to summarize what's driving it.
- **Event impact** — before/after tone delta around an event (from `events.csv`
  or a custom date), with a Welch t-test significance read.
- **Cross-language framing** — domestic vs foreign press tone, plus tone broken
  down by source language.

Analytics live in `src/analytics/` (`forecast.py`, `anomaly.py`, `topics.py`,
`impact.py`, `framing.py`) so they're reusable and testable. Topic modeling uses
scikit-learn LDA (not BERTopic) and forecasting uses statsmodels ARIMA (not
Prophet) for lean, Python-3.13-friendly installs — both heavier libraries remain
documented upgrade paths.

### Your-text & reports (Phase 4)

- **Political mood** (homepage) — global snapshot + biggest weekly movers +
  early-warning flags.
- **Search** — find any tracked entity/theme by name or alias, with a sparkline.
- **Analyze text** — paste text; get an overall −100…+100 score, detected
  entities, **per-entity aspect sentiment** (a separate score each, not one
  blend), **explainability** highlighting (which words drove the score, via
  leave-one-out), comparison against the live aggregate trend, and an optional
  emotion breakdown. Runs the shared `src/nlp` engine (VADER by default;
  transformers auto-used if installed).
- **Reports** — export a media-sentiment summary for an entity or country as
  **Markdown or PDF**.
- **Methodology** — what the tool measures (media tone, not public opinion), the
  data-integrity signals, and the known limitations.

## Setup

Requires **Python 3.11+** (developed on 3.13).

```bash
pip install -r requirements.txt
```

The stack is intentionally lean: pandas, numpy, PyYAML, requests/httpx,
streamlit, plotly, statsmodels, scipy, scikit-learn, vaderSentiment, fpdf2
(SQLite is stdlib). **Optional** heavier backends are auto-detected if you
install them — `transformers`+`torch` (RoBERTa sentiment) and
`spacy`+`en_core_web_sm` (NER) — but nothing requires them; the app is fully
functional without.

## Run it

**1. Build the database** (ingest → clean → store → aggregate):

```bash
# Try live GDELT, fall back to synthetic data if the API is unavailable:
python scripts/run_pipeline.py --source auto

# Force the deterministic offline demo dataset:
python scripts/run_pipeline.py --source synthetic --weeks 16

# Force live GDELT only:
python scripts/run_pipeline.py --source gdelt
```

> **GDELT rate-limiting:** GDELT's free DOC API throttles aggressively (HTTP
> 429). When it's unavailable, `--source auto` transparently falls back to a
> **synthetic (fabricated) dataset** so the whole pipeline stays runnable and
> testable offline. Synthetic rows are tagged `source='synthetic'` in the DB and
> the dashboard shows a clear banner — they are **never** presented as real
> coverage.

**2. Launch the dashboard:**

```bash
streamlit run src/dashboard/app.py
```

The app opens on the **Political mood** homepage, with 14 pages grouped into
**Overview · Explore · Intelligence · Your text & reports** in the sidebar.

## The watchlist config (how to add a tracked entity)

Everything the system tracks lives in [`config/watchlist.yaml`](config/watchlist.yaml).
**No entity/country/theme name is ever hardcoded in pipeline code.** To track
something new, add an entry and re-run the pipeline:

```yaml
entities:
  - id: some_id            # stable, unique, snake_case
    name: Display Name
    type: figure           # figure | party | theme
    home_country: US       # GDELT country code, or null for cross-cutting themes
    query: '"Display Name"' # GDELT DOC 2.0 query fragment
    aliases: ["Nickname"]
```

Then:

```bash
python scripts/run_pipeline.py --source synthetic
```

The new entity is pulled, aggregated, and appears in the dashboard dropdown on
refresh. (This config → track → pull → aggregate → visualize loop is the
Phase 1 acceptance test.)

Countries are configured similarly, each with a GDELT source-country code and an
ISO-3 code (used by the Phase 2 choropleth).

## Data model

- **`articles`** — one row per article: entity, country, url, domain, language,
  date, tone, and `source` (`gdelt` | `synthetic`).
- **`entities`** — mirror of the watchlist config.
- **`aggregated_scores`** — one row per **entity × country × ISO-week**:
  `avg_tone`, `article_volume`, `source_diversity` (distinct outlets), and a
  `low_confidence` flag for weeks with thin coverage.

## Tests

```bash
pytest -q
```

Covers the core modules: synthetic ingestion (determinism, schema), cleaning +
aggregation (dedupe, country/date normalization, low-confidence flagging),
analytics (weighted series, volatility, forecast, anomaly, event impact), and
the NLP engine (scale/polarity, **aspect scores are separate per entity**,
watchlist entity detection, explainability drivers).

## Responsible-use notes

- **Source diversity** and **low-confidence flags** are computed at aggregation
  and surfaced across the UI, so thin/one-outlet weeks are visible.
- All copy describes results as **media / coverage sentiment**, never as public
  opinion. The **Methodology** page documents the full list of limitations.
- Synthetic fallback data is always tagged and banner-flagged — never presented
  as real coverage.
