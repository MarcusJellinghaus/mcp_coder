"""Tests for iCoder CLI resume/continue-session resolution wiring."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

from tests.icoder.conftest import (
    FAKE_RUNTIME_INFO,
    _patch_all_icoder_deps,
    make_icoder_args,
)


def _write_log(path: Path, events: list[dict[str, object]]) -> None:
    """Write a JSONL log file with the given events."""
    lines = [json.dumps(ev) for ev in events]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def test_continue_session_from_json_path_hard_errors(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """`--continue-session-from foo.json` rejects with exit 1 and clear message."""
    from mcp_coder.cli.commands.icoder import execute_icoder

    (tmp_path / "logs").mkdir()
    _patch_all_icoder_deps(monkeypatch, tmp_path)
    response_json = tmp_path / "old_response.json"
    response_json.write_text("{}", encoding="utf-8")

    args = make_icoder_args(tmp_path)
    args.continue_session_from = str(response_json)

    with caplog.at_level(logging.ERROR):
        result = execute_icoder(args)

    assert result == 1
    assert ".jsonl event-log path" in caplog.text


def test_continue_session_from_missing_jsonl_returns_1(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """`--continue-session-from missing.jsonl` returns exit 1."""
    from mcp_coder.cli.commands.icoder import execute_icoder

    (tmp_path / "logs").mkdir()
    _patch_all_icoder_deps(monkeypatch, tmp_path)

    args = make_icoder_args(tmp_path)
    args.continue_session_from = str(tmp_path / "does_not_exist.jsonl")

    with caplog.at_level(logging.ERROR):
        result = execute_icoder(args)

    assert result == 1
    assert "not a .jsonl" in caplog.text or "not found" in caplog.text


def test_continue_session_from_real_jsonl_passes_resume_log_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A valid .jsonl is passed to ICoderApp via resume_log_path; sid resolved."""
    from mcp_coder.cli.commands.icoder import execute_icoder
    from mcp_coder.icoder.ui.app import ICoderApp

    (tmp_path / "logs").mkdir()
    log_path = tmp_path / "logs" / "icoder_2026-05-01T10-00-00.jsonl"
    _write_log(
        log_path,
        [
            {
                "t": 0.0,
                "event": "session_start",
                "provider": "claude",
                "session_id": "sess-resume-1",
            }
        ],
    )

    captured_kwargs: list[dict[str, object]] = []

    def capturing_init(self: object, app_core: object, **kwargs: object) -> None:
        captured_kwargs.append(kwargs)

    monkeypatch.setattr(ICoderApp, "__init__", capturing_init)
    monkeypatch.setattr(ICoderApp, "run", lambda self: None)
    monkeypatch.setattr(
        "mcp_coder.cli.commands.icoder.setup_icoder_environment",
        lambda *_a, **_kw: FAKE_RUNTIME_INFO,
    )
    monkeypatch.setattr(
        "mcp_coder.cli.commands.icoder.resolve_llm_method",
        lambda _: ("claude", None),
    )
    monkeypatch.setattr(
        "mcp_coder.cli.commands.icoder.parse_llm_method_from_args",
        lambda _: "claude",
    )
    monkeypatch.setattr(
        "mcp_coder.cli.commands.icoder.resolve_mcp_config_path",
        lambda *a, **_kw: None,
    )
    monkeypatch.setattr(
        "mcp_coder.icoder.skills.load_skills",
        lambda _: [],
    )
    monkeypatch.setattr(
        "mcp_coder.icoder.skills.register_skill_commands",
        lambda registry, skills, provider, **kwargs: [],
    )

    args = make_icoder_args(tmp_path)
    args.continue_session_from = str(log_path)

    result = execute_icoder(args)

    assert result == 0
    assert len(captured_kwargs) == 1
    assert captured_kwargs[0]["resume_log_path"] == log_path


def test_continue_session_no_prior_logs_logs_message_and_runs_fresh(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """`--continue-session` without prior logs logs message and runs fresh."""
    from mcp_coder.cli.commands.icoder import execute_icoder
    from mcp_coder.icoder.ui.app import ICoderApp

    (tmp_path / "logs").mkdir()  # empty logs dir

    captured_kwargs: list[dict[str, object]] = []

    def capturing_init(self: object, app_core: object, **kwargs: object) -> None:
        captured_kwargs.append(kwargs)

    monkeypatch.setattr(ICoderApp, "__init__", capturing_init)
    monkeypatch.setattr(ICoderApp, "run", lambda self: None)
    monkeypatch.setattr(
        "mcp_coder.cli.commands.icoder.setup_icoder_environment",
        lambda *_a, **_kw: FAKE_RUNTIME_INFO,
    )
    monkeypatch.setattr(
        "mcp_coder.cli.commands.icoder.resolve_llm_method",
        lambda _: ("claude", None),
    )
    monkeypatch.setattr(
        "mcp_coder.cli.commands.icoder.parse_llm_method_from_args",
        lambda _: "claude",
    )
    monkeypatch.setattr(
        "mcp_coder.cli.commands.icoder.resolve_mcp_config_path",
        lambda *a, **_kw: None,
    )
    monkeypatch.setattr(
        "mcp_coder.icoder.skills.load_skills",
        lambda _: [],
    )
    monkeypatch.setattr(
        "mcp_coder.icoder.skills.register_skill_commands",
        lambda registry, skills, provider, **kwargs: [],
    )

    args = make_icoder_args(tmp_path)
    args.continue_session = True

    with caplog.at_level(logging.INFO):
        result = execute_icoder(args)

    assert result == 0
    assert len(captured_kwargs) == 1
    assert captured_kwargs[0].get("resume_log_path") is None
    assert "No previous sessions in this project." in caplog.text


def test_continue_session_with_prior_logs_invokes_picker(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """`--continue-session` with prior logs calls run_startup_picker once."""
    from mcp_coder.cli.commands.icoder import execute_icoder
    from mcp_coder.icoder.ui.app import ICoderApp

    (tmp_path / "logs").mkdir()
    log_path = tmp_path / "logs" / "icoder_2026-05-01T10-00-00.jsonl"
    _write_log(
        log_path,
        [
            {
                "t": 0.0,
                "event": "session_start",
                "provider": "claude",
                "session_id": "sess-1",
            },
            {"t": 0.1, "event": "input_received", "text": "hi"},
        ],
    )

    picker_calls: list[object] = []

    def fake_picker(summaries: object, **_kw: object) -> Path:
        picker_calls.append(summaries)
        return log_path

    captured_kwargs: list[dict[str, object]] = []

    def capturing_init(self: object, app_core: object, **kwargs: object) -> None:
        captured_kwargs.append(kwargs)

    monkeypatch.setattr(ICoderApp, "__init__", capturing_init)
    monkeypatch.setattr(ICoderApp, "run", lambda self: None)
    monkeypatch.setattr("mcp_coder.cli.commands.icoder.run_startup_picker", fake_picker)
    monkeypatch.setattr(
        "mcp_coder.cli.commands.icoder.setup_icoder_environment",
        lambda *_a, **_kw: FAKE_RUNTIME_INFO,
    )
    monkeypatch.setattr(
        "mcp_coder.cli.commands.icoder.resolve_llm_method",
        lambda _: ("claude", None),
    )
    monkeypatch.setattr(
        "mcp_coder.cli.commands.icoder.parse_llm_method_from_args",
        lambda _: "claude",
    )
    monkeypatch.setattr(
        "mcp_coder.cli.commands.icoder.resolve_mcp_config_path",
        lambda *a, **_kw: None,
    )
    monkeypatch.setattr(
        "mcp_coder.icoder.skills.load_skills",
        lambda _: [],
    )
    monkeypatch.setattr(
        "mcp_coder.icoder.skills.register_skill_commands",
        lambda registry, skills, provider, **kwargs: [],
    )

    args = make_icoder_args(tmp_path)
    args.continue_session = True

    result = execute_icoder(args)

    assert result == 0
    assert len(picker_calls) == 1
    assert len(captured_kwargs) == 1
    assert captured_kwargs[0]["resume_log_path"] == log_path


def test_continue_session_picker_escape_runs_fresh(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """When the picker returns None (Esc), the app runs fresh (no resume)."""
    from mcp_coder.cli.commands.icoder import execute_icoder
    from mcp_coder.icoder.ui.app import ICoderApp

    (tmp_path / "logs").mkdir()
    log_path = tmp_path / "logs" / "icoder_2026-05-01T10-00-00.jsonl"
    _write_log(
        log_path,
        [
            {"t": 0.0, "event": "session_start", "provider": "claude"},
            {"t": 0.1, "event": "input_received", "text": "hi"},
        ],
    )

    captured_kwargs: list[dict[str, object]] = []

    def capturing_init(self: object, app_core: object, **kwargs: object) -> None:
        captured_kwargs.append(kwargs)

    monkeypatch.setattr(ICoderApp, "__init__", capturing_init)
    monkeypatch.setattr(ICoderApp, "run", lambda self: None)
    monkeypatch.setattr(
        "mcp_coder.cli.commands.icoder.run_startup_picker",
        lambda summaries, **_kw: None,
    )
    monkeypatch.setattr(
        "mcp_coder.cli.commands.icoder.setup_icoder_environment",
        lambda *_a, **_kw: FAKE_RUNTIME_INFO,
    )
    monkeypatch.setattr(
        "mcp_coder.cli.commands.icoder.resolve_llm_method",
        lambda _: ("claude", None),
    )
    monkeypatch.setattr(
        "mcp_coder.cli.commands.icoder.parse_llm_method_from_args",
        lambda _: "claude",
    )
    monkeypatch.setattr(
        "mcp_coder.cli.commands.icoder.resolve_mcp_config_path",
        lambda *a, **_kw: None,
    )
    monkeypatch.setattr(
        "mcp_coder.icoder.skills.load_skills",
        lambda _: [],
    )
    monkeypatch.setattr(
        "mcp_coder.icoder.skills.register_skill_commands",
        lambda registry, skills, provider, **kwargs: [],
    )

    args = make_icoder_args(tmp_path)
    args.continue_session = True

    result = execute_icoder(args)

    assert result == 0
    assert len(captured_kwargs) == 1
    assert captured_kwargs[0].get("resume_log_path") is None
