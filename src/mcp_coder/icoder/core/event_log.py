"""Structured event log: in-memory list + JSONL file output."""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import IO, TYPE_CHECKING, Any, Iterator

from mcp_coder.icoder.core.types import EventEntry

if TYPE_CHECKING:
    from mcp_coder.icoder.env_setup import RuntimeInfo


def _make_log_filename() -> str:
    """Build a JSONL filename for the current UTC instant.

    Returns:
        Filename of the form ``icoder_<ISO_timestamp>.jsonl``. The
        timestamp is microsecond-precision but the OS clock is coarser
        on some platforms (notably Windows), so callers must still
        guard against collisions.
    """
    timestamp = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H-%M-%S-%f")
    return f"icoder_{timestamp}.jsonl"


def _allocate_log_path(logs_dir: Path) -> Path:
    """Return a fresh, non-colliding ``icoder_*.jsonl`` path under ``logs_dir``.

    The base name is timestamp-derived (see ``_make_log_filename``).
    When that path already exists — e.g. two rotations within the same
    OS clock tick on Windows — a ``-<n>`` counter suffix is appended
    until a free name is found.

    Returns:
        Path to a filename that does not yet exist on disk.
    """
    base = logs_dir / _make_log_filename()
    if not base.exists():
        return base
    stem = base.stem  # e.g. "icoder_2026-05-11T10-00-00-123456"
    suffix = base.suffix  # ".jsonl"
    counter = 2
    while True:
        candidate = logs_dir / f"{stem}-{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


class EventLog:
    """Structured event log: in-memory list + JSONL file output."""

    def __init__(self, logs_dir: str | Path = "logs") -> None:
        """Initialize event log. Creates JSONL file in logs_dir.

        Filename: icoder_<ISO_timestamp>.jsonl
        e.g.: icoder_2026-03-29T14-30-00-123456.jsonl
        """
        logs_path = Path(logs_dir)
        os.makedirs(logs_path, exist_ok=True)

        self._logs_dir: Path = logs_path
        self._path: Path = _allocate_log_path(logs_path)
        self._start: float = time.monotonic()
        self._entries: list[EventEntry] = []
        self._file: IO[str] = open(self._path, "a", encoding="utf-8")  # noqa: SIM115

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
    def current_path(self) -> Path:
        """Return the path of the active JSONL file."""
        return self._path

    def rotate(self) -> Path:
        """Close current JSONL file, open a fresh one with new timestamp.

        Resets monotonic clock and clears in-memory entries. Subsequent
        emit() calls write to the new file. The new file starts empty;
        callers that need a self-contained log (so the picker filter on
        ``session_start.provider`` can see it) must invoke
        ``emit_session_start`` immediately after.

        Returns:
            Path of the freshly opened JSONL file.
        """
        self._file.flush()
        self._file.close()
        new_path = _allocate_log_path(self._logs_dir)
        self._file = open(new_path, "a", encoding="utf-8")  # noqa: SIM115
        self._start = time.monotonic()
        self._entries.clear()
        self._path = new_path
        return new_path

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
        """Support context manager usage.

        Returns:
            Self for use in with-statements.
        """
        return self

    def __exit__(self, *exc: object) -> None:
        """Close on context manager exit."""
        self.close()


def emit_session_start(
    event_log: EventLog,
    *,
    provider: str,
    runtime_info: "RuntimeInfo | None" = None,
    session_id: str | None = None,
) -> EventEntry:
    """Emit a ``session_start`` event into ``event_log``.

    The payload always carries the current ``provider`` (so the
    startup picker — which filters on ``session_start.provider`` —
    can list the file). When ``runtime_info`` is supplied, the
    runtime fields used by the in-app banner are included as well;
    when omitted (e.g. unit tests), only ``provider`` and
    ``session_id`` are written.

    Returns:
        The recorded ``EventEntry`` for the emitted ``session_start``.
    """
    payload: dict[str, object] = {"provider": provider}
    if runtime_info is not None:
        payload["mcp_coder_version"] = runtime_info.mcp_coder_version
        payload["tool_env"] = runtime_info.tool_env_path
        payload["project_venv"] = runtime_info.project_venv_path
        payload["project_dir"] = runtime_info.project_dir
        payload["mcp_servers"] = {s.name: s.version for s in runtime_info.mcp_servers}
        payload["mcp_connection_status"] = {
            s.name: {"ok": s.ok, "status_text": s.status_text}
            for s in (runtime_info.mcp_connection_status or [])
        }
    if session_id is not None:
        payload["session_id"] = session_id
    return event_log.emit("session_start", **payload)


def iter_events(path: Path | str) -> Iterator[dict[str, Any]]:
    """Yield each JSONL event as a dict. Skips blank lines.

    Raises FileNotFoundError if path does not exist.
    Raises json.JSONDecodeError on malformed lines (no swallowing).
    """
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped:
                yield json.loads(stripped)


def read_session_id_from_log(path: Path | str) -> str | None:
    """Resolve the recorded session_id from a JSONL event log.

    Reads ``session_start.session_id`` from ``path``; if absent, falls
    back to the most recent ``stream_event{type=done}`` entry's
    ``session_id``.

    Returns:
        The recovered session id, or ``None`` when no candidate is found.
    """
    session_id: str | None = None
    last_done_sid: str | None = None
    for event in iter_events(path):
        kind = event.get("event")
        if kind == "session_start":
            raw = event.get("session_id")
            if isinstance(raw, str):
                session_id = raw
                break
        elif kind == "stream_event" and event.get("type") == "done":
            raw = event.get("session_id")
            if isinstance(raw, str):
                last_done_sid = raw
    if session_id is None:
        session_id = last_done_sid
    return session_id
