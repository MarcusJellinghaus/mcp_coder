"""Tests for iCoder EventLog."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from unittest.mock import patch

import pytest

from mcp_coder.icoder.core import event_log as event_log_module
from mcp_coder.icoder.core.event_log import (
    EventLog,
    emit_session_start,
    iter_events,
)


def test_emit_records_event(tmp_path: Path) -> None:
    with EventLog(logs_dir=tmp_path) as log:
        log.emit("input_received", text="/help")
        assert len(log.entries) == 1
        assert log.entries[0].event == "input_received"
        assert log.entries[0].data["text"] == "/help"


def test_timestamps_monotonic(tmp_path: Path) -> None:
    with EventLog(logs_dir=tmp_path) as log:
        log.emit("first")
        log.emit("second")
        assert log.entries[1].t >= log.entries[0].t


def test_jsonl_file_written(tmp_path: Path) -> None:
    with EventLog(logs_dir=tmp_path) as log:
        log.emit("input_received", text="hello")
    jsonl_files = list(tmp_path.glob("icoder_*.jsonl"))
    assert len(jsonl_files) == 1
    lines = jsonl_files[0].read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 1
    data = json.loads(lines[0])
    assert data["event"] == "input_received"
    assert data["text"] == "hello"
    assert "t" in data


def test_jsonl_filename_format(tmp_path: Path) -> None:
    with EventLog(logs_dir=tmp_path) as _log:
        pass
    jsonl_files = list(tmp_path.glob("icoder_*.jsonl"))
    assert len(jsonl_files) == 1
    name = jsonl_files[0].stem  # e.g. "icoder_2026-03-29T14-30-00"
    assert name.startswith("icoder_")


def test_creates_logs_dir(tmp_path: Path) -> None:
    new_dir = tmp_path / "subdir" / "logs"
    with EventLog(logs_dir=new_dir) as log:
        log.emit("test")
    assert new_dir.exists()


def test_context_manager(tmp_path: Path) -> None:
    with EventLog(logs_dir=tmp_path) as log:
        log.emit("test_event", key="value")
        assert len(log.entries) == 1
    # File should be closed after exiting context
    jsonl_files = list(tmp_path.glob("icoder_*.jsonl"))
    assert len(jsonl_files) == 1


def test_multiple_events_multiple_lines(tmp_path: Path) -> None:
    with EventLog(logs_dir=tmp_path) as log:
        log.emit("first")
        log.emit("second")
        log.emit("third")
    jsonl_files = list(tmp_path.glob("icoder_*.jsonl"))
    lines = jsonl_files[0].read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 3


def test_current_path_matches_initial_file(tmp_path: Path) -> None:
    with EventLog(logs_dir=tmp_path) as log:
        log.emit("input_received", text="hello")
        jsonl_files = list(tmp_path.glob("icoder_*.jsonl"))
        assert len(jsonl_files) == 1
        assert log.current_path == jsonl_files[0]


def test_rotate_changes_current_path(tmp_path: Path) -> None:
    with EventLog(logs_dir=tmp_path) as log:
        original_path = log.current_path
        new_path = log.rotate()
        assert new_path != original_path
        assert log.current_path == new_path


def test_rotate_keeps_old_file_on_disk(tmp_path: Path) -> None:
    with EventLog(logs_dir=tmp_path) as log:
        log.emit("first")
        original_path = log.current_path
        log.rotate()
        assert original_path.exists()
        assert log.current_path.exists()
        assert original_path != log.current_path


def test_rotate_redirects_writes_to_new_file(tmp_path: Path) -> None:
    with EventLog(logs_dir=tmp_path) as log:
        log.emit("before_rotate", value=1)
        original_path = log.current_path
        log.rotate()
        log.emit("after_rotate", value=2)
        new_path = log.current_path

    old_lines = original_path.read_text(encoding="utf-8").strip().split("\n")
    new_lines = new_path.read_text(encoding="utf-8").strip().split("\n")
    assert len(old_lines) == 1
    assert json.loads(old_lines[0])["event"] == "before_rotate"
    assert len(new_lines) == 1
    assert json.loads(new_lines[0])["event"] == "after_rotate"


def test_rotate_clears_entries_and_resets_clock(tmp_path: Path) -> None:
    with EventLog(logs_dir=tmp_path) as log:
        log.emit("first")
        log.emit("second")
        assert len(log.entries) == 2
        log.rotate()
        assert log.entries == []
        log.emit("after_rotate")
        assert len(log.entries) == 1
        # Clock reset means the new emit's t should be very small (~0).
        assert log.entries[0].t < 1.0


def test_iter_events_yields_dicts(tmp_path: Path) -> None:
    with EventLog(logs_dir=tmp_path) as log:
        log.emit("first", value=1)
        log.emit("second", text="hello")
        path = log.current_path
    events = list(iter_events(path))
    assert len(events) == 2
    assert events[0]["event"] == "first"
    assert events[0]["value"] == 1
    assert events[1]["event"] == "second"
    assert events[1]["text"] == "hello"


def test_iter_events_skips_blank_lines(tmp_path: Path) -> None:
    path = tmp_path / "test.jsonl"
    path.write_text(
        '{"t": 0.0, "event": "first"}\n\n   \n{"t": 0.1, "event": "second"}\n',
        encoding="utf-8",
    )
    events = list(iter_events(path))
    assert len(events) == 2
    assert events[0]["event"] == "first"
    assert events[1]["event"] == "second"


def test_iter_events_missing_file_raises(tmp_path: Path) -> None:
    missing = tmp_path / "does_not_exist.jsonl"
    with pytest.raises(FileNotFoundError):
        list(iter_events(missing))


def test_rotate_handles_filename_collision(tmp_path: Path) -> None:
    """Two rotations within the same OS clock tick still produce distinct files.

    Simulates the Windows case where ``datetime.now()`` returns the same
    microsecond value for back-to-back calls. The collision-handling
    counter suffix must keep both files alive.
    """
    fixed_name = "icoder_2026-05-11T10-00-00-000000.jsonl"

    with patch(
        "mcp_coder.icoder.core.event_log._make_log_filename",
        return_value=fixed_name,
    ):
        with EventLog(logs_dir=tmp_path) as log:
            first_path = log.current_path
            second_path = log.rotate()
            third_path = log.rotate()

    assert first_path != second_path
    assert second_path != third_path
    assert first_path != third_path
    files = sorted(tmp_path.glob("icoder_*.jsonl"))
    assert len(files) == 3


def test_emit_session_start_writes_provider_to_new_file(tmp_path: Path) -> None:
    """After rotate(), emit_session_start writes a session_start with provider."""
    with EventLog(logs_dir=tmp_path) as log:
        log.emit("input_received", text="hello")
        log.rotate()
        emit_session_start(log, provider="claude")
        new_path = log.current_path

    events = list(iter_events(new_path))
    assert len(events) == 1
    assert events[0]["event"] == "session_start"
    assert events[0]["provider"] == "claude"


def test_emit_session_start_includes_runtime_info_fields(tmp_path: Path) -> None:
    """emit_session_start serialises runtime_info into the event payload."""
    from mcp_coder.icoder.env_setup import RuntimeInfo
    from mcp_coder.utils.mcp_verification import MCPServerInfo

    runtime_info = RuntimeInfo(
        mcp_coder_version="9.9.9",
        mcp_coder_utils_version="9.9.9",
        python_version="3.13.0",
        claude_code_version="1.2.3",
        tool_env_path="/fake/tool",
        project_venv_path="/fake/.venv",
        project_dir="/fake/proj",
        env_vars={},
        mcp_servers=[
            MCPServerInfo(name="srv", path=Path("/fake/srv"), version="1.0"),
        ],
    )
    with EventLog(logs_dir=tmp_path) as log:
        emit_session_start(
            log,
            provider="langchain",
            runtime_info=runtime_info,
            session_id="sess-99",
        )
        path = log.current_path

    events = list(iter_events(path))
    assert len(events) == 1
    payload = events[0]
    assert payload["provider"] == "langchain"
    assert payload["session_id"] == "sess-99"
    assert payload["mcp_coder_version"] == "9.9.9"
    assert payload["mcp_coder_utils_version"] == "9.9.9"
    assert payload["python_version"] == "3.13.0"
    assert payload["claude_code_version"] == "1.2.3"
    assert payload["tool_env"] == "/fake/tool"
    assert payload["project_venv"] == "/fake/.venv"
    assert payload["project_dir"] == "/fake/proj"
    assert payload["mcp_servers"] == {"srv": "1.0"}
    assert payload["mcp_connection_status"] == {}


def test_emit_session_start_payload_covers_live_banner_keys(tmp_path: Path) -> None:
    """Persisted session_start payload contains every key the live banner uses.

    ``format_runtime_banner`` is invoked from ``on_mount`` with a
    ``RuntimeInfo``-shaped dict and from ``do_resume`` with the
    ``session_start`` event payload. For the replayed banner to render
    the same set of lines as the live banner, every key the renderer
    reads must be present in the persisted payload (under either the
    live name or its session_start alias).
    """
    from mcp_coder.icoder.env_setup import RuntimeInfo
    from mcp_coder.utils.mcp_verification import ClaudeMCPStatus, MCPServerInfo

    runtime_info = RuntimeInfo(
        mcp_coder_version="1.2.3",
        mcp_coder_utils_version="4.5.6",
        python_version="3.13.0",
        claude_code_version="claude 1.0.0",
        tool_env_path="/tool",
        project_venv_path="/proj/.venv",
        project_dir="/proj",
        env_vars={},
        mcp_servers=[
            MCPServerInfo(name="srv-a", path=Path("/srv-a"), version="9.0"),
        ],
        mcp_connection_status=[
            ClaudeMCPStatus(name="srv-a", status_text="Connected", ok=True),
        ],
    )
    with EventLog(logs_dir=tmp_path) as log:
        emit_session_start(log, provider="claude", runtime_info=runtime_info)
        path = log.current_path

    events = list(iter_events(path))
    payload = events[0]

    # Live-banner keys read by format_runtime_banner. The renderer
    # accepts either the RuntimeInfo name (e.g. tool_env_path) or the
    # session_start alias (e.g. tool_env); the persisted payload uses
    # the alias for the path fields.
    assert "mcp_coder_version" in payload
    assert "mcp_coder_utils_version" in payload
    assert "python_version" in payload
    assert "claude_code_version" in payload
    assert "tool_env" in payload or "tool_env_path" in payload
    assert "project_venv" in payload or "project_venv_path" in payload
    assert "project_dir" in payload
    assert "mcp_servers" in payload
    assert "mcp_connection_status" in payload


def test_chat_sidecar_created_alongside_jsonl(tmp_path: Path) -> None:
    """Constructor opens both ``.jsonl`` and matching ``_chat.txt``."""
    with EventLog(logs_dir=tmp_path) as log:
        assert log.current_chat_path.exists()
        assert log.current_chat_path.stem == log.current_path.stem + "_chat"
        assert log.current_chat_path.suffix == ".txt"
        assert log.current_chat_path.parent == log.current_path.parent


def test_write_chat_appends_and_flushes(tmp_path: Path) -> None:
    """``write_chat`` appends each line plus newline (empty string = bare newline)."""
    with EventLog(logs_dir=tmp_path) as log:
        log.write_chat("hello")
        log.write_chat("")
        chat_path = log.current_chat_path
    assert chat_path.read_text(encoding="utf-8") == "hello\n\n"


def test_rotate_pairs_files_with_matching_stems(tmp_path: Path) -> None:
    """``rotate()`` switches both files and they share a stem."""
    with EventLog(logs_dir=tmp_path) as log:
        old_jsonl = log.current_path
        old_chat = log.current_chat_path
        log.write_chat("before")
        log.rotate()
        new_jsonl = log.current_path
        new_chat = log.current_chat_path

        assert new_jsonl != old_jsonl
        assert new_chat != old_chat
        assert new_chat.stem == new_jsonl.stem + "_chat"
        assert old_jsonl.exists()
        assert old_chat.exists()
        assert old_chat.read_text(encoding="utf-8") == "before\n"


def test_rotate_preserves_collision_suffix(tmp_path: Path) -> None:
    """Collision suffix on JSONL carries over to the chat sidecar."""
    fixed_name = "icoder_2026-05-11T10-00-00-000000.jsonl"
    with patch(
        "mcp_coder.icoder.core.event_log._make_log_filename",
        return_value=fixed_name,
    ):
        with EventLog(logs_dir=tmp_path) as log:
            first_jsonl = log.current_path
            first_chat = log.current_chat_path
            log.rotate()
            second_jsonl = log.current_path
            second_chat = log.current_chat_path

    assert first_jsonl.name == "icoder_2026-05-11T10-00-00-000000.jsonl"
    assert first_chat.name == "icoder_2026-05-11T10-00-00-000000_chat.txt"
    assert second_jsonl.name == "icoder_2026-05-11T10-00-00-000000-2.jsonl"
    assert second_chat.name == "icoder_2026-05-11T10-00-00-000000-2_chat.txt"


def test_close_closes_both_files(tmp_path: Path) -> None:
    """``close()`` flushes and closes both file handles."""
    log = EventLog(logs_dir=tmp_path)
    chat_file = log._chat_file
    log.close()
    assert log._file.closed
    assert chat_file is not None
    assert chat_file.closed


def test_chat_open_failure_is_best_effort(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """When the chat file cannot be opened, JSONL still works and write_chat is a no-op."""
    real_open = open

    def fake_open(file, *args, **kwargs):  # type: ignore[no-untyped-def]
        path_str = str(file)
        if path_str.endswith("_chat.txt"):
            raise OSError("simulated open failure")
        return real_open(file, *args, **kwargs)

    monkeypatch.setattr(event_log_module, "open", fake_open, raising=False)

    with caplog.at_level(logging.WARNING, logger="mcp_coder.icoder.core.event_log"):
        log = EventLog(logs_dir=tmp_path)
        try:
            assert log._chat_file is None
            assert not log._file.closed
            log.emit("input_received", text="still works")
            log.write_chat("ignored")
        finally:
            log.close()

    assert any(
        "chat mirror disabled" in record.getMessage() for record in caplog.records
    )
