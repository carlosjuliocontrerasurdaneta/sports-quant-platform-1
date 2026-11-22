"""Information cutoffs for historical decisions."""
from __future__ import annotations

from collections import defaultdict
import csv
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Callable
from zoneinfo import ZoneInfo

from sqp.domain.models import Event
from sqp.sports.team_names import normalize_key

StarterHistory = Callable[[dict, Event, datetime], dict[str, str | None]]


def utc_instant(value: object) -> datetime | None:
    """Parse an explicit, timezone-aware instant."""
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.astimezone(timezone.utc) if parsed.tzinfo is not None else None


def result_day_start(value: object, league: str) -> datetime | None:
    """Midnight on the result provider's calendar (MLB Eastern, others UTC)."""
    try:
        day = date.fromisoformat(str(value)[:10])
    except ValueError:
        return None
    zone = ZoneInfo("America/New_York") if league == "mlb" else timezone.utc
    return datetime.combine(day, time.min, zone).astimezone(timezone.utc)


def result_available_at(result: dict, league: str) -> datetime | None:
    """Use confirmed availability or an explicitly conservative approximation.

    Date-only feeds retain the result-provider calendar boundary. A timestamped
    start without a final time also waits 24 hours from kickoff, so the date
    boundary alone cannot admit a match that had just begun.
    """
    day_start = result_day_start(result.get("date"), league)
    if day_start is None:
        return None
    start = utc_instant(result.get("start_time") or result.get("date"))
    raw = str(result.get("available_at")).strip()
    if raw.lower() not in ("", "nan", "nat", "none", "<na>"):
        explicit = utc_instant(raw)
        if explicit is not None and explicit >= day_start and (start is None or explicit > start):
            return explicit
        return None
    day = date.fromisoformat(str(result["date"])[:10])
    next_day = result_day_start((day + timedelta(days=1)).isoformat(), league)
    assert next_day is not None
    day_closed = next_day - timedelta(microseconds=1)
    return day_closed if start is None else max(day_closed, start + timedelta(days=1))


def row_starters_at(result: dict, cutoff: datetime | None, *,
                    retrospective: bool = False) -> dict[str, str | None]:
    """Contemporaneous starter fields require their own recorded availability."""
    starters: dict[str, str | None] = {}
    for side in ("home", "away"):
        for field, output in ((f"{side}_starter", f"{side}_pitcher"),
                              (f"{side}_goalie_announced", f"{side}_goalie")):
            seen = utc_instant(result.get(f"{field}_available_at"))
            value = str(result.get(field)).strip()
            if value.lower() in ("", "nan", "nat", "none", "<na>"):
                continue
            if retrospective or (seen is not None and cutoff is not None and seen < cutoff):
                starters[output] = value
    return starters


def load_starter_history(root: Path, league: str) -> StarterHistory | None:
    """Index prospectively captured MLB pitchers or NHL goalies for replay.

    MLB joins on gamePk or on the logged odds event ID for daily confirmations.
    NHL requires a unique provider game at the same kickoff and matching team.
    Empty announcements revoke the preceding identity.
    """
    filenames = {"mlb": "pitcher_probables_mlb.csv", "nhl": "goalie_probables_nhl.csv"}
    if league not in filenames:
        return None
    directory = root / "data" / "historical"
    path = directory / filenames[league]
    confirmation_path = directory / "pitcher_confirmation_log_mlb.csv"
    has_confirmation = league == "mlb" and confirmation_path.is_file()
    if not path.is_file() and not has_confirmation:
        return None
    mlb_rows: dict[tuple[str, str], list[tuple[datetime, str | None]]] = defaultdict(list)
    confirmed: dict[tuple[str, str], list[tuple[datetime, str, str, str | None]]] = defaultdict(list)
    nhl_rows: dict[tuple[datetime, str], list[tuple[datetime, str, str, str | None]]] = defaultdict(list)
    if path.is_file():
        with path.open(encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                seen = utc_instant(row.get("captured_at_utc"))
                start = utc_instant(row.get("commence_time"))
                side = row.get("team_side", "")
                if seen is None or start is None or seen >= start or side not in ("home", "away"):
                    continue
                if league == "mlb":
                    game_pk = row.get("game_pk")
                    if game_pk:
                        mlb_rows[(game_pk, side)].append((seen, row.get("pitcher_name") or None))
                else:
                    event_id = row.get("event_id")
                    team = normalize_key(row.get("team"))
                    if event_id and team:
                        nhl_rows[(start, side)].append(
                            (seen, team, event_id, row.get("goalie_espn_id") or None))
    if has_confirmation:
        with confirmation_path.open(encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                seen = utc_instant(row.get("confirmed_at_utc"))
                event_id, game_day = row.get("event_id"), row.get("game_date")
                if seen is not None and event_id and game_day:
                    for side in ("home", "away"):
                        confirmed[(event_id, side)].append(
                            (seen, game_day, normalize_key(row.get(side)),
                             row.get(f"{side}_pitcher") or None))

    def resolve(result: dict, event: Event, cutoff: datetime) -> dict[str, str | None]:
        out: dict[str, str | None] = {}
        start = utc_instant(event.start_time)
        for side, team in (("home", event.home), ("away", event.away)):
            if league == "mlb":
                key = (str(result.get("game_id") or ""), side)
                candidates = list(mlb_rows.get(key, []))
                if start is not None:
                    day = start.date().isoformat()
                    full = normalize_key(team)
                    candidates.extend((seen, player) for seen, game_day, recorded, player
                                      in confirmed.get((event.event_id, side), [])
                                      if game_day == day and recorded == full and seen < start)
                output = f"{side}_pitcher"
            elif start is not None:
                full = normalize_key(team)
                rows = [(seen, event_id, goalie) for seen, recorded, event_id, goalie
                        in nhl_rows.get((start, side), [])
                        if seen < cutoff and (full == recorded or full.endswith(" " + recorded))]
                if len({event_id for _, event_id, _ in rows}) != 1:
                    continue
                candidates = [(seen, goalie) for seen, _, goalie in rows]
                output = f"{side}_goalie"
            else:
                continue
            known = [(seen, value) for seen, value in candidates if seen < cutoff]
            if known:
                latest = max(seen for seen, _ in known)
                values = {value for seen, value in known if seen == latest}
                out[output] = next(iter(values)) if len(values) == 1 else None
        return out

    return resolve
