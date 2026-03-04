"""
timer_sql.py — Streaming timer for MIR pipelines using SQLiteInterface.

Features:
- Context manager, decorator, manual start/stop
- Optional in-memory accumulation for debugging
- Loop iteration tracking
- Streams events directly to SQLite table
- Metadata stored as JSON
"""
# TODO: Add run label for a timer instance.

# =========================================================================== #
# Built-in Imports.
import time
import json
import inspect
from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import wraps
from pathlib import Path

# Local Imports.
from src.python.sql import SQLiteInterface, sqlite_adapt

__all__ = ["Timer"]

# =========================================================================== #
@dataclass
class TimingEvent:
    name: str
    category: str = "general"
    start: float = 0.0
    end: float = 0.0
    duration: float = 0.0
    meta: dict = field(default_factory=dict)
    call_site: str | None = None
    iteration: int | None = None

    def as_record(self) -> dict:
        """Convert to dict for SQL insertion."""
        return {
            "name": self.name,
            "category": self.category,
            "start": self.start,
            "end": self.end,
            "duration": self.duration,
            "call_site": self.call_site,
            "iteration": self.iteration,
            "meta": json.dumps(self.meta, sort_keys=True),
        }

# =========================================================================== #
class SQLBackend:
    """
    Timer backend that writes events to an existing SQLiteInterface object.

    Requires the timing table to already exist (defined in schema.sql).
    """

    def __init__(self, sql: SQLiteInterface, table: str = "timing"):
        self.sql = sql
        self.table = table

        # Optional: Fail fast if schema not applied
        if not self.sql.table_exists(self.table):
            raise RuntimeError(
                f"Timing table '{self.table}' does not exist. "
                "Apply schema before using SQLBackend."
            )

    def write(self, event: TimingEvent):
        record = sqlite_adapt(event.as_record())
        self.sql.write(self.table, record)

# =========================================================================== #
class Timer:
    """
    Lightweight, streaming timer with SQL backend support.
    """

    def __init__(
        self,
        sql: SQLiteInterface | None = None,
        store_events: bool = False,
        capture_site: bool = True,
        clock=time.perf_counter,
        table: str = "timing",
    ):
        """
        Parameters:
        -----------
        sql           : existing SQLiteInterface object (required for streaming)
        store_events  : keep events in memory (optional)
        capture_site  : record file:line where timing is called
        clock         : callable returning float (default: time.perf_counter)
        table         : table name in SQL
        """
        self.capture_site = capture_site
        self._clock = clock
        self._open: dict[int, TimingEvent] = {}

        self.store_events = store_events
        if store_events:
            self._events: list[TimingEvent] = []

        self.backend = SQLBackend(sql, table) if sql else None

    @contextmanager
    def track(
        self,
        name: str,
        *,
        category: str = "general",
        meta: dict | None = None,
        iteration: int | None = None,
        _stack_depth: int = 2,
    ):
        """Context manager for timing a block."""
        event = self._begin(name, category, meta, iteration, _stack_depth)
        try:
            yield event
        finally:
            self._finish(event)

    def start(
        self,
        name: str,
        *,
        category: str = "general",
        meta: dict | None = None,
        iteration: int | None = None,
        _stack_depth: int = 2,
    ) -> int:
        """Start a timing event manually. Returns a unique id for stop()."""
        event = self._begin(name, category, meta, iteration, _stack_depth)
        tid = id(event)
        self._open[tid] = event
        return tid

    def stop(self, tid: int) -> TimingEvent:
        """Stop a manually started timing event."""
        event = self._open.pop(tid)
        self._finish(event)
        return event

    def timed(self, category: str = "general", meta: dict | None = None):
        """Decorator to time entire function call."""

        def decorator(fn):
            @wraps(fn)
            def wrapper(*args, **kwargs):
                with self.track(fn.__qualname__, category=category, meta=meta or {}, _stack_depth=3):
                    return fn(*args, **kwargs)

            return wrapper

        return decorator

    def loop_track(self, name: str, iterable, *, category: str = "general", meta_fn=None):
        """Yield items from iterable while timing each iteration."""
        for i, item in enumerate(iterable):
            m = meta_fn(item) if meta_fn else {}
            with self.track(name, category=category, meta=m, iteration=i, _stack_depth=3):
                yield item

    def _begin(self, name, category, meta, iteration, stack_depth) -> TimingEvent:
        site = None
        if self.capture_site:
            try:
                frame = inspect.stack()[stack_depth]
                site = f"{Path(frame.filename).name}:{frame.lineno}"
            except Exception:
                pass

        event = TimingEvent(
            name=name,
            category=category,
            start=self._clock(),
            meta=meta or {},
            call_site=site,
            iteration=iteration,
        )
        return event

    def _finish(self, event: TimingEvent):
        event.end = self._clock()
        event.duration = event.end - event.start

        if self.store_events:
            self._events.append(event)

        if self.backend:
            self.backend.write(event)

    def events(self):
        """Return in-memory events if store_events=True"""
        if not self.store_events:
            raise RuntimeError("Events are not stored in memory. Set store_events=True.")
        return list(self._events)

    def reset(self):
        """Clear in-memory events (does nothing for SQL backend)."""
        if self.store_events:
            self._events.clear()
        self._open.clear()

# =========================================================================== #
