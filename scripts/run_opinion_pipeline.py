"""Public-opinion pipeline:  ingest posts -> score (model) -> store -> aggregate.

Run from the project root:
    python scripts/run_opinion_pipeline.py                    # auto source, RoBERTa
    python scripts/run_opinion_pipeline.py --source synthetic --backend vader
    python scripts/run_opinion_pipeline.py --source reddit    # needs .env creds

Populates opinion_posts + opinion_scores. Pair with run_pipeline.py (media)
to unlock the media-vs-public comparison.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import DEFAULT_DB_PATH, DEFAULT_CONFIG_PATH, load_watchlist  # noqa: E402
from src.ingestion.ingest import default_window                             # noqa: E402
from src.ingestion.opinion_ingest import ingest_opinion                     # noqa: E402
from src.processing.aggregate import aggregate_opinion_weekly              # noqa: E402
from src import storage                                                     # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Run the public-opinion pipeline.")
    p.add_argument("--source", choices=["auto", "reddit", "bluesky", "synthetic"],
                   default="auto")
    p.add_argument("--backend", choices=["transformers", "vader", "auto"],
                   default="transformers",
                   help="Sentiment model for scoring posts (default: RoBERTa).")
    p.add_argument("--weeks", type=int, default=16)
    p.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    p.add_argument("--db", default=str(DEFAULT_DB_PATH))
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args(argv)

    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING,
                        format="%(levelname)s %(name)s: %(message)s")

    print("=" * 66)
    print(" Global Political Sentiment Tracker — PUBLIC OPINION pipeline")
    print(" (social sentiment from real posts — NOT representative opinion)")
    print("=" * 66)

    wl = load_watchlist(args.config)
    window = default_window(weeks=args.weeks)
    print(f"Watchlist : {len(wl.entities)} entities")
    print(f"Window    : {window[0]} -> {window[1]}  (source={args.source}, "
          f"backend={args.backend})")

    print("\n[1/3] Ingesting + scoring posts (this runs the sentiment model)…")
    res = ingest_opinion(wl, source=args.source, window=window,
                         backend=args.backend)
    print(f"      source used   : {res.source_used}")
    print(f"      scoring model : {res.backend}")
    print(f"      posts scored  : {len(res.posts):,}")
    for note in res.notes[:6]:
        print(f"      note: {note}")
    if res.source_used == "synthetic":
        print("      ⚠  SYNTHETIC (fabricated) posts — demo only, not real opinion.")
    if res.posts.empty:
        print("No posts ingested. Nothing to store.")
        return 0

    print("\n[2/3] Storing posts to SQLite…")
    conn = storage.connect(args.db)
    storage.init_db(conn)
    storage.sync_entities(conn, wl)
    n_posts = storage.upsert_opinion_posts(conn, res.posts)
    print(f"      posts written : {n_posts:,}")

    print("\n[3/3] Aggregating to entity x source x week…")
    agg = aggregate_opinion_weekly(res.posts)
    n_agg = storage.upsert_opinion_scores(conn, agg)
    low = int(agg["low_confidence"].sum()) if not agg.empty else 0
    print(f"      opinion rows  : {n_agg:,}  ({low} low-confidence)")
    conn.close()

    print("\nDone. Media-vs-public comparison is now available in the API/frontend.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
