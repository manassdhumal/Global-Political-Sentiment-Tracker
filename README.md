# 🌍 Global Political Sentiment Tracker

Tracks the **tone of news coverage** toward political figures, parties, and
issues — across countries and over time — using [GDELT](https://www.gdeltproject.org/).

> **Measures media sentiment, not public opinion.** A score reflects how the
> *press* covers a subject, not what people believe. Thin/low-confidence
> coverage is flagged; translation, sarcasm, and outlet bias all affect tone.

## Features

- **World map** choropleth of coverage tone per country, plus cross-country and
  entity-vs-entity comparisons and issue drill-downs.
- **Time series** of tone and article volume, with known events marked and a
  volatility index of the most-swinging entities/countries.
- **Intelligence layer**: short-term forecasting, anomaly/early-warning
  detection, topic modeling on spikes, event impact scoring, and
  domestic-vs-foreign (cross-language) framing.
- **Analyze your own text**: overall score, per-entity aspect sentiment,
  explainability highlighting, and comparison against the live trend.
- **Political-mood homepage**, global search, exportable reports (Markdown/PDF),
  and a methodology page documenting limitations.
- Fully **config-driven** watchlist — no tracked names hardcoded.

## Setup

Requires Python 3.11+.

```bash
pip install -r requirements.txt
```

## Run

```bash
# 1. Build the database (tries live GDELT, falls back to synthetic demo data)
python scripts/run_pipeline.py --source auto

# 2. Launch the dashboard
streamlit run src/dashboard/app.py
```

> GDELT's free API rate-limits aggressively. When it's unavailable, `--source
> auto` falls back to a deterministic **synthetic dataset** (clearly flagged in
> the UI, never presented as real coverage) so the app runs fully offline.

## Add a tracked entity

Edit [`config/watchlist.yaml`](config/watchlist.yaml) and re-run the pipeline:

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

## Structure

`ingestion → processing → storage → analytics → nlp → reporting → dashboard`,
with data rolled up to **entity × country × week**. Kept lean; heavier backends
(transformers, spaCy, BERTopic, Prophet) are optional, auto-detected upgrades.
