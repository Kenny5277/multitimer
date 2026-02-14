"""Persistence helpers for MultiTimer timers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List

from timers import TimerEntry


DEFAULT_STORAGE_FILE = Path("timers.json")


def load_timers(path: Path = DEFAULT_STORAGE_FILE) -> List[TimerEntry]:
    """Load timers from disk, returning an empty list if the file is missing."""
    if not path.exists():
        return []

    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        return []

    timers: List[TimerEntry] = []
    for item in raw:
        if isinstance(item, dict):
            timers.append(TimerEntry.from_dict(item))
    return timers


def save_timers(timers: Iterable[TimerEntry], path: Path = DEFAULT_STORAGE_FILE) -> None:
    """Save all timers to disk in JSON format."""
    payload = [timer.to_dict() for timer in timers]
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
