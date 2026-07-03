"""Structured event log: in-memory list + JSONL file output."""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import IO, TYPE_CHECKING, Any, Iterator

from mcp_coder.icoder.core.types import EventEntry

if TYPE_CHECKING:
    from mcp_coder.icoder.env_setup import RuntimeInfo

logger = logging.getLogger(__name__)


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


def _chat_path_for(jsonl_path: Path) -> Path:
    """Return the paired ``_chat.txt`` path for a given JSONL log path.

    The chat sidecar shares the JSONL stem (including any ``-2`` /
    ``-3`` collision suffix), so the pair can never desynchronize.
    """
    return jsonl_path.with_name(jsonl_path.stem + "_chat.txt")


def _try_open_chat(path: Path) -> IO[str] | None:
    """Open the chat sidecar for append; return ``None`` on failure.

    Best-effort by design: a missing/locked/read-only chat file must
    not break iCoder. Failures are logged once at warning level.

    Returns:
        Open file handle in append mode, or ``None`` if the open failed.
    """
    try:
        return open(path, "a", encoding="utf-8")  # noqa: SIM115
    except OSError as exc:
        logger.warning("iCoder chat mirror disabled (%s): %s", path, exc)
        return None


class EventLog:
    """Structured event log: in-memory list + JSONL file output.

    ``write_chat`` must be called only from the Textual UI thread; the
    chat sidecar handle has no locking.
    """

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
        self._chat_path: Path = _chat_path_for(self._path)
        self._chat_file: IO[str] | None = _try_open_chat(self._chat_path)

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
    def logs_dir(self) -> Path:
        """Directory that holds this session's log files."""
        return self._logs_dir

    @property
    def current_path(self) -> Path:
        """Path of the active JSONL file."""
        return self._path

    @property
    def current_chat_path(self) -> Path:
        """Path of the paired ``_chat.txt`` sidecar.

        Always present (even when the file failed to open); callers
        must not assume the file exists on disk.
        """
        return self._chat_path

    def write_chat(self, line: str) -> None:
        r"""Append ``line + "\n"`` to the chat sidecar; best-effort.

        No-op when the sidecar failed to open. On write failure the
        file is closed and further calls become no-ops; the exception
        is swallowed so a broken mirror cannot break iCoder.
        """
        if self._chat_file is None:
            return
        try:
            self._chat_file.write(line + "\n")
            self._chat_file.flush()
        except OSError as exc:
            logger.warning(
                "iCoder chat mirror write failed (%s): %s", self._chat_path, exc
            )
            try:
                self._chat_file.close()
            except OSError:
                pass
            self._chat_file = None

    def rotate(self) -> Path:
        """Close current JSONL file, open a fresh one with new timestamp.

        Resets monotonic clock and clears in-memory entries. Subsequent
        emit() calls write to the new file. The new file starts empty;
        callers that need a self-contained log (so the picker filter on
        ``session_start.provider`` can see it) must invoke
        ``emit_session_start`` immediately after. The paired
        ``_chat.txt`` sidecar is rotated in lock-step so the two files
        always share a stem.

        Returns:
            Path of the freshly opened JSONL file.
        """
        self._file.flush()
        self._file.close()
        if self._chat_file is not None:
            try:
                self._chat_file.flush()
                self._chat_file.close()
            except OSError as exc:
                logger.warning(
                    "iCoder chat mirror flush/close failed during rotate (%s): %s",
                    self._chat_path,
                    exc,
                )
            self._chat_file = None
        new_path = _allocate_log_path(self._logs_dir)
        self._file = open(new_path, "a", encoding="utf-8")  # noqa: SIM115
        self._start = time.monotonic()
        self._entries.clear()
        self._path = new_path
        self._chat_path = _chat_path_for(new_path)
        self._chat_file = _try_open_chat(self._chat_path)
        return new_path

    @property
    def entries(self) -> list[EventEntry]:
        """Copy of all recorded events (for testing/inspection)."""
        return list(self._entries)

    def close(self) -> None:
        """Flush and close the JSONL file handle and the chat sidecar."""
        if not self._file.closed:
            self._file.flush()
            self._file.close()
        if self._chat_file is not None and not self._chat_file.closed:
            try:
                self._chat_file.flush()
                self._chat_file.close()
            except OSError:
                pass

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
        payload["mcp_coder_utils_version"] = runtime_info.mcp_coder_utils_version
        payload["python_version"] = runtime_info.python_version
        payload["claude_code_version"] = runtime_info.claude_code_version
        payload["tool_env"] = runtime_info.tool_env_path
        payload["project_venv"] = runtime_info.project_venv_path
        payload["project_dir"] = runtime_info.project_dir
        payload["mcp_servers"] = {s.name: s.version for s in runtime_info.mcp_servers}
        payload["mcp_connection_status"] = {
            s.name: {"ok": s.ok, "status_text": s.status_text}
            for s in (runtime_info.mcp_connection_status or [])
        }
        payload["mcp_tools_exposed"] = runtime_info.mcp_tools_exposed
        payload["mcp_tools_status"] = runtime_info.mcp_tools_status
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
