# 🌍 Global Political Sentiment Tracker

Tracks how the world's **news media** and **social platforms** feel about
political figures, parties, and issues — across countries and over time.
Media tone comes from [GDELT](https://www.gdeltproject.org/); public/social
sentiment comes from Reddit + Bluesky posts scored by a local RoBERTa model.

> **Measures media & social sentiment — not public opinion.** Media tone is how
> the *press* frames a subject; social sentiment is *vocal, non-representative*
> users. Neither is a poll. The **gap between them** is the interesting signal.
> Thin coverage is flagged low-confidence; translation, sarcasm, and outlet bias
> all affect tone.

## Features

- **World map** choropleth of coverage tone per country; cross-country,
  entity-vs-entity, and issue drill-downs.
- **Media vs Public** — press tone vs social sentiment per entity, and the gap.
- **Intelligence**: short-term forecasting, anomaly/early-warning detection,
  topic modeling on spikes, event-impact scoring, cross-language framing.
- **Analyze your own text**: overall score, per-entity **aspect-based** sentiment,
  explainability highlighting, and comparison against the live trend.
- **Political-mood homepage**, global search, exportable reports (Markdown/PDF),
  volatility index, event annotations, and a methodology page.
- Fully **config-driven** watchlist — no tracked names hardcoded.

## Architecture

```
config/           watchlist.yaml + events.csv (single source of truth)
src/              ingestion · processing · storage · analytics · nlp · reporting
api/              FastAPI service exposing everything as JSON (/docs for Swagger)
frontend/         Next.js + React + Tailwind dashboard (dark-first, light/dark)
src/dashboard/    legacy Streamlit UI (deprecated — see below)
```

Data is rolled up to **entity × country × week** (media) and
**entity × source × week** (opinion). The Python stack stays lean; heavier
backends (transformers/RoBERTa, spaCy) are optional and auto-detected.

## Setup

Requires **Python 3.11+** and **Node.js 18+**.

```bash
pip install -r requirements.txt          # backend + pipelines
cd frontend && npm install && cd ..      # frontend
```

## Run

```bash
# 1. Build the media database (tries live GDELT, else synthetic demo data)
python scripts/run_pipeline.py --source auto

# 2. Build the public-opinion layer (RoBERTa-scored; synthetic if no creds)
python scripts/run_opinion_pipeline.py --source auto

# 3. Start the API
uvicorn api.main:app --port 8000         # http://localhost:8000/docs

# 4. Start the frontend (separate terminal)
cd frontend && npm run dev               # http://localhost:3000
```

> **Offline-friendly.** GDELT rate-limits, and Reddit/Bluesky need credentials —
> when unavailable, both pipelines fall back to deterministic **synthetic**
> data, clearly flagged in the UI and never presented as real.

## Live data (optional)

Copy `.env.example` to `.env` and add credentials — the app reads them from
there (never commit `.env`):

- **Reddit**: create a "script" app at reddit.com/prefs/apps
- **Bluesky**: Settings → App Passwords

Without credentials everything still runs on synthetic data.

## Add a tracked entity

Edit [`config/watchlist.yaml`](config/watchlist.yaml) and re-run the pipelines:

```yaml
entities:
  - id: some_id
    name: Display Name
    type: figure           # figure | party | theme
    home_country: US        # GDELT country code, or null for themes
    query: '"Display Name"' # GDELT query fragment
    aliases: ["Nickname"]
```

## Tests

```bash
pytest -q
```

## Legacy Streamlit app

The original UI (`streamlit run src/dashboard/app.py`) still works and is a
dependency-light fallback, but it's **deprecated** in favour of the React
frontend, which adds the media-vs-public views.
