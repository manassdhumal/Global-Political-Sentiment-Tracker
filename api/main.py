"""FastAPI application entrypoint.

Run (from project root):
    uvicorn api.main:app --reload --port 8000

Interactive docs at http://localhost:8000/docs
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Make `src` importable when uvicorn loads this module.
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import deps
from api.routers import (
    config as config_router,
    explore,
    intelligence,
    nlp,
    misc,
    opinion,
    topics,
    geography,
    simulator,
    network,
    polling,
    timeseries,
    markets,
    polarization,
    analyst,
    live,
    watchlists,
    multilingual,
)

app = FastAPI(
    title="Global Political Sentiment Tracker API",
    version="2.0.0",
    description="Media & social sentiment toward political figures, parties and "
                "issues — across countries and over time. Measures coverage/"
                "social tone, NOT public opinion.",
)

# CORS: local dev origins by default; add the deployed frontend origin(s) via
# GPST_CORS_ORIGINS (comma-separated). Use "*" to allow any origin.
_DEFAULT_ORIGINS = [
    "http://localhost:3000", "http://127.0.0.1:3000",
    "http://localhost:3001", "http://127.0.0.1:3001",
]
_env_origins = [o.strip() for o in os.getenv("GPST_CORS_ORIGINS", "").split(",") if o.strip()]
_allow_all = "*" in _env_origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if _allow_all else _DEFAULT_ORIGINS + _env_origins,
    allow_credentials=not _allow_all,   # credentials can't be combined with "*"
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(config_router.router)
app.include_router(explore.router)
app.include_router(intelligence.router)
app.include_router(nlp.router)
app.include_router(misc.router)
app.include_router(opinion.router)
app.include_router(topics.router)
app.include_router(geography.router)
app.include_router(simulator.router)
app.include_router(network.router)
app.include_router(polling.router)
app.include_router(timeseries.router)
app.include_router(markets.router)
app.include_router(polarization.router)
app.include_router(analyst.router)
app.include_router(live.router)
app.include_router(watchlists.router)
app.include_router(multilingual.router)


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {
        "status": "ok",
        "data_ready": deps.data_ready(),
        "synthetic": deps.synthetic_count() > 0,
    }


@app.get("/", tags=["meta"])
def root() -> dict:
    return {"name": "Global Political Sentiment Tracker API",
            "docs": "/docs", "health": "/health"}
