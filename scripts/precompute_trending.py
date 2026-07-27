"""Precompute the trending snapshot and cache it for the API.

Ranking ~80 catalog topics from LIVE data (GDELT/BigQuery) means many queries,
so it shouldn't run per web request. This job computes it once and writes
data/trending_cache.json, which /api/trending then serves instantly.

Run periodically (cron / Task Scheduler), e.g. hourly:
    python scripts/precompute_trending.py --source auto --top-n 30

    # cron (hourly):
    0 * * * * cd /path/to/project && python scripts/precompute_trending.py --source auto
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.topics import trending, global_snapshot  # noqa: E402
from src.topics.cache import write_trending        # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Precompute + cache trending topics.")
    p.add_argument("--source", choices=["synthetic", "auto", "live", "gdelt", "bigquery"],
                   default="synthetic",
                   help="Data source for trending (auto/live/bigquery use real data).")
    p.add_argument("--top-n", type=int, default=40)
    args = p.parse_args(argv)

    print(f"Precomputing trending (source={args.source})…")
    t0 = time.time()
    snapshot = global_snapshot(source=args.source)
    rows = trending(top_n=args.top_n, source=args.source)
    write_trending({"snapshot": snapshot, "trending": rows, "source": args.source})
    print(f"Cached {len(rows)} trending topics in {time.time() - t0:.1f}s "
          f"-> data/trending_cache.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
