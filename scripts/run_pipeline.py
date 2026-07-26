"""End-to-end Phase 1 pipeline:  ingest -> clean -> store -> aggregate.

Run from the project root:
    python scripts/run_pipeline.py                 # source=auto (GDELT, else synthetic)
    python scripts/run_pipeline.py --source synthetic
    python scripts/run_pipeline.py --source gdelt --weeks 8

This is the loop referenced in Phase 1 step 7: change config/watchlist.yaml
-> re-run this -> the new entity is pulled, aggregated, and shows up in the
dashboard.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Windows consoles default to cp1252 and choke on unicode (arrows, warning
# glyphs). Emit UTF-8 so status output never crashes the pipeline.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass

# Make `src` importable when run as a script from the project root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import DEFAULT_CONFIG_PATH, DEFAULT_DB_PATH, load_watchlist  # noqa: E402
from src.ingestion.ingest import ingest_watchlist, default_window            # noqa: E402
from src.processing.clean import clean_articles                             # noqa: E402
from src.processing.aggregate import aggregate_weekly                       # noqa: E402
from src import storage                                                     # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Phase 1 sentiment pipeline.")
    parser.add_argument("--source", choices=["auto", "gdelt", "synthetic"],
                        default="auto",
                        help="Data source. 'auto' tries GDELT then falls back "
                             "to synthetic (fabricated) data.")
    parser.add_argument("--weeks", type=int, default=16,
                        help="How many weeks of history to pull (default 16).")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH))
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )

    print("=" * 66)
    print(" Global Political Sentiment Tracker — Phase 1 pipeline")
    print(" (measures MEDIA COVERAGE TONE, not public opinion)")
    print("=" * 66)

    wl = load_watchlist(args.config)
    print(f"Watchlist : {len(wl.countries)} countries, {len(wl.entities)} entities")

    window = default_window(weeks=args.weeks)
    print(f"Window    : {window[0]} -> {window[1]}  (source={args.source})")

    # --- ingest ---
    print("\n[1/4] Ingesting coverage…")
    result = ingest_watchlist(wl, source=args.source, window=window)
    print(f"      source used : {result.source_used}")
    print(f"      raw articles: {len(result.articles):,}")
    for note in result.notes:
        print(f"      note: {note}")
    if result.source_used == "synthetic":
        print("      ⚠  SYNTHETIC (fabricated) data — for demo/testing only, "
              "not real coverage.")

    # --- clean ---
    print("\n[2/4] Cleaning / normalizing…")
    clean_df = clean_articles(result.articles, wl)
    print(f"      clean articles: {len(clean_df):,} "
          f"(deduped from {len(result.articles):,})")

    # --- store ---
    print("\n[3/4] Storing to SQLite…")
    conn = storage.connect(args.db)
    storage.init_db(conn)
    storage.sync_entities(conn, wl)
    n_art = storage.upsert_articles(conn, clean_df)
    print(f"      articles written: {n_art:,}  ->  {args.db}")

    # --- aggregate ---
    print("\n[4/4] Aggregating to entity x country x week…")
    agg = aggregate_weekly(clean_df)
    n_agg = storage.upsert_aggregated_scores(conn, agg)
    print(f"      aggregated rows : {n_agg:,}")
    if not agg.empty:
        low = int(agg["low_confidence"].sum())
        print(f"      low-confidence  : {low:,} / {n_agg:,} weekly cells flagged "
              f"(thin coverage)")
    conn.close()

    print("\nDone. Launch the dashboard with:")
    print("    streamlit run src/dashboard/app.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
