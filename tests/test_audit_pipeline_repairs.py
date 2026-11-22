from datetime import datetime, timedelta, timezone

import pandas as pd
import pytest

from sqp.config import Settings
from sqp.domain.models import Event, EventOdds, MarketLine
from sqp.exceptions import DataValidationError
from sqp.pipeline import daily
from sqp.pipeline.probabilities import (
    _consensus_lines,
    _novig_probs,
    validate_book_contracts,
)
from sqp.pipeline.revalidation import NO_EXECUTION_PRICE, revalidate_candidates
from sqp.providers import odds_cache
from sqp.providers.odds_api import OddsAPIClient
from sqp.storage.odds_store import OddsStore


def _event(*, outcomes, neutral=False):
    return {
        "id": "e1",
        "home_team": "Local",
        "away_team": "Visitante",
        "commence_time": (datetime.now(timezone.utc) + timedelta(hours=3)).isoformat(),
        "neutral": neutral,
        "bookmakers": [{"key": "shop", "markets": [{"key": "h2h", "outcomes": outcomes}]}],
    }


def test_malformed_nodes_do_not_discard_other_books_and_events():
    event = _event(outcomes=[{"name": "Local", "price": 1.9}])
    mixed = {**event, "bookmakers": [
        None,
        {"key": "broken", "markets": {}},
        {"key": "partial", "markets": [None, {"key": "h2h", "outcomes": "bad"}]},
        *event["bookmakers"],
    ]}
    client = OddsAPIClient("mock")
    events = client._parse_events([mixed, {"id": "bad"}], "icehockey_nhl", "nhl")
    assert [item.event.event_id for item in events] == ["e1"]
    assert [line.price_decimal for line in events[0].lines] == [1.9]
    assert client.last_parse_skipped == 5
    assert client._parse_events([], "icehockey_nhl", "nhl") == []
    with pytest.raises(DataValidationError):
        client._parse_events({}, "icehockey_nhl", "nhl")
    with pytest.raises(DataValidationError):
        client._parse_events([{**event, "bookmakers": [None]}], "icehockey_nhl", "nhl")


@pytest.mark.parametrize("draw", [{"name": "Draw", "price": "missing"}, {"name": "Tie"}])
def test_unpriced_draw_still_excludes_regulation_book(draw):
    regular = _event(outcomes=[{"name": "Local", "price": 1.9},
                               {"name": "Visitante", "price": 2.0}])
    regulation = {"key": "reg", "markets": [{"key": "h2h", "outcomes": [
        {"name": "Local", "price": 2.5}, {"name": "Visitante", "price": 2.6}, draw,
    ]}]}
    regular["bookmakers"].append(regulation)
    [eo] = OddsAPIClient("mock")._parse_events([regular], "icehockey_nhl", "nhl")
    assert len(eo.lines) == 5
    assert _consensus_lines(validate_book_contracts(eo, False)) == {
        ("h2h", "Local", None): 1.9, ("h2h", "Visitante", None): 2.0,
    }


def test_three_way_and_totals_require_the_canonical_outcomes():
    assert _novig_probs({
        ("h2h", "Local", None): 2.2, ("h2h", "Visitante", None): 3.1,
        ("h2h", "Unexpected", None): 3.2,
    }, "h2h", three_way=True, outcomes=("Local", "Visitante")) == {}
    assert _novig_probs({
        ("totals", "Over", 2.25): 1.9, ("totals", "Under", 2.25): 1.9,
        ("totals", "Unexpected", 2.25): 2.0,
    }, "totals", 2.25) == {}


def test_contracts_are_validated_per_book_and_line_with_normalized_aliases():
    eo = EventOdds(Event("e", "soccer_epl", "epl", "Équipe A", "Equipo B", "2099-01-01T00:00:00Z"), [
        MarketLine("h2h", "good", "Equipe A", 2.0),
        MarketLine("h2h", "good", "Equipo B", 3.0),
        MarketLine("h2h", "good", "tie", 3.1),
        MarketLine("h2h", "incomplete", "Équipe A", 2.5),
        MarketLine("h2h", "incomplete", "Equipo B", 3.5),
        MarketLine("totals", "good", "over", 2.0, 2.25),
        MarketLine("totals", "good", "UNDER", 1.9, 2.25),
        MarketLine("totals", "incomplete", "Over", 2.7, 2.25),
        MarketLine("totals", "incomplete", "Under", 1.4, 2.0),
        MarketLine("spreads", "good", "Equipe A", 1.8, -0.25),
        MarketLine("spreads", "good", "Equipo B", 2.1, 0.25),
    ])
    cons = _consensus_lines(validate_book_contracts(eo, True))
    assert cons == {
        ("h2h", "Équipe A", None): 2.0, ("h2h", "Equipo B", None): 3.0,
        ("h2h", "Draw", None): 3.1, ("totals", "Over", 2.25): 2.0,
        ("totals", "Under", 2.25): 1.9, ("spreads", "Équipe A", -0.25): 1.8,
        ("spreads", "Equipo B", 0.25): 2.1,
    }


def test_repeated_quotes_do_not_give_one_book_extra_weight():
    event = Event("e", "basketball_nba", "nba", "Local", "Visitante", "2099-01-01T00:00:00Z")
    eo = EventOdds(event, [
        MarketLine("h2h", "good", "Local", 2.0),
        MarketLine("h2h", "good", "Local", 2.0),
        MarketLine("h2h", "good", "Visitante", 1.8),
        MarketLine("h2h", "bad", "Local", 2.1),
        MarketLine("h2h", "bad", "Local", 2.2),
        MarketLine("h2h", "bad", "Visitante", 1.7),
    ])
    eligible = validate_book_contracts(eo, False)
    assert [(line.bookmaker, line.outcome) for line in eligible.lines] == [
        ("good", "Local"), ("good", "Visitante"),
    ]


@pytest.mark.parametrize(("execution", "consensus", "expected", "stamp"), [
    (1.70, 2.00, "revoke", "2026-11-21T19:45:00.123456+00:00"),
    (2.04, 1.70, "revoke", "2026-11-21T19:45:00+00:00"),
    (2.04, 2.00, "keep", "2026-11-21T19:45:00+00:00"),
    (None, 2.00, NO_EXECUTION_PRICE, "2026-11-21T19:45:00+00:00"),
    # audit-2026-11-22 AUD-004: sin la casa de ejecucion, un consenso que ya
    # deja el edge bajo el minimo revoca; no puede salvar el pick.
    (None, 1.70, "revoke", "2026-11-21T19:45:00+00:00"),
])
def test_revalidation_distinguishes_the_execution_book(execution, consensus, expected, stamp, tmp_path):
    now = datetime(2026, 11, 21, 20, tzinfo=timezone.utc)
    start = "2026-11-21T21:00:00+00:00"
    pred = tmp_path / "predictions"
    pred.mkdir()
    path = pred / "candidates_nba.csv"
    pd.DataFrame([{"event_id": "e1", "market": "h2h", "selection": "Local",
                   "price_decimal": 2.0, "adjusted_edge": 0.08, "execution_book": "Pinnacle",
                   "stake": 5.0, "generated_at": "2026-11-21T17:00:00+00:00"}]).to_csv(path, index=False)
    pd.DataFrame([{"event_id": "e1", "start_time": start}]).to_csv(
        pred / "predictions_nba.csv", index=False)
    quotes = [
        MarketLine("h2h", "a", "Local", consensus), MarketLine("h2h", "b", "Local", consensus),
    ]
    if execution is not None:
        quotes.append(MarketLine("h2h", "pinnacle", "Local", execution))
    evt = Event("e1", "basketball_nba", "nba", "Local", "Visitante", start)
    store = OddsStore(tmp_path)
    store.append_snapshot("nba", [EventOdds(evt, quotes)], "2026-11-21T19:40:00+00:00")
    store.append_snapshot("nba", [EventOdds(evt, quotes)], stamp)
    result = revalidate_candidates(pred, tmp_path, min_edge=0.02, now=now)
    row = pd.read_csv(path).iloc[0]
    assert row["reval_action"] == expected
    assert row["reval_consensus_price"] == pytest.approx(consensus)
    if execution is None and expected == "revoke":
        assert result["revoked"] == 1 and result["skipped_no_price"] == 0
        assert row["reval_price"] == pytest.approx(consensus)
        assert pd.isna(row["reval_execution_price"])
    elif execution is None:
        assert result["skipped_no_price"] == 1 and result["kept"] == 0
        assert pd.isna(row["reval_price"])
    else:
        assert row["reval_execution_price"] == pytest.approx(execution)
        assert row["reval_price"] == pytest.approx(min(consensus, execution))
    assert row["stake"] == (0.0 if expected == "revoke" else 5.0)


class _Session:
    def __init__(self, event):
        self.event = event
        self.calls = 0

    def get(self, *args, **kwargs):
        self.calls += 1
        return self

    def raise_for_status(self):
        pass

    def json(self):
        return [self.event]


def test_snapshot_recovers_if_interrupted_before_main_cache_publish(tmp_path, monkeypatch):
    session = _Session(_event(outcomes=[{"name": "Local", "price": 1.9},
                                         {"name": "Visitante", "price": 2.1}], neutral=True))
    cache_dir = tmp_path / "cache"

    def make_client(*args, **kwargs):
        return OddsAPIClient("mock", session=session, cache_dir=cache_dir,
                             track_snapshots=True, force_refresh=False)

    first = make_client()
    write = odds_cache.atomic_write_json

    def interrupt_main(payload, path, **kwargs):
        if not path.name.endswith(".snapshot.json"):
            raise KeyboardInterrupt
        return write(payload, path, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(odds_cache, "atomic_write_json", interrupt_main)
        with pytest.raises(KeyboardInterrupt):
            first.fetch_odds("nba", "basketball_nba")
    captured_at = first.last_response_captured_at
    assert captured_at is not None and first.snapshot_pending()
    retry = make_client()
    monkeypatch.setattr(retry, "is_sport_active", lambda *args: True)
    monkeypatch.setattr(daily, "OddsAPIClient", lambda *args, **kwargs: retry)
    monkeypatch.setattr(daily, "_fetch_recent_scores", lambda *args: [])
    monkeypatch.setattr(daily, "ROOT", tmp_path)
    result = daily.run_league("nba", Settings(), mode="live")
    assert bool(result["neutral"].iloc[0])
    assert session.calls == 1 and retry.last_response_cached
    assert retry.last_response_captured_at == captured_at
    assert not retry.snapshot_pending()
    month = captured_at[:7].replace("-", "")
    stored = pd.read_csv(OddsStore(tmp_path).path("nba", month))
    assert stored["captured_at"].tolist() == [captured_at, captured_at]
    daily.run_league("nba", Settings(), mode="live")
    assert session.calls == 1
    assert len(pd.read_csv(OddsStore(tmp_path).path("nba", month))) == 2


def test_pending_capture_survives_concurrent_primary_replacement(tmp_path, monkeypatch):
    session = _Session(_event(outcomes=[{"name": "Local", "price": 1.9},
                                         {"name": "Visitante", "price": 2.1}]))
    cache_dir = tmp_path / "cache"
    earlier = OddsAPIClient("mock", session=session, cache_dir=cache_dir,
                             track_snapshots=True, force_refresh=False)
    later = OddsAPIClient("mock", session=session, cache_dir=cache_dir,
                           track_snapshots=True, force_refresh=True)
    earlier.fetch_odds("nba", "basketball_nba")
    later.fetch_odds("nba", "basketball_nba")
    assert earlier.snapshot_pending() and later.snapshot_pending()
    assert earlier.last_response_captured_at != later.last_response_captured_at

    retry = OddsAPIClient("mock", session=session, cache_dir=cache_dir,
                           track_snapshots=True, force_refresh=False)
    monkeypatch.setattr(retry, "is_sport_active", lambda *args: True)
    monkeypatch.setattr(daily, "OddsAPIClient", lambda *args, **kwargs: retry)
    monkeypatch.setattr(daily, "_fetch_recent_scores", lambda *args: [])
    monkeypatch.setattr(daily, "ROOT", tmp_path)
    daily.run_league("nba", Settings(), mode="live")
    assert not earlier.snapshot_pending() and not later.snapshot_pending()
    assert session.calls == 2 and retry.last_response_cached
    paths = list((tmp_path / "data" / "odds").glob("odds_nba_*.csv"))
    stamps = pd.concat([pd.read_csv(path) for path in paths])["captured_at"].value_counts()
    assert stamps.to_dict() == {earlier.last_response_captured_at: 2, later.last_response_captured_at: 2}


def test_old_snapshot_replay_is_idempotent_outside_the_old_tail(tmp_path):
    evt = Event("e", "basketball_nba", "nba", "Local", "Visitante", "2026-11-21T20:00:00Z")
    original = [EventOdds(evt, [MarketLine("h2h", "old", "Local", 1.9)])]
    subsequent = [EventOdds(evt, [
        MarketLine("h2h", f"subsequent-{i}-{i:020}", "Local", 2.01) for i in range(3100)
    ])]
    store = OddsStore(tmp_path)
    stamp = "2026-11-20T13:00:00+00:00"
    assert store.append_snapshot("nba", original, stamp) == 1
    assert store.append_snapshot("nba", subsequent, "2026-11-21T13:00:00+00:00") == 3100
    assert store.path("nba", "202611").stat().st_size > 262144
    assert store.append_snapshot("nba", original, stamp) == 0
