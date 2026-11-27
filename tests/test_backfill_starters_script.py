"""scripts/backfill_starters.py: a network outage is one log line and exit 1,
not an uncaught traceback (logs/backfill_diario.log, 2026-11-25)."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import requests

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "backfill_starters.py"


def _load():
    spec = importlib.util.spec_from_file_location("backfill_starters_script", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_network_error_returns_1_without_touching_store(monkeypatch):
    mod = _load()

    def boom(self, days_back=365):  # noqa: ARG001
        raise requests.ConnectionError("dns down")

    saved = []
    monkeypatch.setattr(mod.MLBStatsProvider, "fetch_starters", boom)
    monkeypatch.setattr(mod.StartersStore, "save",
                        lambda self, *a, **k: saved.append(a) or 0)
    monkeypatch.setattr(sys, "argv", ["backfill_starters.py", "--days", "3"])
    assert mod.main() == 1
    assert saved == []
