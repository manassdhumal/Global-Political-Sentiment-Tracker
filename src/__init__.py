"""Global Political Sentiment Tracker.

A Python system that tracks the TONE OF NEWS COVERAGE toward political
figures, parties and issues over time and across countries, using GDELT
as the primary signal.

Module map (kept cleanly separated so later phases slot in without rewrites):
    src.config      -- load & validate the watchlist config
    src.ingestion   -- pull coverage from GDELT (+ synthetic fallback)
    src.processing  -- clean/normalize and aggregate
    src.storage     -- SQLite schema + persistence
    src.dashboard   -- Streamlit app

NOTE: every score here is MEDIA SENTIMENT (coverage tone), not public opinion.
"""

__version__ = "0.1.0"
