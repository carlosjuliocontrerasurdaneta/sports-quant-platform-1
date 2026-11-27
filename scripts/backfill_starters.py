#!/usr/bin/env python
"""Backfill the MLB starter map (gamePk -> probable starters) into
data/historical/starters_mlb.csv. Re-running refreshes announcements
(newest ingestion wins per game_id).

Example:
  python scripts/backfill_starters.py --days 365
"""
import argparse
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from sqp.config import ROOT
from sqp.logging_config import get_logger
from sqp.providers.mlb_statsapi import MLBStatsProvider
from sqp.storage.starters import StartersStore

log = get_logger("sqp.backfill")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=365)
    args = ap.parse_args()
    try:
        rows = MLBStatsProvider().fetch_starters(days_back=args.days)
    except requests.RequestException as exc:
        # Red caida / MLB Stats API fuera: una linea en el log y exit 1, no un
        # traceback de 40 lineas. El almacen existente queda intacto.
        log.error("[mlb] starter backfill skipped, MLB Stats API unreachable: "
                  "%s: %s", type(exc).__name__, exc)
        return 1
    both = sum(1 for r in rows if r["home_starter"] and r["away_starter"])
    store = StartersStore(ROOT)
    total = store.save("mlb", rows)
    log.info("[mlb] fetched %d starter rows (%d days back), %d with both starters "
             "(%.1f%%); store now has %d rows -> %s",
             len(rows), args.days, both, 100.0 * both / len(rows) if rows else 0.0,
             total, store.path("mlb"))
    if rows and both / len(rows) < 0.8:
        log.warning("[mlb] starter coverage below 80%%: pitcher features will be "
                    "neutral on uncovered games.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
