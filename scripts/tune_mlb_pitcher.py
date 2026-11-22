#!/usr/bin/env python
"""Walk-forward tuning of the MLB starter-feature parameters (and tilt_scale).

Stage 1: grid over (pitcher_prior_starts, pitcher_bound), bound=0.0 = feature
off (control). Stage 2: tilt_scale grid at the stage-1 winner. Scored by walk-
forward log loss. Uses the starters who actually played to estimate an
upper bound. Prospective validation is required before changing live ratings.

Example:
  python scripts/tune_mlb_pitcher.py
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from sqp.backtesting.engine import walk_forward_backtest
from sqp.config import ROOT
from sqp.pipeline.daily import _league_meta
from sqp.storage.results_store import ResultsStore
from sqp.storage.starters import StartersStore

PRIORS = (5.0, 10.0, 20.0, 40.0)
BOUNDS = (0.0, 0.10, 0.20, 0.35)
TILTS = (0.4, 0.6, 0.8)


def _run(results: list[dict], base: dict, **over) -> dict:
    params = {**base, **over}
    res = walk_forward_backtest(results, "mlb", "baseball", params, retrospective_starters=True)
    return {**over, "log_loss": res["log_loss"], "brier_score": res["brier_score"],
            "ece": res["ece"], "n": res["n_games_evaluated"]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help=argparse.SUPPRESS)
    args = ap.parse_args()
    if args.write:
        ap.error("La búsqueda usa abridores observados retrospectivamente y solo estima "
                 "una cota superior. Se requiere validación prospectiva para cambiar ratings.yaml.")

    results = ResultsStore(ROOT).load("mlb")
    attached = StartersStore(ROOT).attach("mlb", results)
    print(f"[mlb] starter map attached to {attached}/{len(results)} results")
    base = dict(_league_meta("mlb").get("league_params") or {})

    rows = [_run(results, base, pitcher_prior_starts=p, pitcher_bound=b)
            for p in PRIORS for b in BOUNDS]
    t1 = pd.DataFrame(rows)
    print("\n=== Stage 1: prior x bound (bound 0 = pitcher feature OFF) ===")
    print(t1.round(4).to_string(index=False))
    best1 = t1.loc[t1["log_loss"].idxmin()]

    rows2 = [_run(results, base, pitcher_prior_starts=float(best1["pitcher_prior_starts"]),
                  pitcher_bound=float(best1["pitcher_bound"]), tilt_scale=t)
             for t in TILTS]
    t2 = pd.DataFrame(rows2)
    print("\n=== Stage 2: tilt_scale at stage-1 winner ===")
    print(t2.round(4).to_string(index=False))
    best2 = t2.loc[t2["log_loss"].idxmin()]

    tuned = {"pitcher_prior_starts": float(best1["pitcher_prior_starts"]),
             "pitcher_bound": float(best1["pitcher_bound"]),
             "tilt_scale": float(best2["tilt_scale"])}
    print(f"\nbest: {tuned} (log_loss {best2['log_loss']:.4f}) | "
          "Retrospective starter upper bound. Validate with pregame captures before using it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
