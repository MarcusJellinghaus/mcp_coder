"""Tests for ICoderApp JSONL replay (replay_log)."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

import pytest

from mcp_coder.icoder.core.app_core import AppCore
from mcp_coder.icoder.core.event_log import EventLog
from mcp_coder.icoder.services.llm_service import FakeLLMService
from mcp_coder.icoder.ui.app import ICoderApp
from mcp_coder.icoder.ui.replay import replay_log
from mcp_coder.icoder.ui.widgets.input_area import InputArea
from mcp_coder.icoder.ui.widgets.output_log import OutputLog
from mcp_coder.llm.types import StreamEvent

pytestmark = pytest.mark.textual_integration


@pytest.fixture
def make_icoder_app(event_log: EventLog) -> Callable[..., ICoderApp]:
    """Factory to create ICoderApp with custom FakeLLM responses."""

    def _factory(
        *,
        responses: list[list[StreamEvent]] | None = None,
    ) -> ICoderApp:
        llm = FakeLLMService(responses=responses or [])
        return ICoderApp(AppCore(llm_service=llm, event_log=event_log))

    return _factory


def _write_log(path: Path, events: list[dict[str, object]]) -> None:
    """Write a JSONL log file with the given events."""
    lines = [json.dumps(ev) for ev in events]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


async def test_replay_renders_input_and_llm_text(
    make_icoder_app: Callable[..., ICoderApp],
    tmp_path: Path,
) -> None:
    """Replay shows '> hello' and the LLM text; token widget stays hidden."""
    log_path = tmp_path / "icoder_2026-05-01T10-00-00.jsonl"
    _write_log(
        log_path,
        [
            {"t": 0.0, "event": "session_start", "provider": "claude"},
            {"t": 0.1, "event": "input_received", "text": "hello"},
            {"t": 0.2, "event": "llm_request_start", "text": "hello"},
            {
                "t": 0.3,
                "event": "stream_event",
                "type": "text_delta",
                "text": "hi there",
            },
            {
                "t": 0.4,
                "event": "stream_event",
                "type": "done",
                "usage": {"input_tokens": 100, "output_tokens": 50},
            },
            {"t": 0.5, "event": "llm_request_end"},
        ],
    )
    app = make_icoder_app(responses=[])
    async with app.run_test() as pilot:
        await pilot.pause()
        replay_log(app, log_path)
        await pilot.pause()
        joined = "\n".join(app.query_one(OutputLog).recorded_lines)
        assert "> hello" in joined
        assert "hi there" in joined
        # Token widget remains hidden because replay_mode skips token update.
        assert not app._core.token_usage.has_data


async def test_replay_populates_command_history(
    make_icoder_app: Callable[..., ICoderApp],
    tmp_path: Path,
) -> None:
    """After replay, pressing Up in the input area shows the prior input."""
    log_path = tmp_path / "icoder_2026-05-01T10-00-00.jsonl"
    _write_log(
        log_path,
        [
            {"t": 0.0, "event": "session_start", "provider": "claude"},
            {"t": 0.1, "event": "input_received", "text": "first prompt"},
        ],
    )
    app = make_icoder_app(responses=[])
    async with app.run_test() as pilot:
        await pilot.pause()
        replay_log(app, log_path)
        await pilot.pause()
        input_area = app.query_one(InputArea)
        input_area.focus()
        await pilot.pause()
        await pilot.press("up")
        await pilot.pause()
        assert input_area.text == "first prompt"


async def test_replay_renders_tool_blocks(
    make_icoder_app: Callable[..., ICoderApp],
    tmp_path: Path,
) -> None:
    """Replay of a log with tool_use_start + tool_result renders tool block lines."""
    log_path = tmp_path / "icoder_2026-05-01T10-00-00.jsonl"
    _write_log(
        log_path,
        [
            {"t": 0.0, "event": "session_start", "provider": "claude"},
            {"t": 0.1, "event": "input_received", "text": "list files"},
            {"t": 0.2, "event": "llm_request_start", "text": "list files"},
            {
                "t": 0.3,
                "event": "stream_event",
                "type": "tool_use_start",
                "name": "mcp__mcp-workspace__list_directory",
                "args": {},
            },
            {
                "t": 0.4,
                "event": "stream_event",
                "type": "tool_result",
                "name": "mcp__mcp-workspace__list_directory",
                "output": '{"result": ["file1.py", "file2.py"]}',
            },
            {"t": 0.5, "event": "stream_event", "type": "done"},
            {"t": 0.6, "event": "llm_request_end"},
        ],
    )
    app = make_icoder_app(responses=[])
    async with app.run_test() as pilot:
        await pilot.pause()
        replay_log(app, log_path)
        await pilot.pause()
        joined = "\n".join(app.query_one(OutputLog).recorded_lines)
        assert "file1.py" in joined
        assert "file2.py" in joined
        assert "└ done" in joined


async def test_replay_interrupted_turn_shows_cancelled_marker(
    make_icoder_app: Callable[..., ICoderApp],
    tmp_path: Path,
) -> None:
    """Replay of an interrupted turn (start without end) emits — Cancelled —."""
    log_path = tmp_path / "icoder_2026-05-01T10-00-00.jsonl"
    _write_log(
        log_path,
        [
            {"t": 0.0, "event": "session_start", "provider": "claude"},
            {"t": 0.1, "event": "input_received", "text": "interrupted"},
            {"t": 0.2, "event": "llm_request_start", "text": "interrupted"},
            {
                "t": 0.3,
                "event": "stream_event",
                "type": "text_delta",
                "text": "partial reply",
            },
            # No llm_request_end — turn was cancelled mid-flight.
        ],
    )
    app = make_icoder_app(responses=[])
    async with app.run_test() as pilot:
        await pilot.pause()
        replay_log(app, log_path)
        await pilot.pause()
        joined = "\n".join(app.query_one(OutputLog).recorded_lines)
        assert "— Cancelled —" in joined


async def test_replay_does_not_update_token_usage(
    make_icoder_app: Callable[..., ICoderApp],
    tmp_path: Path,
) -> None:
    """Replay of done event with usage data leaves token_usage.has_data False."""
    log_path = tmp_path / "icoder_2026-05-01T10-00-00.jsonl"
    _write_log(
        log_path,
        [
            {"t": 0.0, "event": "session_start", "provider": "claude"},
            {"t": 0.1, "event": "input_received", "text": "tokens"},
            {"t": 0.2, "event": "llm_request_start", "text": "tokens"},
            {
                "t": 0.3,
                "event": "stream_event",
                "type": "done",
                "usage": {"input_tokens": 999, "output_tokens": 999},
            },
            {"t": 0.4, "event": "llm_request_end"},
        ],
    )
    app = make_icoder_app(responses=[])
    async with app.run_test() as pilot:
        await pilot.pause()
        replay_log(app, log_path)
        await pilot.pause()
        assert not app._core.token_usage.has_data


async def test_replay_empty_log_does_not_raise(
    make_icoder_app: Callable[..., ICoderApp],
    tmp_path: Path,
) -> None:
    """Replay of an empty log file completes without exception."""
    log_path = tmp_path / "icoder_empty.jsonl"
    log_path.write_text("", encoding="utf-8")
    app = make_icoder_app(responses=[])
    async with app.run_test() as pilot:
        await pilot.pause()
        replay_log(app, log_path)
        await pilot.pause()


async def test_replay_log_re_emits_events_when_event_log_supplied(
    make_icoder_app: Callable[..., ICoderApp],
    tmp_path: Path,
) -> None:
    """When `event_log` is supplied, replayed events are re-recorded into it."""
    log_path = tmp_path / "icoder_2026-05-01T10-00-00.jsonl"
    _write_log(
        log_path,
        [
            {"t": 0.0, "event": "session_start", "provider": "claude"},
            {"t": 0.1, "event": "input_received", "text": "hello"},
            {"t": 0.2, "event": "llm_request_start", "text": "hello"},
            {
                "t": 0.3,
                "event": "stream_event",
                "type": "text_delta",
                "text": "hi",
            },
            {"t": 0.4, "event": "stream_event", "type": "done"},
            {"t": 0.5, "event": "llm_request_end"},
        ],
    )
    app = make_icoder_app(responses=[])
    async with app.run_test() as pilot:
        await pilot.pause()
        new_log = app._core.event_log
        replay_log(app, log_path, event_log=new_log)
        await pilot.pause()
        # session_start is NOT re-emitted; everything else is.
        recorded = [e.event for e in new_log.entries]
        assert "session_start" not in recorded
        assert "input_received" in recorded
        assert "llm_request_start" in recorded
        assert "stream_event" in recorded
        assert "llm_request_end" in recorded


async def test_replay_log_no_event_log_does_not_re_emit(
    make_icoder_app: Callable[..., ICoderApp],
    tmp_path: Path,
) -> None:
    """Without `event_log`, the new event log is unaffected by replay."""
    log_path = tmp_path / "icoder_2026-05-01T10-00-00.jsonl"
    _write_log(
        log_path,
        [
            {"t": 0.0, "event": "session_start", "provider": "claude"},
            {"t": 0.1, "event": "input_received", "text": "hello"},
        ],
    )
    app = make_icoder_app(responses=[])
    async with app.run_test() as pilot:
        await pilot.pause()
        new_log = app._core.event_log
        before = len(new_log.entries)
        replay_log(app, log_path)
        await pilot.pause()
        assert len(new_log.entries) == before
