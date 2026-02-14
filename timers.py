"""Timer scheduling logic for MultiTimer.

This module intentionally has no Tkinter dependencies so it can be tested
independently from the UI layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Iterable, List, Optional
from uuid import uuid4


@dataclass
class TimerEntry:
    """Represents one repeating reminder timer."""

    id: str
    name: str
    interval_minutes: int
    running: bool = False
    next_trigger_iso: Optional[str] = None

    @property
    def interval_seconds(self) -> int:
        """Return timer interval in seconds."""
        return self.interval_minutes * 60

    def next_trigger(self) -> Optional[datetime]:
        """Parse and return the next trigger datetime if available."""
        if not self.next_trigger_iso:
            return None
        return datetime.fromisoformat(self.next_trigger_iso)

    def set_next_trigger(self, dt: Optional[datetime]) -> None:
        """Store next trigger as ISO text for persistence."""
        self.next_trigger_iso = dt.isoformat() if dt else None

    def to_dict(self) -> dict:
        """Serialize timer into a JSON-friendly dict."""
        return {
            "id": self.id,
            "name": self.name,
            "interval_minutes": self.interval_minutes,
            "running": self.running,
            "next_trigger_iso": self.next_trigger_iso,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TimerEntry":
        """Build a timer entry from persisted data."""
        return cls(
            id=str(data.get("id") or uuid4()),
            name=str(data.get("name", "Timer")),
            interval_minutes=max(1, int(data.get("interval_minutes", 1))),
            running=bool(data.get("running", False)),
            next_trigger_iso=data.get("next_trigger_iso"),
        )


class TimerManager:
    """Centralized scheduler and state manager for repeating timers."""

    def __init__(self, timers: Optional[Iterable[TimerEntry]] = None) -> None:
        self._timers: Dict[str, TimerEntry] = {}
        if timers:
            for timer in timers:
                self._timers[timer.id] = timer

    def all(self) -> List[TimerEntry]:
        """Return all timers in insertion order."""
        return list(self._timers.values())

    def get(self, timer_id: str) -> Optional[TimerEntry]:
        """Return timer by ID if it exists."""
        return self._timers.get(timer_id)

    def add_timer(self, name: str, interval_minutes: int) -> TimerEntry:
        """Add a new timer with the provided name and interval."""
        self._validate_interval(interval_minutes)
        timer = TimerEntry(id=str(uuid4()), name=name.strip() or "Timer", interval_minutes=interval_minutes)
        self._timers[timer.id] = timer
        return timer

    def edit_timer(self, timer_id: str, name: str, interval_minutes: int) -> TimerEntry:
        """Edit an existing timer and reschedule if needed."""
        self._validate_interval(interval_minutes)
        timer = self._require_timer(timer_id)
        timer.name = name.strip() or "Timer"
        timer.interval_minutes = interval_minutes
        if timer.running:
            # Reschedule based on the new interval from now.
            timer.set_next_trigger(datetime.now() + timedelta(seconds=timer.interval_seconds))
        return timer

    def delete_timer(self, timer_id: str) -> None:
        """Delete timer by ID."""
        self._require_timer(timer_id)
        del self._timers[timer_id]

    def start_timer(self, timer_id: str, now: Optional[datetime] = None) -> TimerEntry:
        """Start one timer and schedule its next trigger."""
        current = now or datetime.now()
        timer = self._require_timer(timer_id)
        timer.running = True
        timer.set_next_trigger(current + timedelta(seconds=timer.interval_seconds))
        return timer

    def stop_timer(self, timer_id: str) -> TimerEntry:
        """Stop one timer and clear next trigger."""
        timer = self._require_timer(timer_id)
        timer.running = False
        timer.set_next_trigger(None)
        return timer

    def start_all(self, now: Optional[datetime] = None) -> None:
        """Start every configured timer."""
        for timer in self._timers.values():
            self.start_timer(timer.id, now=now)

    def stop_all(self) -> None:
        """Stop every configured timer."""
        for timer in self._timers.values():
            self.stop_timer(timer.id)

    def tick(self, now: Optional[datetime] = None) -> List[TimerEntry]:
        """Advance scheduler and return any timers that triggered now.

        Triggered timers are immediately rescheduled according to the repeating
        interval requirement.
        """
        current = now or datetime.now()
        triggered: List[TimerEntry] = []
        for timer in self._timers.values():
            if not timer.running:
                continue
            next_time = timer.next_trigger()
            if next_time is None:
                timer.set_next_trigger(current + timedelta(seconds=timer.interval_seconds))
                continue
            if current >= next_time:
                triggered.append(timer)
                timer.set_next_trigger(current + timedelta(seconds=timer.interval_seconds))
        return triggered

    def next_in_seconds(self, timer_id: str, now: Optional[datetime] = None) -> Optional[int]:
        """Return whole seconds until next trigger for one timer."""
        timer = self._require_timer(timer_id)
        if not timer.running:
            return None
        next_time = timer.next_trigger()
        if not next_time:
            return None
        current = now or datetime.now()
        delta = int((next_time - current).total_seconds())
        return max(0, delta)

    @staticmethod
    def _validate_interval(interval_minutes: int) -> None:
        if int(interval_minutes) < 1:
            raise ValueError("Interval must be at least 1 minute.")

    def _require_timer(self, timer_id: str) -> TimerEntry:
        timer = self.get(timer_id)
        if not timer:
            raise KeyError(f"Unknown timer id: {timer_id}")
        return timer
