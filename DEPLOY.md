# Deploying

Two pieces: the **API** (FastAPI, containerized) and the **frontend** (Next.js).
The app runs on synthetic data with zero config; add credentials later for live
data. A fresh server IP also often clears GDELT's rate limit, so live GDELT may
"just work" once deployed.

```
frontend (Vercel)  ──HTTPS──▶  API (Render / Railway / Fly)  ──▶ GDELT / Reddit / Bluesky
```

## 1. Deploy the API (Render)

The repo includes a [`Dockerfile`](Dockerfile) and [`render.yaml`](render.yaml).

1. Push the repo to GitHub (already done).
2. On [Render](https://render.com): **New → Blueprint**, select this repo — it
   reads `render.yaml` and creates a free Docker web service (`gpst-api`).
   *(Or: New → Web Service → Docker, default settings.)*
3. Set env var **`GPST_CORS_ORIGINS`** — temporarily `*` (you'll tighten it once
   the frontend URL exists).
4. Deploy. Note the URL, e.g. `https://gpst-api.onrender.com`, and check
   `https://gpst-api.onrender.com/health` and `/docs`.

The image is lean (~no torch); RoBERTa sentiment falls back to VADER. To enable
the transformer model, add `torch`+`transformers` and use a larger instance.

## 2. Deploy the frontend (Vercel)

1. On [Vercel](https://vercel.com): **Add New → Project**, import this repo.
2. Set **Root Directory = `frontend`** (important — the Next app lives there).
3. Add env var **`NEXT_PUBLIC_API_BASE`** = your API URL from step 1
   (e.g. `https://gpst-api.onrender.com`). *Set it before the first build —
   `NEXT_PUBLIC_*` is inlined at build time.*
4. Deploy. You'll get e.g. `https://gpst.vercel.app`.

## 3. Lock down CORS

Back on Render, set **`GPST_CORS_ORIGINS`** to your Vercel URL
(`https://gpst.vercel.app`) and redeploy. Done.

## Environment variables

| Where | Var | Purpose |
|---|---|---|
| API | `GPST_CORS_ORIGINS` | Comma-separated allowed frontend origins (`*` allows all) |
| API | `GPST_TOPIC_SOURCE` | `synthetic` (default) or `auto` to prefer live data |
| API | `GPST_BQ_PROJECT` | GCP project for real GDELT history via BigQuery (+ auth) |
| API | `GPST_REDIS_URL` | Redis URL for a shared trending cache across web + cron |
| API | `GPST_NARRATIVE` / `ANTHROPIC_API_KEY` | `anthropic` for LLM-written topic explanations (default: offline rule-based) |
| API | `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET` | live Reddit opinion |
| API | `BLUESKY_HANDLE` / `BLUESKY_APP_PASSWORD` | live Bluesky opinion |
| Frontend | `NEXT_PUBLIC_API_BASE` | URL of the deployed API |

## Notes

- **Free tiers sleep.** Render's free web service cold-starts after idle; the
  first request may take ~30s.
- **Trending precompute cache.** `scripts/precompute_trending.py` writes a
  cache the API serves. On hosts where cron and web don't share a filesystem
  (Render free tier), set **`GPST_REDIS_URL`** on both so they share the cache
  via Redis (e.g. Render's free Key Value / Upstash). Without it, the API just
  computes trending on the fly.
- **Other hosts.** The same `Dockerfile` works on Railway, Fly.io, Google Cloud
  Run, etc. — just set the env vars and expose `$PORT`.
