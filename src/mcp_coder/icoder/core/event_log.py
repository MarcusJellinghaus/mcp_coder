"""Structured event log: in-memory list + JSONL file output."""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import IO

from mcp_coder.icoder.core.types import EventEntry


class EventLog:
    """Structured event log: in-memory list + JSONL file output."""

    def __init__(self, logs_dir: str | Path = "logs") -> None:
        """Initialize event log. Creates JSONL file in logs_dir.

        Filename: icoder_<ISO_timestamp>.jsonl
        e.g.: icoder_2026-03-29T14-30-00.jsonl
        """
        logs_path = Path(logs_dir)
        os.makedirs(logs_path, exist_ok=True)

        timestamp = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")
        filename = f"icoder_{timestamp}.jsonl"

        self._start: float = time.monotonic()
        self._entries: list[EventEntry] = []
        self._file: IO[str] = open(  # noqa: SIM115
            logs_path / filename, "a", encoding="utf-8"
        )

    def emit(self, event: str, **data: object) -> EventEntry:
        """Record a structured event.

        Args:
            event: Event type name (e.g. "input_received")
            **data: Arbitrary key-value pairs for this event

        Returns:
            The created EventEntry (with auto-computed timestamp).
        """
        entry = EventEntry(
            t=time.monotonic() - self._start,
            event=event,
            data=dict(data),
        )
        self._entries.append(entry)
        self._file.write(
            json.dumps({"t": entry.t, "event": entry.event, **entry.data}) + "\n"
        )
        self._file.flush()
        return entry

    @property
    def entries(self) -> list[EventEntry]:
        """Return copy of all recorded events (for testing/inspection)."""
        return list(self._entries)

    def close(self) -> None:
        """Flush and close the JSONL file handle."""
        if not self._file.closed:
            self._file.flush()
            self._file.close()

    def __enter__(self) -> EventLog:
        """Support context manager usage."""
        return self

    def __exit__(self, *exc: object) -> None:
        """Close on context manager exit."""
        self.close()
