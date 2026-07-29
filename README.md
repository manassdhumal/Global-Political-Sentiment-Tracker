# 🌍 Global Political Sentiment Tracker

[![CI](https://github.com/manassdhumal/Global-Political-Sentiment-Tracker/actions/workflows/ci.yml/badge.svg)](https://github.com/manassdhumal/Global-Political-Sentiment-Tracker/actions/workflows/ci.yml)

Tracks how the world's **news media** and **social platforms** feel about
political figures, parties, and issues — across countries and over time.
Media tone comes from [GDELT](https://www.gdeltproject.org/); public/social
sentiment comes from Reddit + Bluesky posts scored by a local RoBERTa model.

> **Measures media & social sentiment — not public opinion.** Media tone is how
> the *press* frames a subject; social sentiment is *vocal, non-representative*
> users. Neither is a poll. The **gap between them** is the interesting signal.
> Thin coverage is flagged low-confidence; translation, sarcasm, and outlet bias
> all affect tone.

## Three focused sections

1. **Trending** — what's moving right now: a global snapshot, the biggest
   rising/falling topics, and a live trending grid (attention + sentiment shift).
2. **Browse topics** — the full catalog (people, parties, issues, institutions,
   geopolitics), searchable and filterable by category.
3. **Analyze a topic** — the system is **open-ended**: type *any* topic (a person,
   party, issue, or free-text phrase) and get its full analysis on one page —
   **media vs public** sentiment over its **entire history** (since the topic first
   appeared), forecast + anomalies, what's driving it (topic modeling), and
   coverage by country and language.

Each topic's timeline runs from its own **inception**, so histories span years and
vary in length by topic. Every insight is on one page — no navigation maze.

## Architecture

```
config/           topics.yaml (browse catalog) · watchlist.yaml · events.csv
src/topics/       open-ended, on-demand topic engine (catalog · synth · analyze · trending)
src/              ingestion · processing · storage · analytics · nlp · reporting
api/              FastAPI service exposing everything as JSON (/docs for Swagger)
frontend/         Next.js + React + Tailwind (3-section, dark-first, light/dark)
src/dashboard/    legacy Streamlit UI (deprecated — see below)
```

Topics are analysed **on demand** — media tone from GDELT, social sentiment from
Reddit/Bluesky scored by a local RoBERTa model. When live sources are
unavailable, a deterministic **synthetic fallback** generates a long history for
any topic (clearly flagged, never presented as real). The Python stack stays
lean; heavier backends are optional and auto-detected.

## Setup

Requires **Python 3.11+** and **Node.js 18+**.

```bash
pip install -r requirements.txt          # backend + pipelines
cd frontend && npm install && cd ..      # frontend
```

## Run

The v3 app analyses topics **on demand** — no pre-build step needed:

```bash
# 1. Start the API
uvicorn api.main:app --port 8000         # http://localhost:8000/docs

# 2. Start the frontend (separate terminal)
cd frontend && npm run dev               # http://localhost:3000
```

> **Offline-friendly.** GDELT rate-limits and Reddit/Bluesky need credentials —
> when unavailable, topic analysis falls back to deterministic **synthetic**
> data (a long history per topic), clearly flagged in the UI and never presented
> as real.

Optional legacy batch pipelines (feed the older aggregate endpoints + Streamlit):

```bash
python scripts/run_pipeline.py --source auto          # media
python scripts/run_opinion_pipeline.py --source auto  # public opinion
```

## Live data (optional)

Copy `.env.example` to `.env` and add credentials — the app reads them from
there (never commit `.env`):

- **Reddit**: create a "script" app at reddit.com/prefs/apps
- **Bluesky**: Settings → App Passwords

Without credentials everything still runs on synthetic data.

To make topic analysis prefer **live** data (GDELT media + social opinion, with
per-piece synthetic fallback), set `GPST_TOPIC_SOURCE=auto` — or pass
`?source=auto` to `/api/topic`. Each topic page shows its actual data source
(`media: gdelt-bq/gdelt-doc/synthetic`, `social: reddit+bluesky/synthetic`).

**Real history via BigQuery (no rate limits).** For genuine multi-year data,
enable GDELT's public GKG table on BigQuery:

```bash
pip install google-cloud-bigquery
# authenticate (ADC or a service account), then:
export GPST_BQ_PROJECT=your-gcp-project      # GPST_BQ_MAX_GB caps query cost
```

With `source=auto`, media falls back BigQuery → DOC API → synthetic. Queries are
cost-guarded (partitioned table, date filter, `maximum_bytes_billed`).

**Live trending (precompute).** Ranking the whole catalog from live data is too
many queries per request, so a job precomputes it into a cache the API serves:

```bash
python scripts/precompute_trending.py --source auto   # run hourly via cron / Task Scheduler
```

`/api/trending` serves the cached snapshot when fresh, else computes synthetically
on the fly.

## Deploy

Ship the frontend to **Vercel** and the API as a **container** (Render/Railway/
Fly). The repo includes a lean [`Dockerfile`](Dockerfile), [`render.yaml`](render.yaml),
and a full step-by-step in **[DEPLOY.md](DEPLOY.md)**. CORS is env-configurable
(`GPST_CORS_ORIGINS`); the frontend points at the API via `NEXT_PUBLIC_API_BASE`.

## Topics

You don't need to register a topic to analyse it — **type anything** on the
"Analyze a topic" page. To add a topic to the **Browse catalog / Trending**
pool, add an entry to [`config/topics.yaml`](config/topics.yaml):

```yaml
topics:
  - {id: my_topic, label: My Topic, query: "my topic", category: issue}
    # category: figure | party | issue | institution | geopolitics
```

## Tests

```bash
pytest -q
```

## Legacy Streamlit app

The original UI (`streamlit run src/dashboard/app.py`) still works and is a
dependency-light fallback, but it's **deprecated** in favour of the React
frontend, which adds the media-vs-public views.
