"""Tests for icoder log inventory."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from mcp_coder.icoder.core.log_inventory import FIRST_PROMPT_MAX, list_icoder_logs
from mcp_coder.icoder.core.types import LogSummary


def _write_log(path: Path, events: list[dict[str, object]]) -> None:
    """Write a JSONL log file with the given events."""
    lines = [json.dumps(ev) for ev in events]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def test_empty_directory_returns_empty_list(tmp_path: Path) -> None:
    assert list_icoder_logs(tmp_path) == []


def test_single_log_with_session_start_and_two_inputs(tmp_path: Path) -> None:
    log_path = tmp_path / "icoder_2026-05-01T10-00-00.jsonl"
    _write_log(
        log_path,
        [
            {"t": 0.0, "event": "session_start", "provider": "claude"},
            {"t": 0.1, "event": "input_received", "text": "hello world"},
            {"t": 0.2, "event": "input_received", "text": "second"},
        ],
    )
    result = list_icoder_logs(tmp_path)
    assert len(result) == 1
    summary = result[0]
    assert summary.path == log_path
    assert summary.provider == "claude"
    assert summary.n_turns == 2
    assert summary.first_prompt == "hello world"


def test_first_prompt_truncated_to_max(tmp_path: Path) -> None:
    long_text = "x" * 200
    log_path = tmp_path / "icoder_2026-05-01T10-00-00.jsonl"
    _write_log(
        log_path,
        [
            {"t": 0.0, "event": "session_start", "provider": "claude"},
            {"t": 0.1, "event": "input_received", "text": long_text},
        ],
    )
    result = list_icoder_logs(tmp_path)
    assert len(result) == 1
    assert len(result[0].first_prompt) == FIRST_PROMPT_MAX
    assert result[0].first_prompt == long_text[:FIRST_PROMPT_MAX]


def test_provider_filter_excludes_other_providers(tmp_path: Path) -> None:
    claude_path = tmp_path / "icoder_2026-05-01T10-00-00.jsonl"
    langchain_path = tmp_path / "icoder_2026-05-02T10-00-00.jsonl"
    _write_log(
        claude_path,
        [
            {"t": 0.0, "event": "session_start", "provider": "claude"},
            {"t": 0.1, "event": "input_received", "text": "claude turn"},
        ],
    )
    _write_log(
        langchain_path,
        [
            {"t": 0.0, "event": "session_start", "provider": "langchain"},
            {"t": 0.1, "event": "input_received", "text": "langchain turn"},
        ],
    )
    result = list_icoder_logs(tmp_path, provider="claude")
    assert len(result) == 1
    assert result[0].path == claude_path
    assert result[0].provider == "claude"


def test_sorted_newest_first_by_filename_timestamp(tmp_path: Path) -> None:
    older = tmp_path / "icoder_2026-05-01T10-00-00.jsonl"
    newer = tmp_path / "icoder_2026-05-02T10-00-00.jsonl"
    # Write newer first, older second to defeat any incidental dir ordering.
    _write_log(
        newer,
        [
            {"t": 0.0, "event": "session_start", "provider": "claude"},
            {"t": 0.1, "event": "input_received", "text": "newer"},
        ],
    )
    _write_log(
        older,
        [
            {"t": 0.0, "event": "session_start", "provider": "claude"},
            {"t": 0.1, "event": "input_received", "text": "older"},
        ],
    )
    result = list_icoder_logs(tmp_path)
    assert [s.path for s in result] == [newer, older]
    assert result[0].timestamp > result[1].timestamp


def test_log_without_session_start_or_input(tmp_path: Path) -> None:
    log_path = tmp_path / "icoder_2026-05-01T10-00-00.jsonl"
    _write_log(log_path, [])
    # Included when provider is None.
    result_no_filter = list_icoder_logs(tmp_path)
    assert len(result_no_filter) == 1
    summary = result_no_filter[0]
    assert summary.provider is None
    assert summary.n_turns == 0
    assert summary.first_prompt == ""
    # Excluded when filtering by provider.
    assert list_icoder_logs(tmp_path, provider="claude") == []


def test_corrupt_json_propagates(tmp_path: Path) -> None:
    log_path = tmp_path / "icoder_2026-05-01T10-00-00.jsonl"
    log_path.write_text(
        '{"t": 0.0, "event": "session_start", "provider": "claude"}\n'
        "not valid json\n",
        encoding="utf-8",
    )
    with pytest.raises(json.JSONDecodeError):
        list_icoder_logs(tmp_path)


def test_slash_command_counts_as_turn(tmp_path: Path) -> None:
    log_path = tmp_path / "icoder_2026-05-01T10-00-00.jsonl"
    _write_log(
        log_path,
        [
            {"t": 0.0, "event": "session_start", "provider": "claude"},
            {"t": 0.1, "event": "input_received", "text": "/help"},
            {"t": 0.2, "event": "input_received", "text": "follow up"},
        ],
    )
    result = list_icoder_logs(tmp_path)
    assert len(result) == 1
    assert result[0].n_turns == 2
    assert result[0].first_prompt == "/help"


def test_filename_with_microseconds_parsed(tmp_path: Path) -> None:
    log_path = tmp_path / "icoder_2026-05-01T10-00-00-123456.jsonl"
    _write_log(
        log_path,
        [
            {"t": 0.0, "event": "session_start", "provider": "claude"},
        ],
    )
    result = list_icoder_logs(tmp_path)
    assert len(result) == 1
    assert result[0].timestamp == datetime(
        2026, 5, 1, 10, 0, 0, 123456, tzinfo=timezone.utc
    )


def test_unparseable_filename_falls_back_to_mtime(tmp_path: Path) -> None:
    log_path = tmp_path / "icoder_not-a-date.jsonl"
    _write_log(
        log_path,
        [
            {"t": 0.0, "event": "session_start", "provider": "claude"},
        ],
    )
    result = list_icoder_logs(tmp_path)
    assert len(result) == 1
    expected = datetime.fromtimestamp(log_path.stat().st_mtime, tz=timezone.utc)
    assert result[0].timestamp == expected


def test_logsummary_is_frozen_and_hashable() -> None:
    summary = LogSummary(
        path=Path("/tmp/icoder_test.jsonl"),
        timestamp=datetime(2026, 5, 1, 10, 0, 0, tzinfo=timezone.utc),
        provider="claude",
        n_turns=3,
        first_prompt="hello",
    )
    # Frozen: cannot be mutated.
    with pytest.raises(Exception):
        summary.n_turns = 4  # type: ignore[misc]
    # Hashable: can be put in a set.
    assert {summary} == {summary}


def test_non_matching_glob_files_ignored(tmp_path: Path) -> None:
    (tmp_path / "other.jsonl").write_text("{}\n", encoding="utf-8")
    (tmp_path / "icoder_2026-05-01T10-00-00.txt").write_text(
        "ignored", encoding="utf-8"
    )
    valid = tmp_path / "icoder_2026-05-01T10-00-00.jsonl"
    _write_log(
        valid,
        [{"t": 0.0, "event": "session_start", "provider": "claude"}],
    )
    result = list_icoder_logs(tmp_path)
    assert [s.path for s in result] == [valid]


def test_logs_dir_accepts_string(tmp_path: Path) -> None:
    log_path = tmp_path / "icoder_2026-05-01T10-00-00.jsonl"
    _write_log(
        log_path,
        [{"t": 0.0, "event": "session_start", "provider": "claude"}],
    )
    result = list_icoder_logs(str(tmp_path))
    assert len(result) == 1
    assert result[0].path == log_path
