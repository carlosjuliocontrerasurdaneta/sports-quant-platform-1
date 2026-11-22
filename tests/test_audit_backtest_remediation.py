"""Temporal and settlement regressions found in the November 2026 audit."""
from datetime import datetime, timezone
import math

import pandas as pd
import pytest

from sqp.backtesting.availability import load_starter_history, result_available_at
from sqp.backtesting.engine import walk_forward_backtest
from sqp.backtesting.roi_engine import load_closing_odds, realized_roi_backtest
from sqp.config import RiskConfig
from sqp.domain.models import Event
from sqp.sports.registry import get_adapter
from sqp.storage.results_store import ResultsStore


def _result(day, home_score, away_score, *, home="Boston Celtics", away="Miami Heat", **extra):
    return dict(date=day, home=home, away=away, home_score=home_score, away_score=away_score, **extra)


def test_roi_uses_only_results_available_at_the_quote(tmp_path):
    quote = "2026-01-22T08:00:00Z"
    start = "2026-01-23T19:00:00Z"
    before = [_result(f"2026-01-{day:02d}", 100 + day % 2, 101 - day % 2)
              for day in range(1, 21)]
    target = _result("2026-01-23", 104, 100)
    odds_dir = tmp_path / "data" / "odds"
    odds_dir.mkdir(parents=True)
    pd.DataFrame([
        dict(event_id="target", home=target["home"], away=target["away"],
             commence_time=start, captured_at=quote, market="h2h", bookmaker="book",
             outcome=side, price_decimal=2.05, point=None)
        for side in (target["home"], target["away"])
    ]).to_csv(odds_dir / "odds_nba_202601.csv", index=False)
    odds = load_closing_odds(tmp_path, "nba")
    risk = RiskConfig(
        market_shrink=0, min_edge=0., max_plausible_edge=1., uncertainty_penalty=0.,
        line_movement_penalty=0., line_velocity_penalty=0., low_book_penalty=0.,
    )

    def probability(*intervening):
        out = realized_roi_backtest(before + list(intervening) + [target],
                                    odds, "nba", "basketball", None, risk, 1000, warmup=0)
        assert out["n_bets"] == 1
        settled = out["settled"].iloc[0]
        assert pd.Timestamp(settled["captured_at"]) == pd.Timestamp(quote)
        assert pd.Timestamp(settled["decision_cutoff"]) == pd.Timestamp(quote)
        return settled["estimated_probability"]

    morning = _result("2026-01-22", 125, 100, start_time="2026-01-22T03:00:00Z")
    assert probability() == probability(morning)
    assert probability() == probability({**morning, "available_at": quote})
    assert probability() == probability({**morning, "available_at": "2026-01-22T08:01:00Z"})
    assert probability() < probability({**morning, "available_at": "2026-01-22T07:59:00Z"})
    frozen = realized_roi_backtest(before + [target], odds, "nba", "basketball",
                                   None, risk, 1000, warmup=0, bet_from_date="2026-01-23")
    assert frozen["n_events_capture_before_freeze"] == 1
    assert frozen["n_bets"] == 0


def test_result_store_preserves_known_availability(tmp_path):
    store = ResultsStore(tmp_path)
    final = "2026-01-12T22:00:00Z"
    assert store.upsert("nba", [_result("2026-01-12", 100, 90, available_at=final)]) == 1
    assert store.upsert("nba", [_result("2026-01-13", 91, 90)]) == 1
    assert [r["available_at"] for r in store.load("nba")] == [final, ""]


def test_known_start_just_before_midnight_is_not_a_completed_day_result():
    row = _result("2026-01-12", 100, 90, start_time="2026-01-12T23:59:00Z")
    assert result_available_at(row, "nba") == datetime(2026, 1, 13, 23, 59, tzinfo=timezone.utc)
    row["available_at"] = "2026-01-13T03:00:00Z"
    assert result_available_at(row, "nba") == datetime(2026, 1, 13, 3, tzinfo=timezone.utc)


def test_tennis_backtest_orients_independently_of_winner():
    rows = [
        _result("2026-01-01", 1, 0, home="Player Alpha", away="Player Bravo"),
        _result("2026-01-02", 1, 0, home="Player Bravo", away="Player Alpha"),
    ]
    out = walk_forward_backtest(rows, "atp", "tennis", warmup=0)
    assert out["binary_outcomes"] == [1., 0.]
    assert out["binary_probs"][0] == 0.5
    assert out["binary_probs"][1] > 0.5  # Alpha won the preceding match.


def test_neutral_venue_affects_prices_and_reaches_walk_forward():
    row = _result("2026-01-01", 28, 12, home="Alabama Crimson Tide",
                  away="Georgia Bulldogs", neutral=True)
    params = {"elo_home_adv": 150.}
    ad = get_adapter("ncaaf", "football", params)
    local = Event("game", "bt", "ncaaf", row["home"], row["away"], row["date"])
    assert ad.estimate(local, None, None).home_win_estimated_probability > 0.57
    out = walk_forward_backtest([row], "ncaaf", "football", params, warmup=0)
    assert out["binary_probs"] == [0.5]
    reverse = Event("reverse", "bt", "ncaaf", row["away"], row["home"], row["date"], neutral=True)
    assert ad.estimate(reverse, None, None).home_win_estimated_probability == 0.5


def test_quarter_lines_weight_half_liquidations_as_half_stakes():
    rows = [_result("2026-01-01", 1, 1), _result("2026-01-02", 3, 0)]
    out = walk_forward_backtest(rows, "epl", "soccer", warmup=0,
                                spread_lines=(-0.25,), total_lines=(2.25,))
    for market in out["markets"].values():
        assert market["weights"] == [0.5, 1.]
        assert market["outcomes"] == [0., 1.]
        assert market["n_resolved_units"] == 1.5
        p0, p1 = market["probs"]
        assert market["observed_rate"] == pytest.approx(2 / 3)
        assert market["brier"] == pytest.approx((.5 * p0**2 + (1 - p1)**2) / 1.5)
        assert market["log_loss"] == pytest.approx(-(.5 * math.log1p(-p0) + math.log(p1)) / 1.5)


def test_pitcher_capture_before_cutoff_and_withdrawal(tmp_path):
    directory = tmp_path / "data" / "historical"
    directory.mkdir(parents=True)
    start = "2026-01-03T19:00:00Z"
    pd.DataFrame([
        dict(captured_at_utc=f"2026-01-03T{hour}:00:00Z", commence_time=start,
             game_pk="123", team_side="home", pitcher_name=pitcher)
        for hour, pitcher in [("09", "Before"), ("10", ""), ("11", "After"), ("20", "Postgame")]
    ]).to_csv(directory / "pitcher_probables_mlb.csv", index=False)
    lookup = load_starter_history(tmp_path, "mlb")
    assert lookup is not None
    ev = Event("event", "bt", "mlb", "Home", "Away", start)
    row = {"game_id": "123"}
    assert lookup(row, ev, datetime(2026, 1, 3, 10, tzinfo=timezone.utc)) == {"home_pitcher": "Before"}
    assert lookup(row, ev, datetime(2026, 1, 3, 11, tzinfo=timezone.utc)) == {"home_pitcher": None}
    assert lookup(row, ev, datetime(2026, 1, 3, 21, tzinfo=timezone.utc)) == {"home_pitcher": "After"}


def test_goalie_capture_uses_unique_event_and_observed_time(tmp_path):
    directory = tmp_path / "data" / "historical"
    directory.mkdir(parents=True)
    start = "2026-01-03T19:00:00Z"
    pd.DataFrame([
        dict(captured_at_utc=f"2026-01-03T{hour}:00:00Z", commence_time=start,
             event_id=identity, team_side="home", team="Bruins", goalie_espn_id=goalie)
        for hour, identity, goalie in [("09", "123", "100"), ("10", "123", "200"),
                                       ("11", "456", "300")]
    ]).to_csv(directory / "goalie_probables_nhl.csv", index=False)
    lookup = load_starter_history(tmp_path, "nhl")
    assert lookup is not None
    ev = Event("event", "bt", "nhl", "Boston Bruins", "Toronto Maple Leafs", start)
    assert lookup({}, ev, datetime(2026, 1, 3, 10, tzinfo=timezone.utc)) == {"home_goalie": "100"}
    assert lookup({}, ev, datetime(2026, 1, 3, 11, tzinfo=timezone.utc)) == {"home_goalie": "200"}
    assert lookup({}, ev, datetime(2026, 1, 3, 12, tzinfo=timezone.utc)) == {}


def test_roi_can_reuse_timestamped_daily_pitcher_confirmations(tmp_path):
    directory = tmp_path / "data" / "historical"
    directory.mkdir(parents=True)
    pd.DataFrame([
        dict(confirmed_at_utc="2026-01-03T09:00:00Z", event_id="event", game_date="2026-01-03",
             home="Home", away="Away", home_pitcher="Confirmed", away_pitcher="Away Starter"),
        dict(confirmed_at_utc="2026-01-03T20:00:00Z", event_id="event", game_date="2026-01-03",
             home="Home", away="Away", home_pitcher="Postgame", away_pitcher="Away Starter"),
    ]).to_csv(directory / "pitcher_confirmation_log_mlb.csv", index=False)
    ev = Event("event", "bt", "mlb", "Home", "Away", "2026-01-03T19:00:00Z")
    lookup = load_starter_history(tmp_path, "mlb")
    assert lookup is not None
    assert lookup({}, ev, datetime(2026, 1, 3, 21, tzinfo=timezone.utc)) == {
        "home_pitcher": "Confirmed", "away_pitcher": "Away Starter",
    }


def test_calibration_uses_starter_identity_only_when_recorded_before_the_event():
    past = [_result(f"2026-01-0{day}", 10, 0, home_starter="Strong", away_starter="Weak")
            for day in range(1, 5)]
    game = _result("2026-01-05", 3, 1, start_time="2026-01-05T22:00:00Z",
                   home_starter="Strong", away_starter="Weak")

    def p(row, **kwargs):
        return walk_forward_backtest(past + [row], "mlb", "baseball", warmup=4,
                                     **kwargs)["binary_probs"][0]

    assert p(game) == p({**game, "home_starter": "Weak", "away_starter": "Strong"})
    assert p(game) == p({**game, "home_starter_available_at": "2026-01-05T22:00:00Z"})
    assert p({**game, "home_starter_available_at": "2026-01-05T21:00:00Z"}) > p(game)
    assert p(game, retrospective_starters=True) > p(game)
