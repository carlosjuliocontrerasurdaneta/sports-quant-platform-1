"""Atomic TTL cache with a durable journal for unpersisted daily odds snapshots."""
from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqp.exceptions import LockNoAdquiridoError
from sqp.storage.atomic import atomic_write_json
from sqp.storage.lock import locked


@dataclass(frozen=True)
class CacheEntry:
    data: Any
    captured_at: datetime
    snapshot_id: str | None = None

    @property
    def age_s(self) -> float:
        # NTFS mtime can be ahead of the process clock.
        return max(0.0, time.time() - self.captured_at.timestamp())

    def payload(self) -> dict:
        return {
            "_sqp_cache_version": 1,
            "captured_at": self.captured_at.isoformat(),
            "snapshot_id": self.snapshot_id,
            "data": self.data,
        }


class FileCache:
    def __init__(self, cache_dir: Path):
        self.dir = cache_dir

    @staticmethod
    def key(path: str, params: dict) -> str:
        norm = "&".join(f"{k}={params[k]}" for k in sorted(params) if k != "apiKey")
        return hashlib.sha1(f"{path}?{norm}".encode("utf-8"), usedforsecurity=False).hexdigest()

    def _file(self, key: str) -> Path:
        return self.dir / f"{key}.json"

    def age_s(self, key: str) -> float | None:
        entry = self._read(self._file(key))
        return None if entry is None else entry.age_s

    def get(self, key: str, ttl: float):
        entry = self.get_entry(key, ttl)
        return None if entry is None else entry.data

    @staticmethod
    def _read(path: Path) -> CacheEntry | None:
        try:
            # Dato y mtime vienen del mismo descriptor incluso si otro
            # proceso reemplaza el archivo de caché al mismo tiempo.
            with path.open(encoding="utf-8") as fh:
                data = json.load(fh)
                mtime = datetime.fromtimestamp(os.fstat(fh.fileno()).st_mtime, timezone.utc)
            if isinstance(data, dict) and data.get("_sqp_cache_version") == 1:
                stamp = datetime.fromisoformat(data["captured_at"])
                snapshot_id = data.get("snapshot_id")
                if stamp.tzinfo is None:
                    return None
                if snapshot_id is not None and (
                    not isinstance(snapshot_id, str) or len(snapshot_id) != 32
                    or any(c not in "0123456789abcdef" for c in snapshot_id)
                ):
                    return None
                return CacheEntry(data["data"], stamp, snapshot_id)
            return CacheEntry(data, mtime)
        except (KeyError, TypeError, ValueError, OSError):
            return None

    def get_entry(self, key: str, ttl: float, *, recover_pending: bool = False) -> CacheEntry | None:
        latest = self._read(self._file(key))
        primary = latest
        if recover_pending:
            # El diario es legible aun si la caché principal nunca se publicó.
            for entry in self.pending_entries(key):
                if latest is None or entry.captured_at > latest.captured_at:
                    latest = entry
        if latest is None or latest.age_s >= ttl:
            return None
        if latest is not primary:
            self._publish_latest(key, latest)
        return latest

    def _publish_latest(self, key: str, entry: CacheEntry) -> bool:
        path = self._file(key)
        try:
            with locked(path):
                previous = self._read(path)
                if previous is None or entry.captured_at >= previous.captured_at:
                    atomic_write_json(entry.payload(), path, indent=None)
        except (TypeError, OSError, LockNoAdquiridoError):
            return False
        return True

    # Las marcas sin identificador siguen siendo legibles en instalaciones antiguas.
    def _pending_file(self, key: str) -> Path:
        return self.dir / f"{key}.pending"

    def mark_pending(self, key: str) -> None:
        try:
            self.dir.mkdir(parents=True, exist_ok=True)
            self._pending_file(key).touch()
        except OSError:
            pass

    def clear_pending(self, key: str) -> None:
        try:
            self._pending_file(key).unlink(missing_ok=True)
        except OSError:
            pass

    def is_pending(self, key: str) -> bool:
        return self._pending_file(key).exists()

    def _snapshot_file(self, key: str, snapshot_id: str) -> Path:
        return self.dir / f"{key}.{snapshot_id}.snapshot.json"

    def pending_entries(self, key: str) -> list[CacheEntry]:
        entries = []
        for path in self.dir.glob(f"{key}.*.snapshot.json"):
            entry = self._read(path)
            if (entry is not None and entry.snapshot_id is not None
                    and path == self._snapshot_file(key, entry.snapshot_id)):
                entries.append(entry)
        return sorted(entries, key=lambda entry: entry.captured_at)

    def snapshot_pending(self, key: str, snapshot_id: str) -> bool:
        return self._snapshot_file(key, snapshot_id).exists()

    def acknowledge_snapshot(self, key: str, snapshot_id: str) -> None:
        self._snapshot_file(key, snapshot_id).unlink(missing_ok=True)

    def put(self, key: str, data, *, captured_at: datetime | None = None,
            snapshot_id: str | None = None) -> None:
        try:
            self.dir.mkdir(parents=True, exist_ok=True)
            if captured_at is None:
                atomic_write_json(data, self._file(key), indent=None)
            else:
                entry = CacheEntry(data, captured_at, snapshot_id)
                if snapshot_id is not None:
                    # Cada adquisición se publica junto con su propia obligación
                    # de escritura y puede sobrevivir a refrescos concurrentes.
                    atomic_write_json(entry.payload(), self._snapshot_file(key, snapshot_id), indent=None)
                if not self._publish_latest(key, entry):
                    return
        except (TypeError, OSError):
            return
        self.clear_pending(key)
