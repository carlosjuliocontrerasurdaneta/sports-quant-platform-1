"""Walk-forward backtest: fit ratings strictly on past, estimate next game,
log estimated probability vs outcome. Temporal by construction (no random
splits). Realized ROI requires real historical odds; without them only
calibration metrics are reported.

Bias warnings that apply to any results: lookahead, leakage, survivorship,
selection, multiple testing, regime change.
"""
from __future__ import annotations
import math
import pandas as pd
from sqp.backtesting.availability import result_day_start, row_starters_at, utc_instant
from sqp.sports.registry import get_adapter
from sqp.calibration.metrics import brier_score, log_loss, expected_calibration_error, reliability_table
from sqp.domain.models import Event
from sqp.markets.settlement_math import is_quarter_line
from sqp.settlement.settle import grade_asian_line


def _market_summary(probs: list[float], outcomes: list[float], weights: list[float]) -> dict:
    """Metricas de un mercado binario, con el SESGO DIRECCIONAL al frente.

    `bias` = probabilidad media estimada - tasa observada. Es la metrica que el
    arnes existia para poder calcular: el Brier mezcla direccion y afilamiento,
    asi que un modelo que sobreestima sistematicamente puede tener buen Brier.
    El bug del `home_scoring_bonus` (2026-08-18) era exactamente eso.
    """
    n = len(probs)
    resolved = sum(weights)
    mean_p = sum(p * w for p, w in zip(probs, weights)) / resolved
    observed = sum(y * w for y, w in zip(outcomes, weights)) / resolved
    sample_weight = weights if resolved != n else None
    return {"n": n,
            "n_resolved_units": resolved,
            "brier": brier_score(probs, outcomes, sample_weight=sample_weight),
            "log_loss": log_loss(probs, outcomes, sample_weight=sample_weight),
            "ece": expected_calibration_error(probs, outcomes, sample_weight=sample_weight),
            "mean_probability": mean_p,
            "observed_rate": observed,
            "bias": mean_p - observed,
            # Series por partido en orden temporal: es lo que necesita
            # `rolling_origin_improvement` para validar una seleccion fuera de
            # muestra. Sin ellas el tuner solo puede comparar agregados.
            "probs": list(probs),
            "outcomes": list(outcomes),
            "weights": list(weights)}


def walk_forward_backtest(results: list[dict], league: str, family: str,
                          league_params: dict | None = None, warmup: int = 60,
                          spread_lines: tuple[float, ...] = (),
                          total_lines: tuple[float, ...] = (), *,
                          retrospective_starters: bool = False,
                          neutral_in_estimate: bool = True) -> dict:
    """Backtest temporal por bloques diarios. Sin `spread_lines`/`total_lines`
    solo se evalua moneyline; la interfaz de los consumidores se conserva.

    Con lineas, evalua ademas esos mercados contra lineas FIJAS de referencia:
    el desenlace sale del marcador, asi que no hace falta historico de cuotas.
    Los empujes se excluyen y las medias liquidaciones pesan media unidad.
    Los empates se excluyen de las métricas binarias del moneyline.

    Los titulares de la fila solo entran si hay evidencia de que ya se conocían
    al comienzo del partido (o al inicio del día si falta la hora).
    `retrospective_starters=True` reproduce experimentos de cota superior
    congelados, usando la identidad observada en la fila del resultado.

    `neutral_in_estimate=False` construye la estimacion sin la marca de sede
    neutral de la fila (como el motor anterior a 9de724f); las actualizaciones
    Elo siguen usandola. Solo para instrumentos pre-registrados cuya base se
    congelo sin ella (portero NHL, audit-2026-11-22 AUD-003); el valor por
    defecto es el comportamiento de produccion.
    """
    adapter = get_adapter(league, family, league_params)
    probs, outcomes = [], []
    market_probs: dict[str, list[float]] = {}
    market_outcomes: dict[str, list[float]] = {}
    market_weights: dict[str, list[float]] = {}

    def _record(market: str, line: float, p: float | None, margin: int,
                total: int, selection: str) -> None:
        if p is None:
            return
        diff = margin + line if market == "spreads" else total - line
        if is_quarter_line(line):
            result = grade_asian_line(market, selection, True, margin, total, line)
        elif diff == 0:
            result = "push"
        else:
            result = "win" if diff > 0 else "loss"
        if result in ("push", "void"):
            return
        key = f"{market}@{line}"
        market_probs.setdefault(key, []).append(p)
        market_outcomes.setdefault(key, []).append(float(result in ("win", "half_win")))
        market_weights.setdefault(key, []).append(0.5 if result.startswith("half_") else 1.0)
    dates: list[str] = []
    draw_probs, draw_outcomes = [], []
    threeway_ll_terms: list[float] = []
    # Dates do not establish when a same-day final score became available.
    # Estimate the whole day against the state at the preceding day's close.
    pending: list[dict] = []
    for i, r in enumerate(sorted(results, key=lambda row: str(row.get("date", "")))):
        if pending and str(r.get("date", ""))[:10] != str(pending[0].get("date", ""))[:10]:
            for completed in pending:
                adapter.observe(completed)
            pending.clear()
        if i >= warmup:
            home, away = r["home"], r["away"]
            hs, ars = r["home_score"], r["away_score"]
            if family == "tennis" and (adapter.normalize(home), home) > (adapter.normalize(away), away):
                # The results provider may label the actual winner as “home”.
                # Use the same pregame ordering regardless of who won.
                home, away, hs, ars = away, home, ars, hs
            cutoff = (utc_instant(r.get("start_time") or r.get("date"))
                      or result_day_start(r.get("date"), league))
            starters = row_starters_at(r, cutoff, retrospective=retrospective_starters)
            ev = Event(event_id=str(i), sport_key="bt", league=league,
                       home=home, away=away, start_time=str(r.get("date")),
                       data_label=r.get("data_label", "real"),
                       home_pitcher=starters.get("home_pitcher"),
                       away_pitcher=starters.get("away_pitcher"),
                       home_goalie=starters.get("home_goalie"),
                       away_goalie=starters.get("away_goalie"),
                       neutral=(family == "tennis"
                                or (neutral_in_estimate and r.get("neutral") is True)))
            est = adapter.estimate(ev, None, None)
            ph = est.home_win_estimated_probability
            if est.draw_estimated_probability is not None:
                # Three-way: binary metrics exclude draws, so the evaluated
                # probability must condition on no-draw or calibration is
                # mechanically overstated against draw-excluded frequencies.
                denom = ph + est.away_win_estimated_probability
                probs.append(ph / denom if denom > 0 else 0.5)
                draw_probs.append(est.draw_estimated_probability)
                draw_outcomes.append(1.0 if hs == ars else 0.0)
                if hs > ars:
                    p_outcome = ph
                elif hs == ars:
                    p_outcome = est.draw_estimated_probability
                else:
                    p_outcome = est.away_win_estimated_probability
                threeway_ll_terms.append(-math.log(max(1e-12, p_outcome)))
            else:
                probs.append(ph)
            outcomes.append(1.0 if hs > ars else (0.5 if hs == ars else 0.0))
            dates.append(str(r.get("date")))
            margin, total = hs - ars, hs + ars
            for s in spread_lines:
                _record("spreads", s,
                        adapter.estimate(ev, s, None).home_cover_estimated_probability,
                        margin, total, home)
            for t in total_lines:
                _record("totals", t,
                        adapter.estimate(ev, None, t).over_estimated_probability,
                        margin, total, "Over")
        pending.append(r)
    mask = [o in (0.0, 1.0) for o in outcomes]  # binary metrics exclude draws
    p = [x for x, m in zip(probs, mask) if m]
    y = [x for x, m in zip(outcomes, mask) if m]
    d = [x for x, m in zip(dates, mask) if m]
    return {
        "league": league, "n_games_evaluated": len(p),
        "brier_score": brier_score(p, y) if p else float("nan"),
        "log_loss": log_loss(p, y) if p else float("nan"),
        "ece": expected_calibration_error(p, y) if p else float("nan"),
        "reliability_table": reliability_table(p, y) if p else pd.DataFrame(),
        "observed_draw_rate": (sum(draw_outcomes) / len(draw_outcomes)) if draw_outcomes else None,
        "n_draws_observed": int(sum(draw_outcomes)),
        "n_threeway_evaluated": len(draw_outcomes),
        "mean_estimated_draw_probability": (sum(draw_probs) / len(draw_probs)) if draw_probs else None,
        "log_loss_threeway": (sum(threeway_ll_terms) / len(threeway_ll_terms)) if threeway_ll_terms else None,
        # Per-game series in temporal order, for rolling-origin holdout selection
        # in tuning (compute losses over arbitrary time windows without re-running).
        "binary_probs": p,
        "binary_outcomes": y,
        "binary_dates": d,
        "retrospective_starters": retrospective_starters,
        "threeway_ll_series": list(threeway_ll_terms),
        # Spreads/totals contra lineas fijas. Vacio salvo que se pidan lineas.
        "markets": {k: _market_summary(v, market_outcomes[k], market_weights[k])
                    for k, v in market_probs.items() if v},
        "note": ("Calibration-only backtest. Three-way leagues are scored on "
                 "P(home | no draw) vs draw-excluded outcomes; draw calibration "
                 "is reported separately. Realized ROI requires real historical "
                 "odds; never infer profitability from calibration alone."),
    }
