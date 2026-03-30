"""Tests for iCoder EventLog."""

from __future__ import annotations

import json
from pathlib import Path

from mcp_coder.icoder.core.event_log import EventLog


def test_emit_records_event(tmp_path: Path) -> None:
    log = EventLog(logs_dir=tmp_path)
    log.emit("input_received", text="/help")
    assert len(log.entries) == 1
    assert log.entries[0].event == "input_received"
    assert log.entries[0].data["text"] == "/help"
    log.close()


def test_timestamps_monotonic(tmp_path: Path) -> None:
    log = EventLog(logs_dir=tmp_path)
    log.emit("first")
    log.emit("second")
    assert log.entries[1].t >= log.entries[0].t
    log.close()


def test_jsonl_file_written(tmp_path: Path) -> None:
    log = EventLog(logs_dir=tmp_path)
    log.emit("input_received", text="hello")
    log.close()
    jsonl_files = list(tmp_path.glob("icoder_*.jsonl"))
    assert len(jsonl_files) == 1
    lines = jsonl_files[0].read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 1
    data = json.loads(lines[0])
    assert data["event"] == "input_received"
    assert data["text"] == "hello"
    assert "t" in data


def test_jsonl_filename_format(tmp_path: Path) -> None:
    log = EventLog(logs_dir=tmp_path)
    log.close()
    jsonl_files = list(tmp_path.glob("icoder_*.jsonl"))
    assert len(jsonl_files) == 1
    name = jsonl_files[0].stem  # e.g. "icoder_2026-03-29T14-30-00"
    assert name.startswith("icoder_")


def test_creates_logs_dir(tmp_path: Path) -> None:
    new_dir = tmp_path / "subdir" / "logs"
    log = EventLog(logs_dir=new_dir)
    log.emit("test")
    log.close()
    assert new_dir.exists()


def test_context_manager(tmp_path: Path) -> None:
    with EventLog(logs_dir=tmp_path) as log:
        log.emit("test_event", key="value")
        assert len(log.entries) == 1
    # File should be closed after exiting context
    jsonl_files = list(tmp_path.glob("icoder_*.jsonl"))
    assert len(jsonl_files) == 1


def test_multiple_events_multiple_lines(tmp_path: Path) -> None:
    log = EventLog(logs_dir=tmp_path)
    log.emit("first")
    log.emit("second")
    log.emit("third")
    log.close()
    jsonl_files = list(tmp_path.glob("icoder_*.jsonl"))
    lines = jsonl_files[0].read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 3
