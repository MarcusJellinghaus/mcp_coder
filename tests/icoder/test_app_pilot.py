"""Textual pilot integration tests for ICoderApp."""

from __future__ import annotations

import asyncio
import json
import logging
import queue
import threading
from collections.abc import Callable, Iterator
from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from textual.pilot import Pilot
from textual.widgets import Static

from mcp_coder.icoder.core.app_core import AppCore
from mcp_coder.icoder.core.event_log import EventLog
from mcp_coder.icoder.env_setup import RuntimeInfo
from mcp_coder.icoder.permissions.approval import ApprovalDecision, ApprovalEngine
from mcp_coder.icoder.permissions.model import Matcher, PermissionFrame
from mcp_coder.icoder.permissions.skill_frame import SkillFrame
from mcp_coder.icoder.services.llm_service import FakeLLMService, LLMService
from mcp_coder.icoder.ui.app import ICoderApp
from mcp_coder.icoder.ui.stream_view import _DENY_NO_UI
from mcp_coder.icoder.ui.widgets.busy_indicator import BusyIndicator
from mcp_coder.icoder.ui.widgets.detail_modal import DetailModal
from mcp_coder.icoder.ui.widgets.input_area import InputArea
from mcp_coder.icoder.ui.widgets.output_log import ContentUnit, OutputLog
from mcp_coder.llm.types import StreamEvent
from mcp_coder.utils.mcp_verification import ClaudeMCPStatus, MCPServerInfo

pytestmark = pytest.mark.textual_integration


@pytest.fixture
def icoder_app(fake_llm: FakeLLMService, event_log: EventLog) -> ICoderApp:
    """Create ICoderApp with fake dependencies."""
    app_core = AppCore(llm_service=fake_llm, event_log=event_log)
    return ICoderApp(app_core)


@pytest.fixture
def make_icoder_app(
    event_log: EventLog,
) -> Callable[..., ICoderApp]:
    """Factory to create ICoderApp with custom FakeLLM responses or a custom LLM service."""

    def _factory(
        *,
        responses: list[list[StreamEvent]] | None = None,
        llm_service: LLMService | None = None,
        format_tools: bool = True,
    ) -> ICoderApp:
        llm = llm_service or FakeLLMService(responses=responses or [])
        return ICoderApp(
            AppCore(llm_service=llm, event_log=event_log),
            format_tools=format_tools,
        )

    return _factory


async def test_app_launches(icoder_app: ICoderApp) -> None:
    """App launches without error."""
    async with icoder_app.run_test():
        assert icoder_app.is_running


async def test_input_focused_on_startup(icoder_app: ICoderApp) -> None:
    """Input area is focused on startup."""
    async with icoder_app.run_test() as pilot:
        await pilot.pause()
        focused = icoder_app.focused
        assert isinstance(focused, InputArea)


async def test_layout_structure(icoder_app: ICoderApp) -> None:
    """Output area is above input area."""
    async with icoder_app.run_test() as pilot:
        await pilot.pause()
        output = icoder_app.query_one(OutputLog)
        input_area = icoder_app.query_one(InputArea)
        assert output.region.y < input_area.region.y


async def test_submit_text(icoder_app: ICoderApp) -> None:
    """Typed text + Enter echoes to output and clears input."""
    async with icoder_app.run_test() as pilot:
        input_area = icoder_app.query_one(InputArea)
        input_area.focus()
        await pilot.pause()
        input_area.insert("hello world")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        output = icoder_app.query_one(OutputLog)
        assert "> hello world" in output.recorded_lines
        assert input_area.text == ""


async def test_clear_command(icoder_app: ICoderApp) -> None:
    """/clear command clears the output log."""
    async with icoder_app.run_test() as pilot:
        input_area = icoder_app.query_one(InputArea)
        input_area.focus()
        await pilot.pause()
        # First send /help to get some output
        input_area.insert("/help")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        # Then clear
        input_area.insert("/clear")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        output = icoder_app.query_one(OutputLog)
        assert len(output.recorded_lines) == 0


async def test_quit_command(icoder_app: ICoderApp) -> None:
    """/quit command exits the app."""
    async with icoder_app.run_test() as pilot:
        input_area = icoder_app.query_one(InputArea)
        input_area.focus()
        await pilot.pause()
        input_area.insert("/quit")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
    assert not icoder_app.is_running


async def test_shift_enter_newline(icoder_app: ICoderApp) -> None:
    """Shift-Enter inserts newline without submitting."""
    async with icoder_app.run_test() as pilot:
        input_area = icoder_app.query_one(InputArea)
        input_area.focus()
        await pilot.pause()
        input_area.insert("line1")
        await pilot.pause()
        await pilot.press("shift+enter")
        await pilot.pause()
        input_area.insert("line2")
        await pilot.pause()
        assert "\n" in input_area.text


async def test_llm_streaming(icoder_app: ICoderApp) -> None:
    """LLM streaming response appears in output."""
    async with icoder_app.run_test() as pilot:
        input_area = icoder_app.query_one(InputArea)
        input_area.focus()
        await pilot.pause()
        input_area.insert("hello")
        await pilot.pause()
        await pilot.press("enter")
        # Give worker thread time to run
        await pilot.pause(delay=0.5)
        output = icoder_app.query_one(OutputLog)
        assert "fake response" in output.recorded_lines


# --- Streaming buffer regression tests (a–e + edge cases) ---


async def _submit_and_wait(
    app: ICoderApp, pilot: Pilot[Any], text: str = "test"
) -> None:
    """Helper: focus input, type text, press enter, wait for worker."""
    input_area = app.query_one(InputArea)
    input_area.focus()
    await pilot.pause()
    input_area.insert(text)
    await pilot.press("enter")
    await pilot.pause(delay=0.5)


async def test_streaming_single_chunk_no_newline(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """(a) Single chunk without newline: buffered, flushed to RichLog on stream end."""
    app = make_icoder_app(
        responses=[
            [
                {"type": "text_delta", "text": "hello"},
                {"type": "done"},
            ]
        ]
    )
    async with app.run_test() as pilot:
        await _submit_and_wait(app, pilot)
        output = app.query_one(OutputLog)
        assert output.recorded_lines.count("hello") == 1
        assert app._text_buffer == ""


async def test_model_stream_slash_text_never_dispatches(
    icoder_app: ICoderApp,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Model /skill-shaped text driven through the render path renders as
    plain text and never reaches registry.dispatch.

    Drives ICoderApp._handle_stream_event directly — the same entry ui/replay.py
    uses — so no human input is involved. The registry spy is a supporting
    check (the render path never references the registry); the load-bearing
    guarantee is the single-call-site test in test_self_invocation_guard.py.
    """
    app = icoder_app
    async with app.run_test() as pilot:
        spy = MagicMock(wraps=app._core.registry.dispatch)
        monkeypatch.setattr(app._core.registry, "dispatch", spy)

        app._handle_stream_event({"type": "text_delta", "text": "/issue_update 5"})
        app._handle_stream_event({"type": "done"})
        await pilot.pause()

        spy.assert_not_called()
        output = app.query_one(OutputLog)
        assert output.recorded_lines.count("/issue_update 5") == 1


async def test_streaming_multi_chunk_no_newlines(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """(b) Multiple chunks without newlines: combined into single line on flush."""
    app = make_icoder_app(
        responses=[
            [
                {"type": "text_delta", "text": "hello"},
                {"type": "text_delta", "text": " world"},
                {"type": "text_delta", "text": "!"},
                {"type": "done"},
            ]
        ]
    )
    async with app.run_test() as pilot:
        await _submit_and_wait(app, pilot)
        output = app.query_one(OutputLog)
        assert output.recorded_lines.count("hello world!") == 1
        assert app._text_buffer == ""


async def test_streaming_mid_newline(make_icoder_app: Callable[..., ICoderApp]) -> None:
    """(c) Newline mid-stream flushes completed line, partial continues."""
    app = make_icoder_app(
        responses=[
            [
                {"type": "text_delta", "text": "line1\nline2"},
                {"type": "done"},
            ]
        ]
    )
    async with app.run_test() as pilot:
        await _submit_and_wait(app, pilot)
        output = app.query_one(OutputLog)
        assert output.recorded_lines.count("line1") == 1
        assert output.recorded_lines.count("line2") == 1
        assert output.recorded_lines.index("line1") < output.recorded_lines.index(
            "line2"
        )
        assert app._text_buffer == ""


async def test_streaming_multiple_newlines_in_chunk(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """(d) Chunk with multiple newlines: each complete line flushed, partial kept."""
    app = make_icoder_app(
        responses=[
            [
                {"type": "text_delta", "text": "line1\nline2\nline3"},
                {"type": "done"},
            ]
        ]
    )
    async with app.run_test() as pilot:
        await _submit_and_wait(app, pilot)
        output = app.query_one(OutputLog)
        for ln in ("line1", "line2", "line3"):
            assert output.recorded_lines.count(ln) == 1
        idx1 = output.recorded_lines.index("line1")
        idx2 = output.recorded_lines.index("line2")
        idx3 = output.recorded_lines.index("line3")
        assert idx1 < idx2 < idx3
        assert app._text_buffer == ""


async def test_streaming_empty_text_delta(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """(e) Empty text_delta is a no-op: no spurious empty lines."""
    app = make_icoder_app(
        responses=[
            [
                {"type": "text_delta", "text": "hello"},
                {"type": "text_delta", "text": ""},
                {"type": "text_delta", "text": " world"},
                {"type": "done"},
            ]
        ]
    )
    async with app.run_test() as pilot:
        await _submit_and_wait(app, pilot)
        output = app.query_one(OutputLog)
        assert output.recorded_lines.count("hello world") == 1
        assert app._text_buffer == ""


async def test_streaming_chunk_ends_on_newline(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """(e2) Chunk ending exactly on newline: line flushed, no trailing empty entry."""
    app = make_icoder_app(
        responses=[
            [
                {"type": "text_delta", "text": "line1\n"},
                {"type": "done"},
            ]
        ]
    )
    async with app.run_test() as pilot:
        await _submit_and_wait(app, pilot)
        output = app.query_one(OutputLog)
        assert output.recorded_lines.count("line1") == 1
        assert app._text_buffer == ""


async def test_streaming_newline_only_chunk(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """(e3) Chunks ['hello', '\\n', 'world']: hello flushes on newline, world on done."""
    app = make_icoder_app(
        responses=[
            [
                {"type": "text_delta", "text": "hello"},
                {"type": "text_delta", "text": "\n"},
                {"type": "text_delta", "text": "world"},
                {"type": "done"},
            ]
        ]
    )
    async with app.run_test() as pilot:
        await _submit_and_wait(app, pilot)
        output = app.query_one(OutputLog)
        assert output.recorded_lines.count("hello") == 1
        assert output.recorded_lines.count("world") == 1
        assert output.recorded_lines.index("hello") < output.recorded_lines.index(
            "world"
        )
        assert app._text_buffer == ""


async def test_streaming_tail_shows_partial_during_stream(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """(e4) Static tail holds partial line during streaming."""
    app = make_icoder_app(
        responses=[
            [
                {"type": "text_delta", "text": "partial"},
                {"type": "done"},
            ]
        ]
    )
    async with app.run_test() as pilot:
        # Drive _handle_stream_event directly for deterministic mid-stream check
        app.query_one(InputArea).focus()
        await pilot.pause()

        # Simulate a single text chunk without StreamDone
        app._handle_stream_event({"type": "text_delta", "text": "partial"})
        await pilot.pause()
        assert app._text_buffer == "partial"

        # Now deliver StreamDone — tail should clear
        app._handle_stream_event({"type": "done"})
        await pilot.pause()
        assert app._text_buffer == ""


# --- Streaming edge-case regression tests (f–h) ---


class ErrorAfterChunksLLMService:
    """LLM service that yields some chunks then raises."""

    def __init__(self, chunks: list[StreamEvent], error_msg: str) -> None:
        self._chunks = chunks
        self._error_msg = error_msg

    def stream(
        self, question: str, *, frame: PermissionFrame | None = None
    ) -> Iterator[StreamEvent]:
        """Yield chunks then raise RuntimeError."""
        yield from self._chunks
        raise RuntimeError(self._error_msg)

    @property
    def provider(self) -> str:
        """Provider name."""
        return "claude"

    @property
    def session_id(self) -> str | None:
        """No session tracking."""
        return None

    def reset_session(self) -> None:
        """No-op."""


async def test_streaming_error_mid_line(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """(f) Stream error mid-line: partial text flushed before error message."""
    app = make_icoder_app(
        llm_service=ErrorAfterChunksLLMService(
            chunks=[{"type": "text_delta", "text": "partial"}],
            error_msg="boom",
        ),
    )
    async with app.run_test() as pilot:
        await _submit_and_wait(app, pilot)
        output = app.query_one(OutputLog)
        lines = output.recorded_lines
        assert "partial" in lines
        error_lines = [ln for ln in lines if ln.startswith("Error:")]
        assert any("boom" in ln for ln in error_lines)
        partial_idx = lines.index("partial")
        error_idx = next(i for i, ln in enumerate(lines) if ln.startswith("Error:"))
        assert partial_idx < error_idx


async def test_streaming_back_to_back_no_leakage(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """(g) Back-to-back streams: buffer resets, no text leaks between streams."""
    app = make_icoder_app(
        responses=[
            [
                {"type": "text_delta", "text": "first"},
                {"type": "done"},
            ],
            [
                {"type": "text_delta", "text": "second"},
                {"type": "done"},
            ],
        ],
    )
    async with app.run_test() as pilot:
        await _submit_and_wait(app, pilot, text="msg1")
        await _submit_and_wait(app, pilot, text="msg2")
        output = app.query_one(OutputLog)
        lines = output.recorded_lines
        assert "first" in lines
        assert "second" in lines
        # No concatenation leak
        assert "firstsecond" not in lines
        assert app._text_buffer == ""


async def test_streaming_tool_event_mid_line(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """(h) Tool event mid-line: partial text flushed before tool block."""
    app = make_icoder_app(
        responses=[
            [
                {"type": "text_delta", "text": "before tool"},
                {
                    "type": "tool_use_start",
                    "name": "mcp__mcp-workspace__read_file",
                    "args": {"file_path": "x.py"},
                },
                {
                    "type": "tool_result",
                    "name": "mcp__mcp-workspace__read_file",
                    "output": "content",
                },
                {"type": "text_delta", "text": "after tool"},
                {"type": "done"},
            ]
        ],
    )
    async with app.run_test() as pilot:
        await _submit_and_wait(app, pilot)
        output = app.query_one(OutputLog)
        lines = output.recorded_lines
        assert "before tool" in lines
        assert "after tool" in lines
        # Find tool start line (contains the "┌" prefix)
        tool_start_lines = [i for i, ln in enumerate(lines) if "┌" in ln]
        assert len(tool_start_lines) >= 1
        before_idx = lines.index("before tool")
        assert before_idx < tool_start_lines[0]
        after_idx = lines.index("after tool")
        assert tool_start_lines[0] < after_idx
        assert app._text_buffer == ""


async def test_tui_renders_runtime_info_on_mount(
    fake_llm: FakeLLMService, event_log: EventLog
) -> None:
    """TUI output log shows runtime info on mount when RuntimeInfo is provided."""
    info = RuntimeInfo(
        mcp_coder_version="0.42.0",
        mcp_coder_utils_version="0.42.0",
        python_version="3.12.0",
        claude_code_version="1.2.3",
        tool_env_path="/fake/tool",
        project_venv_path="/fake/proj/.venv",
        project_dir="/fake/proj",
        env_vars={"MCP_CODER_VENV_PATH": "/fake/bin"},
        mcp_servers=[
            MCPServerInfo(
                name="mcp-tools-py",
                path=Path("/fake/mcp-tools-py"),
                version="1.0",
            ),
        ],
    )
    app_core = AppCore(llm_service=fake_llm, event_log=event_log, runtime_info=info)
    app = ICoderApp(app_core)

    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one(OutputLog)
        recorded = output.recorded_lines
        assert len(recorded) >= 1
        text = recorded[0]
        assert "mcp-coder 0.42.0" in text
        assert "mcp-tools-py 1.0" in text
        assert "Tool env:" in text
        assert "Project env:" in text
        assert "Project dir:" in text


async def test_on_mount_shows_connection_status(
    fake_llm: FakeLLMService, event_log: EventLog
) -> None:
    """on_mount() renders inline connection status when mcp_connection_status is set."""
    info = RuntimeInfo(
        mcp_coder_version="0.42.0",
        mcp_coder_utils_version="0.42.0",
        python_version="3.12.0",
        claude_code_version="1.2.3",
        tool_env_path="/fake/tool",
        project_venv_path="/fake/proj/.venv",
        project_dir="/fake/proj",
        env_vars={"MCP_CODER_VENV_PATH": "/fake/bin"},
        mcp_servers=[
            MCPServerInfo(
                name="mcp-tools-py",
                path=Path("/fake/mcp-tools-py"),
                version="1.0",
            ),
        ],
        mcp_connection_status=[
            ClaudeMCPStatus(name="mcp-tools-py", status_text="Connected", ok=True),
        ],
    )
    app_core = AppCore(llm_service=fake_llm, event_log=event_log, runtime_info=info)
    app = ICoderApp(app_core)

    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one(OutputLog)
        text = output.recorded_lines[0]
        assert "\u2713 Connected" in text
        assert "mcp-tools-py 1.0" in text


async def test_on_mount_no_connection_status_falls_back(
    fake_llm: FakeLLMService, event_log: EventLog
) -> None:
    """on_mount() with mcp_connection_status=None shows version-only (no crash)."""
    info = RuntimeInfo(
        mcp_coder_version="0.42.0",
        mcp_coder_utils_version="0.42.0",
        python_version="3.12.0",
        claude_code_version="1.2.3",
        tool_env_path="/fake/tool",
        project_venv_path="/fake/proj/.venv",
        project_dir="/fake/proj",
        env_vars={"MCP_CODER_VENV_PATH": "/fake/bin"},
        mcp_servers=[
            MCPServerInfo(
                name="mcp-tools-py",
                path=Path("/fake/mcp-tools-py"),
                version="1.0",
            ),
        ],
        mcp_connection_status=None,
    )
    app_core = AppCore(llm_service=fake_llm, event_log=event_log, runtime_info=info)
    app = ICoderApp(app_core)

    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one(OutputLog)
        text = output.recorded_lines[0]
        assert "mcp-tools-py 1.0" in text
        assert "\u2713" not in text
        assert "\u2717" not in text


# --- Status bar widget tests ---


async def test_status_bar_visible_on_startup(icoder_app: ICoderApp) -> None:
    """Status bar is visible with all three zones on startup."""
    async with icoder_app.run_test() as pilot:
        await pilot.pause()
        tokens = icoder_app.query_one("#status-tokens", Static)
        version = icoder_app.query_one("#status-version", Static)
        hint = icoder_app.query_one("#status-hint", Static)
        assert not tokens.has_class("hidden")
        assert version is not None
        assert hint is not None


async def test_status_bar_always_visible_when_typing(icoder_app: ICoderApp) -> None:
    """Status bar stays visible when input area has text (no hide-on-type)."""
    async with icoder_app.run_test() as pilot:
        input_area = icoder_app.query_one(InputArea)
        input_area.focus()
        await pilot.pause()
        input_area.insert("some text")
        await pilot.pause()
        hint = icoder_app.query_one("#status-hint", Static)
        version = icoder_app.query_one("#status-version", Static)
        assert hint is not None
        assert version is not None


async def test_token_display_updates_after_stream_with_usage(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """After stream with usage data, #status-tokens shows formatted counts."""
    app = make_icoder_app(
        responses=[
            [
                {"type": "text_delta", "text": "hello"},
                {
                    "type": "done",
                    "usage": {"input_tokens": 1200, "output_tokens": 800},
                },
            ]
        ]
    )
    async with app.run_test() as pilot:
        await _submit_and_wait(app, pilot)
        token_widget = app.query_one("#status-tokens", Static)
        # Use update() content via _content (internal) or render to string
        rendered = token_widget.render()
        text = str(rendered)
        assert "\u21931.2k" in text
        assert "\u2191800" in text
        assert not token_widget.has_class("hidden")


async def test_token_display_hidden_after_stream_without_usage(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """After stream without usage data, #status-tokens is hidden."""
    app = make_icoder_app(
        responses=[
            [
                {"type": "text_delta", "text": "hello"},
                {"type": "done"},
            ]
        ]
    )
    async with app.run_test() as pilot:
        await _submit_and_wait(app, pilot)
        token_widget = app.query_one("#status-tokens", Static)
        assert token_widget.has_class("hidden")


# --- BusyIndicator integration tests ---


async def test_busy_indicator_shows_ready_on_startup(icoder_app: ICoderApp) -> None:
    """After mount, BusyIndicator renderable contains '✓ Ready'."""
    async with icoder_app.run_test() as pilot:
        await pilot.pause()
        indicator = icoder_app.query_one(BusyIndicator)
        assert "✓ Ready" in indicator.label_text


async def test_busy_indicator_shows_ready_after_streaming(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """After a full stream (text + done), indicator is back to '✓ Ready'."""
    app = make_icoder_app(
        responses=[
            [
                {"type": "text_delta", "text": "hello"},
                {"type": "done"},
            ]
        ]
    )
    async with app.run_test() as pilot:
        await _submit_and_wait(app, pilot)
        indicator = app.query_one(BusyIndicator)
        assert "✓ Ready" in indicator.label_text


async def test_busy_indicator_shows_tool_name_during_tool_use(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """Directly call _handle_stream_event with tool_use_start, verify indicator shows tool display name."""
    app = make_icoder_app(responses=[])
    async with app.run_test() as pilot:
        await pilot.pause()
        app._handle_stream_event(
            {
                "type": "tool_use_start",
                "name": "mcp__mcp-workspace__read_file",
                "args": {"file_path": "x.py"},
            }
        )
        await pilot.pause()
        indicator = app.query_one(BusyIndicator)
        assert "workspace" in indicator.label_text
        assert "read_file" in indicator.label_text


async def test_busy_indicator_resets_on_stream_error(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """Use ErrorAfterChunksLLMService, verify indicator returns to '✓ Ready' after error."""
    app = make_icoder_app(
        llm_service=ErrorAfterChunksLLMService(
            chunks=[{"type": "text_delta", "text": "partial"}],
            error_msg="boom",
        ),
    )
    async with app.run_test() as pilot:
        await _submit_and_wait(app, pilot)
        indicator = app.query_one(BusyIndicator)
        assert "✓ Ready" in indicator.label_text


# --- Plain text rendering tests (Step 3) ---


async def test_tool_result_renders_plain_text_by_default(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """Tool result output is rendered as plain text when format_tools=True (default)."""
    app = make_icoder_app(
        responses=[
            [
                {
                    "type": "tool_use_start",
                    "name": "mcp__mcp-workspace__read_file",
                    "args": {"file_path": "x.py"},
                },
                {
                    "type": "tool_result",
                    "name": "mcp__mcp-workspace__read_file",
                    "output": "# Header\n**bold text**",
                },
                {"type": "done"},
            ]
        ],
    )
    async with app.run_test() as pilot:
        await _submit_and_wait(app, pilot)
        output = app.query_one(OutputLog)
        # Tool start line is append-history; the result body lands on the
        # rendered screen state once update_unit_and_rerender fires.
        assert any("┌" in ln for ln in output.recorded_lines)
        lines = output.rendered_lines
        result_lines = [ln for ln in lines if "done" in ln]
        assert len(result_lines) >= 1
        joined = "\n".join(lines)
        assert "│" in joined, "Rendered content should contain box-drawing body lines"
        assert "# Header" in joined, "Tool output body should be rendered"


# --- Cancel / Escape key tests ---


class SlowLLMService:
    """LLM service that yields events with delays to simulate streaming."""

    def stream(
        self, question: str, *, frame: PermissionFrame | None = None
    ) -> Iterator[StreamEvent]:
        import time

        for i in range(20):
            time.sleep(0.05)
            yield {"type": "text_delta", "text": f"chunk{i} "}
        yield {"type": "done"}

    @property
    def provider(self) -> str:
        return "claude"

    @property
    def session_id(self) -> str | None:
        return None

    def reset_session(self) -> None:
        pass


async def test_escape_cancels_streaming(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """Escape during streaming breaks the loop and shows cancelled marker."""
    app = make_icoder_app(llm_service=SlowLLMService())
    async with app.run_test() as pilot:
        await _submit_and_wait(app, pilot, text="hello")
        await pilot.press("escape")
        await pilot.pause(delay=0.5)
        output = app.query_one(OutputLog)
        assert "\u2014 Cancelled \u2014" in output.recorded_lines


async def test_escape_when_idle_is_noop(icoder_app: ICoderApp) -> None:
    """Escape when not streaming does nothing harmful."""
    async with icoder_app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
        output = icoder_app.query_one(OutputLog)
        assert "\u2014 Cancelled \u2014" not in output.recorded_lines


async def test_busy_indicator_resets_after_cancel(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """After Escape cancel, busy indicator shows 'Ready'."""
    app = make_icoder_app(llm_service=SlowLLMService())
    async with app.run_test() as pilot:
        await _submit_and_wait(app, pilot, text="hello")
        await pilot.press("escape")
        await pilot.pause(delay=0.5)
        indicator = app.query_one(BusyIndicator)
        assert "\u2713 Ready" in indicator.label_text


async def test_session_preserved_after_cancel(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """Cancel doesn't reset session -- previous session ID persists."""

    class SlowLLMServiceWithSession:
        def __init__(self) -> None:
            self._session_id: str | None = "test-session-123"

        def stream(
            self, question: str, *, frame: PermissionFrame | None = None
        ) -> Iterator[StreamEvent]:
            import time

            for i in range(20):
                time.sleep(0.05)
                yield {"type": "text_delta", "text": f"chunk{i} "}
            yield {"type": "done"}

        @property
        def provider(self) -> str:
            return "claude"

        @property
        def session_id(self) -> str | None:
            return self._session_id

        def reset_session(self) -> None:
            self._session_id = None

    svc = SlowLLMServiceWithSession()
    app = make_icoder_app(llm_service=svc)
    async with app.run_test() as pilot:
        await _submit_and_wait(app, pilot, text="hello")
        await pilot.press("escape")
        await pilot.pause(delay=0.5)
        assert svc.session_id == "test-session-123"


async def test_ctrl_c_does_not_quit(icoder_app: ICoderApp) -> None:
    """Ctrl+C should not trigger the quit confirmation dialog."""
    async with icoder_app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("ctrl+c")
        await pilot.pause()
        assert icoder_app.is_running
        assert len(icoder_app._notifications) == 0


async def test_tool_result_renders_plain_text_when_no_format(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """Tool result output is rendered as plain text when format_tools=False."""
    app = make_icoder_app(
        responses=[
            [
                {
                    "type": "tool_use_start",
                    "name": "mcp__mcp-workspace__read_file",
                    "args": {"file_path": "x.py"},
                },
                {
                    "type": "tool_result",
                    "name": "mcp__mcp-workspace__read_file",
                    "output": "# Header\n**bold text**",
                },
                {"type": "done"},
            ]
        ],
        format_tools=False,
    )
    async with app.run_test() as pilot:
        await _submit_and_wait(app, pilot)
        output = app.query_one(OutputLog)
        # With format_tools=False, the raw body renders verbatim onto the
        # screen state (rendered_lines) after the tool result arrives.
        lines = output.rendered_lines
        result_lines = [ln for ln in lines if "│" in ln]
        assert len(result_lines) >= 1
        joined = "\n".join(lines)
        assert "# Header" in joined
        assert "**bold text**" in joined


async def test_chat_txt_mirrors_visible_conversation(
    icoder_app: ICoderApp, event_log: EventLog
) -> None:
    """End-to-end: user + assistant lines land in the paired _chat.txt sidecar."""
    async with icoder_app.run_test() as pilot:
        input_area = icoder_app.query_one(InputArea)
        input_area.focus()
        await pilot.pause()
        input_area.insert("hello")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause(delay=0.5)
    chat_text = event_log.current_chat_path.read_text(encoding="utf-8")
    assert "> hello" in chat_text
    assert chat_text.index("> hello") < chat_text.index("\n\n")
    assert "fake response" in chat_text


def _make_click_tool_unit(
    unit_id: str = "A",
    *,
    output_lines: tuple[str, ...] = (),
    total_lines: int = 0,
) -> ContentUnit:
    """Build a tool ContentUnit for click / F2 pilot tests."""
    return ContentUnit(
        id=unit_id,
        kind="tool",
        timestamp=datetime(2026, 6, 24, 12, 0, 0),
        tool_name="read_file",
        args={"path": "src/main.py"},
        output_lines=output_lines,
        total_lines=total_lines,
    )


async def test_f2_with_no_content_is_silent_noop(icoder_app: ICoderApp) -> None:
    """Pressing F2 with no registered units does nothing (no modal, no crash)."""
    async with icoder_app.run_test() as pilot:
        await pilot.pause()

        await pilot.press("f2")
        await pilot.pause()

        assert len(icoder_app.screen_stack) == 1
        assert icoder_app.is_running


async def test_f2_opens_modal_for_last_unit(icoder_app: ICoderApp) -> None:
    """Pressing F2 opens a DetailModal for the most recent unit."""
    async with icoder_app.run_test() as pilot:
        await pilot.pause()
        output = icoder_app.query_one(OutputLog)
        output.append_unit(_make_click_tool_unit("A"), ["line1"])
        await pilot.pause()

        await pilot.press("f2")
        await pilot.pause()

        assert isinstance(icoder_app.screen, DetailModal)


async def test_double_click_emits_content_detail_opened_event(
    icoder_app: ICoderApp, event_log: EventLog
) -> None:
    """A pilot double click on a unit emits content_detail_opened."""
    async with icoder_app.run_test() as pilot:
        await pilot.pause()
        output = icoder_app.query_one(OutputLog)
        output.append_unit(_make_click_tool_unit("A"), ["line1"])
        await pilot.pause()

        await pilot.click(OutputLog, offset=(0, 0), times=2)
        await pilot.pause()

        events = [entry.event for entry in event_log.entries]
        assert "content_detail_opened" in events


async def test_single_click_emits_tool_tier_toggled_event(
    icoder_app: ICoderApp, event_log: EventLog
) -> None:
    """A pilot single click on a tool unit emits tool_tier_toggled after debounce."""
    async with icoder_app.run_test() as pilot:
        await pilot.pause()
        output = icoder_app.query_one(OutputLog)
        output.append_unit(
            _make_click_tool_unit("A", output_lines=("o1",), total_lines=1), ["s"]
        )
        await pilot.pause()

        await pilot.click(OutputLog, offset=(0, 0))
        await pilot.pause(0.6)

        events = [entry.event for entry in event_log.entries]
        assert "tool_tier_toggled" in events


# --- Step 9: append_unit migration (clickable units + orphan cleanup) ---


async def test_user_input_creates_clickable_unit(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """Submitting input registers a clickable user_input unit at its line."""
    app = make_icoder_app(responses=[[{"type": "done"}]])
    async with app.run_test() as pilot:
        await _submit_and_wait(app, pilot, text="hello there")
        output = app.query_one(OutputLog)
        unit = output.unit_at_line(0)
        assert unit is not None
        assert unit.kind == "user_input"
        assert unit.full_text == "hello there"


async def test_tool_block_creates_clickable_unit(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """A ToolStart + ToolResult pair becomes a single clickable tool unit."""
    app = make_icoder_app(responses=[])
    async with app.run_test() as pilot:
        await pilot.pause()
        app._handle_stream_event(
            {
                "type": "tool_use_start",
                "name": "mcp__mcp-workspace__read_file",
                "args": {"file_path": "x.py"},
            }
        )
        app._handle_stream_event(
            {
                "type": "tool_result",
                "name": "mcp__mcp-workspace__read_file",
                "output": "line1\nline2",
            }
        )
        await pilot.pause()
        output = app.query_one(OutputLog)
        tool_units = [u for u in output._units.values() if u.kind == "tool"]
        assert len(tool_units) == 1
        assert tool_units[0].output == "line1\nline2"
        # Every rendered line of the block resolves to the one tool unit.
        resolved_ids: set[str] = set()
        for i in range(len(output.rendered_lines)):
            resolved = output.unit_at_line(i)
            if resolved is not None:
                resolved_ids.add(resolved.id)
        assert resolved_ids == {tool_units[0].id}


async def test_assistant_text_creates_clickable_turn(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """Streamed assistant text registers a single clickable turn unit."""
    app = make_icoder_app(responses=[])
    async with app.run_test() as pilot:
        await pilot.pause()
        app._handle_stream_event({"type": "text_delta", "text": "hello\nworld\n"})
        app._handle_stream_event({"type": "done"})
        await pilot.pause()
        output = app.query_one(OutputLog)
        turn_units = [u for u in output._units.values() if u.kind == "assistant_turn"]
        assert len(turn_units) == 1
        assert output.unit_at_line(0) is turn_units[0]
        assert "hello" in output.rendered_lines
        assert "world" in output.rendered_lines


async def test_last_unit_returns_most_recent_inserted_unit_dict_order(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """A mid-turn tool becomes last_unit; later turn text does not change it."""
    app = make_icoder_app(responses=[])
    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one(OutputLog)
        app._handle_stream_event({"type": "text_delta", "text": "before\n"})
        app._handle_stream_event(
            {
                "type": "tool_use_start",
                "name": "mcp__mcp-workspace__read_file",
                "args": {},
            }
        )
        await pilot.pause()
        last = output.last_unit()
        assert last is not None and last.kind == "tool"

        # More turn text arrives, but the tool stays the most-recent unit.
        app._handle_stream_event({"type": "text_delta", "text": "after\n"})
        app._handle_stream_event(
            {
                "type": "tool_result",
                "name": "mcp__mcp-workspace__read_file",
                "output": "out",
            }
        )
        await pilot.pause()
        last = output.last_unit()
        assert last is not None and last.kind == "tool"

        turn_id = next(
            u.id for u in output._units.values() if u.kind == "assistant_turn"
        )
        tool_id = next(u.id for u in output._units.values() if u.kind == "tool")
        turn_ranges = [r for r in output._ranges if r[2] == turn_id]
        tool_ranges = [r for r in output._ranges if r[2] == tool_id]
        assert len(turn_ranges) >= 2
        assert len(tool_ranges) == 1
        # The tool range sits between the turn's range entries.
        assert turn_ranges[0][0] < tool_ranges[0][0] < turn_ranges[-1][0]


async def test_cancel_synthesizes_cancelled_tool_unit(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """An orphaned tool start resolves to a cancelled tool unit."""
    app = make_icoder_app(responses=[])
    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one(OutputLog)
        app._handle_stream_event(
            {
                "type": "tool_use_start",
                "name": "mcp__mcp-workspace__read_file",
                "args": {"file_path": "x.py"},
            }
        )
        await pilot.pause()

        # Simulate the cancel-path orphan cleanup.
        app._cleanup_orphan_tools()
        await pilot.pause()

        tool = next(u for u in output._units.values() if u.kind == "tool")
        assert tool.output == "(cancelled)"
        assert tool.is_error is True
        assert tool.duration_ms is None
        assert any("(cancelled)" in ln for ln in output.rendered_lines)


async def test_same_tool_out_of_order_results_pair_by_run_id(
    make_icoder_app: Callable[..., ICoderApp],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Two calls to the same tool pair by tool_run_id, not by arrival order."""
    app = make_icoder_app(responses=[])
    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one(OutputLog)
        app._handle_stream_event(
            {
                "type": "tool_use_start",
                "name": "mcp__mcp-workspace__read_file",
                "args": {"file_path": "a.py"},
                "tool_run_id": "run-a",
            }
        )
        app._handle_stream_event(
            {
                "type": "tool_use_start",
                "name": "mcp__mcp-workspace__read_file",
                "args": {"file_path": "b.py"},
                "tool_run_id": "run-b",
            }
        )
        with caplog.at_level(logging.WARNING):
            # The gated call (a) resolves *after* the ungated one (b).
            app._handle_stream_event(
                {
                    "type": "tool_result",
                    "name": "mcp__mcp-workspace__read_file",
                    "output": "b output",
                    "tool_run_id": "run-b",
                }
            )
            app._handle_stream_event(
                {
                    "type": "tool_result",
                    "name": "mcp__mcp-workspace__read_file",
                    "output": "a output",
                    "tool_run_id": "run-a",
                }
            )
        await pilot.pause()

        tool_units = [u for u in output._units.values() if u.kind == "tool"]
        assert len(tool_units) == 2
        by_arg = {(u.args or {})["file_path"]: u for u in tool_units}
        assert by_arg["a.py"].output == "a output"
        assert by_arg["b.py"].output == "b output"
        assert "desync" not in caplog.text


async def test_cancel_resolves_the_open_same_name_unit(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """Orphan cleanup cancels the still-open unit, not the completed one."""
    app = make_icoder_app(responses=[])
    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one(OutputLog)
        app._handle_stream_event(
            {
                "type": "tool_use_start",
                "name": "mcp__mcp-workspace__read_file",
                "args": {"file_path": "a.py"},
                "tool_run_id": "run-a",
            }
        )
        app._handle_stream_event(
            {
                "type": "tool_use_start",
                "name": "mcp__mcp-workspace__read_file",
                "args": {"file_path": "b.py"},
                "tool_run_id": "run-b",
            }
        )
        app._handle_stream_event(
            {
                "type": "tool_result",
                "name": "mcp__mcp-workspace__read_file",
                "output": "a output",
                "tool_run_id": "run-a",
            }
        )
        await pilot.pause()

        # Cancel while the second (same-name) call is still open.
        app._cleanup_orphan_tools()
        await pilot.pause()

        by_arg = {
            (u.args or {})["file_path"]: u
            for u in output._units.values()
            if u.kind == "tool"
        }
        assert by_arg["a.py"].output == "a output"
        assert by_arg["a.py"].is_error is False
        assert by_arg["b.py"].output == "(cancelled)"
        assert by_arg["b.py"].is_error is True


async def test_stream_done_clears_renderer_fifo(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """After StreamDone, the renderer FIFO is empty (cleanup_pending → [])."""
    app = make_icoder_app(responses=[])
    async with app.run_test() as pilot:
        await pilot.pause()
        app._handle_stream_event(
            {
                "type": "tool_use_start",
                "name": "mcp__mcp-workspace__read_file",
                "args": {},
            }
        )
        app._handle_stream_event(
            {
                "type": "tool_result",
                "name": "mcp__mcp-workspace__read_file",
                "output": "o",
            }
        )
        app._handle_stream_event({"type": "done"})
        await pilot.pause()

        assert app._renderer.cleanup_pending() == []


async def test_banner_stays_on_append_text(
    fake_llm: FakeLLMService, event_log: EventLog
) -> None:
    """The startup banner is recorded but registers no clickable unit."""
    info = RuntimeInfo(
        mcp_coder_version="0.42.0",
        mcp_coder_utils_version="0.42.0",
        python_version="3.12.0",
        claude_code_version="1.2.3",
        tool_env_path="/fake/tool",
        project_venv_path="/fake/proj/.venv",
        project_dir="/fake/proj",
        env_vars={},
        mcp_servers=[
            MCPServerInfo(
                name="mcp-tools-py",
                path=Path("/fake/mcp-tools-py"),
                version="1.0",
            ),
        ],
    )
    app = ICoderApp(
        AppCore(llm_service=fake_llm, event_log=event_log, runtime_info=info)
    )
    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one(OutputLog)
        assert any("mcp-coder" in ln for ln in output.recorded_lines)
        # Banner lines are not part of the clickable registry.
        assert output.unit_at_line(0) is None
        assert output._units == {}


async def test_display_oneline_rebuilds_all_tool_units_as_oneline(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """/display oneline rebuilds existing tool blocks as tier-1 oneline."""
    from mcp_coder.icoder.core.commands.display import register_display

    app = make_icoder_app(responses=[])
    async with app.run_test() as pilot:
        register_display(app._core.registry, app._core)
        await pilot.pause()
        app._handle_stream_event(
            {
                "type": "tool_use_start",
                "name": "mcp__mcp-workspace__read_file",
                "args": {"file_path": "x.py"},
            }
        )
        app._handle_stream_event(
            {
                "type": "tool_result",
                "name": "mcp__mcp-workspace__read_file",
                "output": "line1\nline2",
            }
        )
        await pilot.pause()
        output = app.query_one(OutputLog)
        # Default tier is compressed → box-drawing header present.
        assert any("┌" in ln for ln in output.rendered_lines)

        input_area = app.query_one(InputArea)
        input_area.focus()
        await pilot.pause()
        input_area.insert("/display oneline")
        await pilot.press("enter")
        await pilot.pause()

        lines = output.rendered_lines
        # Tool now renders as a single tier-1 gear summary, no box chars.
        assert any("⚙" in ln for ln in lines)
        assert not any("┌" in ln for ln in lines)


async def test_display_compressed_wipes_per_unit_overrides(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """/display compressed discards a manual per-tool oneline override."""
    from mcp_coder.icoder.core.commands.display import register_display

    app = make_icoder_app(responses=[])
    async with app.run_test() as pilot:
        register_display(app._core.registry, app._core)
        await pilot.pause()
        app._handle_stream_event(
            {
                "type": "tool_use_start",
                "name": "mcp__mcp-workspace__read_file",
                "args": {"file_path": "x.py"},
            }
        )
        app._handle_stream_event(
            {
                "type": "tool_result",
                "name": "mcp__mcp-workspace__read_file",
                "output": "line1\nline2",
            }
        )
        await pilot.pause()
        output = app.query_one(OutputLog)
        tool = next(u for u in output._units.values() if u.kind == "tool")
        # Manually flip this one tool to oneline.
        output.toggle_unit_tier(tool.id)
        await pilot.pause()
        assert any("⚙" in ln for ln in output.rendered_lines)

        input_area = app.query_one(InputArea)
        input_area.focus()
        await pilot.pause()
        input_area.insert("/display compressed")
        await pilot.press("enter")
        await pilot.pause()

        lines = output.rendered_lines
        # Override wiped → tool back to compressed (box header present).
        assert any("┌" in ln for ln in lines)


async def test_resumed_divider_is_not_a_unit(
    make_icoder_app: Callable[..., ICoderApp],
    tmp_path: Path,
) -> None:
    """The dim 'Resumed' divider written on resume is not a clickable unit."""
    log_path = tmp_path / "icoder_2026-05-01T10-00-00.jsonl"
    events = [
        {"t": 0.0, "event": "session_start", "provider": "claude"},
        {"t": 0.1, "event": "input_received", "text": "prior"},
    ]
    log_path.write_text(
        "\n".join(json.dumps(ev) for ev in events) + "\n", encoding="utf-8"
    )
    app = make_icoder_app(responses=[])
    async with app.run_test() as pilot:
        await pilot.pause()
        app.do_resume(log_path)
        await pilot.pause()
        output = app.query_one(OutputLog)
        # The divider is in the append history and on screen (it survives
        # rebuild), but it is not a clickable unit (no range covers it).
        assert any("Resumed" in ln for ln in output.recorded_lines)
        assert any("Resumed" in ln for ln in output.rendered_lines)
        divider_line = next(
            i for i, ln in enumerate(output.rendered_lines) if "Resumed" in ln
        )
        assert output.unit_at_line(divider_line) is None


# --- Step 3: skill_name threading + permission_warning render ---


async def test_ui_worker_threads_skill_name_to_service(
    event_log: EventLog,
) -> None:
    """Submitting a skill command threads its frame to the LLM service.

    A command yielding ``SendToLLM(text="", skill_name=...)`` must resolve the
    skill's frame from the ``skill_frames`` snapshot and reach
    ``FakeLLMService.last_frame`` via the UI worker.
    """
    from mcp_coder.icoder.core.types import Command, Response, SendToLLM

    fake = FakeLLMService(responses=[[{"type": "done"}]])
    frame = PermissionFrame(base="inherit", allow=(Matcher("srv", "a"),))
    app = ICoderApp(
        AppCore(
            llm_service=fake,
            event_log=event_log,
            skill_frames={"tooled": SkillFrame(frame=frame)},
        )
    )
    app._core.registry.add_command(
        Command(
            name="/tooled",
            description="tooled skill",
            handler=lambda args: Response(
                actions=(SendToLLM(text="", skill_name="tooled"),)
            ),
        )
    )
    async with app.run_test() as pilot:
        await _submit_and_wait(app, pilot, text="/tooled")
        assert fake.last_frame is frame


async def test_permission_warning_event_renders_message_text(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """A permission_warning stream event renders its message in the output log."""
    app = make_icoder_app(responses=[])
    async with app.run_test() as pilot:
        await pilot.pause()
        app._handle_stream_event(
            {"type": "permission_warning", "message": "dropped mcp__srv__*"}
        )
        await pilot.pause()
        output = app.query_one(OutputLog)
        assert "dropped mcp__srv__*" in output.recorded_lines


# --- Step 5: startup permission notices (broken skills + degraded config) ---


async def test_startup_surfaces_both_notice_kinds(
    fake_llm: FakeLLMService, event_log: EventLog
) -> None:
    """Startup renders both a degraded-config line and a broken-skill line (#1061).

    Exercises the on_mount render path (not just the pure formatter + AppCore
    properties). ``runtime_info`` is None here, so the notices appearing proves
    they are rendered OUTSIDE the ``elif self._core.runtime_info`` banner branch.
    """
    core = AppCore(
        llm_service=fake_llm,
        event_log=event_log,
        skill_frames={
            "BrokenSkill": SkillFrame(
                frame=PermissionFrame(base="none"),
                blocked_reason="bad tools block",
            )
        },
        permission_degraded=True,
    )
    app = ICoderApp(core)
    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one(OutputLog)
        text = "\n".join(output.recorded_lines)
        # Both failure kinds surfaced; the skill is lower-cased to its command.
        assert "degraded" in text
        assert "/brokenskill is disabled: bad tools block" in text


async def test_startup_no_notices_when_healthy(
    fake_llm: FakeLLMService, event_log: EventLog
) -> None:
    """A healthy startup (no degraded config, no broken skill) renders no notices."""
    core = AppCore(
        llm_service=fake_llm,
        event_log=event_log,
        skill_frames={"ok": SkillFrame(frame=PermissionFrame(base="inherit"))},
        permission_degraded=False,
    )
    app = ICoderApp(core)
    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one(OutputLog)
        text = "\n".join(output.recorded_lines)
        assert "degraded" not in text
        assert "is disabled" not in text


async def test_resume_path_skips_startup_notices(
    fake_llm: FakeLLMService, event_log: EventLog, tmp_path: Path
) -> None:
    """The resume path skips startup permission notices (fresh-start only, #1061)."""
    log_path = tmp_path / "icoder_2026-05-01T10-00-00.jsonl"
    events = [
        {"t": 0.0, "event": "session_start", "provider": "claude"},
        {"t": 0.1, "event": "input_received", "text": "prior"},
    ]
    log_path.write_text(
        "\n".join(json.dumps(ev) for ev in events) + "\n", encoding="utf-8"
    )
    core = AppCore(
        llm_service=fake_llm,
        event_log=event_log,
        skill_frames={
            "brokenskill": SkillFrame(
                frame=PermissionFrame(base="none"),
                blocked_reason="bad tools block",
            )
        },
        permission_degraded=True,
    )
    app = ICoderApp(core, resume_log_path=log_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one(OutputLog)
        text = "\n".join(output.recorded_lines)
        assert "degraded" not in text
        assert "is disabled" not in text


# --- Step 9: approval_request branch + the direct UI -> engine cancel channel ---


class _RecordingEngine(ApprovalEngine):
    """Engine stub recording what the UI sends it (subclassed, so the type holds)."""

    def __init__(self) -> None:
        super().__init__()
        self.resolved: list[tuple[str, ApprovalDecision]] = []
        self.cancel_calls = 0

    def resolve_pending(self, approval_id: str, decision: ApprovalDecision) -> None:
        self.resolved.append((approval_id, decision))

    def cancel_all(self) -> None:
        self.cancel_calls += 1


async def test_approval_request_auto_denies_and_renders_nothing(
    fake_llm: FakeLLMService, event_log: EventLog
) -> None:
    """An approval_request resolves as a deny carrying _DENY_NO_UI, rendering nothing.

    Interim behaviour until the modal lands (#1046): the reason is the UI's own
    string, never the gateway's user-deny wording, because no user was asked.
    """
    engine = _RecordingEngine()
    app = ICoderApp(
        AppCore(llm_service=fake_llm, event_log=event_log, approval_engine=engine)
    )
    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one(OutputLog)
        before = list(output.recorded_lines)

        app._handle_stream_event(
            {
                "type": "approval_request",
                "approval_id": "a1",
                "tool_name": "mcp__srv__do_it",
                "args": {},
            }
        )
        await pilot.pause()

        assert len(engine.resolved) == 1
        approval_id, decision = engine.resolved[0]
        assert approval_id == "a1"
        assert decision.outcome == "deny"
        assert decision.scope == "once"
        assert decision.reason == _DENY_NO_UI
        # Nothing rendered, and no turn/tool state was touched.
        assert output.recorded_lines == before
        assert app._current_turn_id is None
        assert not app._open_tool_units


async def test_cancel_stream_also_cancels_pending_approvals(
    fake_llm: FakeLLMService, event_log: EventLog
) -> None:
    """Escape sets the cancel event AND reaches the engine (FINDINGS §4)."""
    engine = _RecordingEngine()
    app = ICoderApp(
        AppCore(llm_service=fake_llm, event_log=event_log, approval_engine=engine)
    )
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()

        assert engine.cancel_calls == 1
        assert app._cancel_event.is_set()


# --- Step 10: shutdown hook + closed-app guard (R9) ---

#: Hard cap on the quit-with-an-approval-pending case, deliberately far below
#: the provider's 300s inactivity timeout: a stall must fail fast rather than
#: pass for a stalled-then-timed-out turn.
_QUIT_TIMEOUT = 30.0


class _ApprovalPendingLLMService:
    """Fake service reproducing ``_ask_agent_stream``'s two-loop topology.

    ``ApprovalEngine.request_approval`` runs on a background thread with its own
    ``asyncio.run`` loop (the stand-in agent loop) and the emitted event travels
    through a ``queue.Queue``, so the Textual worker parks in ``q.get`` while the
    approval future lives on a *different* loop -- exactly the shape R9 is about,
    without needing a real agent.
    """

    def __init__(self, engine: ApprovalEngine) -> None:
        self._engine = engine
        self.agent_thread: threading.Thread | None = None
        #: Set once the UI has handled the emitted event and the consumer has
        #: gone back to ``q.get`` -- i.e. the approval is genuinely pending.
        self.dispatched = threading.Event()

    def stream(
        self, question: str, *, frame: PermissionFrame | None = None
    ) -> Iterator[StreamEvent]:
        q: queue.Queue[StreamEvent | None] = queue.Queue()

        async def _ask() -> None:
            try:
                await self._engine.request_approval(
                    tool_name="mcp__srv__do_it", args={}, source="project"
                )
            finally:
                q.put(None)  # sentinel, like the provider's producer half

        def _agent_main() -> None:
            # Production keeps the CancelledError off ``asyncio.run``: the
            # provider's ``_run`` wraps its ``run_agent_stream`` drain in an
            # ``except asyncio.CancelledError`` and returns normally, so the
            # agent thread exits quietly with the sentinel already queued. This
            # fake has no drain to wrap -- ``_ask`` is the whole coroutine --
            # so it catches at the thread top instead. Same observable result,
            # which is what the pilot tests below assert: a silent thread exit
            # and no stray traceback over a live Textual screen.
            try:
                asyncio.run(_ask())
            except BaseException:  # pylint: disable=broad-exception-caught
                pass

        self._engine.attach(q.put)
        thread = threading.Thread(target=_agent_main, daemon=True)
        self.agent_thread = thread
        thread.start()
        try:
            while True:
                event = q.get(timeout=_QUIT_TIMEOUT)
                if event is None:
                    return
                yield event
                self.dispatched.set()
        finally:
            # Same order as the provider: detach (cancelling what is left)
            # BEFORE the join, so a parked interceptor unwinds while it waits.
            self._engine.detach()
            thread.join(timeout=5)

    @property
    def provider(self) -> str:
        return "claude"

    @property
    def session_id(self) -> str | None:
        return None

    def reset_session(self) -> None:
        pass

    def set_session_id(self, session_id: str | None) -> None:
        pass


async def test_quit_with_approval_pending_exits_and_unwinds_worker(
    event_log: EventLog, monkeypatch: pytest.MonkeyPatch
) -> None:
    """R9 on the real exit path: quitting with an approval pending must not hang.

    Asserting only that ``on_unmount`` called ``cancel_pending_approvals()``
    would be a proxy for the hook, not for R9 -- it would stay green while the
    unwound worker blocked forever in ``call_from_thread`` against a dead
    message pump. So this drives the whole path: the app exits, the parked
    agent thread dies, and the ``_stream_llm`` worker body returns.
    """
    engine = ApprovalEngine()
    service = _ApprovalPendingLLMService(engine)
    app = ICoderApp(
        AppCore(llm_service=service, event_log=event_log, approval_engine=engine)
    )

    # TODO(#1046): delete this patch together with the auto-deny it defeats.
    # Step 9's interim ``approval_request`` branch answers every request
    # synchronously through AppCore.resolve_pending, so without this nothing is
    # ever pending at quit time and the test cannot exercise R9 at all. The UI
    # branch itself stays unpatched -- its interaction with shutdown is the
    # thing under test. Once the modal lands, a pending approval is the natural
    # state while it is open and this patch point disappears rather than moves.
    monkeypatch.setattr(
        AppCore, "resolve_pending", lambda self, approval_id, decision: None
    )

    # Textual thread workers run in a pooled, reused thread, so ``is_alive()``
    # says nothing about the worker *body*. Wrap it instead: the event is set
    # only once ``_stream_llm`` actually returns.
    worker_done = threading.Event()
    worker_error: list[BaseException] = []
    original_stream_llm = app._stream_llm

    def _tracked(text: str, skill_name: str | None = None) -> None:
        try:
            original_stream_llm(text, skill_name)
        except BaseException as exc:  # pylint: disable=broad-exception-caught
            worker_error.append(exc)
        finally:
            worker_done.set()

    monkeypatch.setattr(app, "_stream_llm", _tracked)

    async def _turn_then_quit() -> None:
        async with app.run_test() as pilot:
            await _submit_and_wait(app, pilot, text="use the tool")
            for _ in range(200):
                if service.dispatched.is_set():
                    break
                await pilot.pause(delay=0.05)
            assert (
                service.dispatched.is_set()
            ), "the approval_request never reached the UI"
            assert engine.pending() == 1, "nothing pending: R9 is not being exercised"
            app.exit()
            await pilot.pause()

    await asyncio.wait_for(_turn_then_quit(), timeout=_QUIT_TIMEOUT)

    assert not app.is_running, "the app did not exit"
    assert engine.cancelled, "on_unmount never reached the engine"
    # Both halves of R9 in one pair of asserts. Without the closed-app guard the
    # worker tail's ``call_from_thread`` hops reach a torn-down app: either they
    # block on a loop this (blocking) wait is keeping busy, or they run and
    # explode on the cleared widget tree.
    assert worker_done.wait(timeout=10.0), "the _stream_llm worker body never returned"
    assert worker_error == [], f"the worker tail hit a torn-down app: {worker_error!r}"
    assert service.agent_thread is not None
    assert (
        service.agent_thread.is_alive() is False
    ), "the parked approval future was never cancelled"


async def test_shutdown_guard_drops_every_ui_call_from_worker_tail(
    make_icoder_app: Callable[..., ICoderApp], monkeypatch: pytest.MonkeyPatch
) -> None:
    """With ``_shutting_down`` set, the worker issues no ``call_from_thread``.

    Driven from the UI thread on purpose: with the guard up not a single
    cross-thread hop is attempted, so the body is free to run here -- and the
    call the tail would otherwise make (``_reset_busy_indicator``, on the
    ``elif not _error_handled`` branch) is the exact one that hangs a quit.
    """
    app = make_icoder_app(
        responses=[[{"type": "text_delta", "text": "hi"}, {"type": "done"}]]
    )
    async with app.run_test() as pilot:
        await pilot.pause()
        calls: list[Callable[..., None]] = []
        monkeypatch.setattr(
            app, "call_from_thread", lambda callback, *args: calls.append(callback)
        )
        app._shutting_down.set()

        app._stream_llm("hello")  # returns instead of blocking on a dead pump

        assert calls == []


async def test_shutdown_race_runtime_error_is_logged_not_propagated(
    make_icoder_app: Callable[..., ICoderApp],
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A ``RuntimeError`` in the race window is caught and logged, never raised.

    ``_shutting_down`` is deliberately NOT set here: this is the narrow window
    where the flag is still down but ``App._loop`` has already gone, so
    ``call_from_thread`` raises. It must not escape the worker.
    """
    app = make_icoder_app(
        responses=[[{"type": "text_delta", "text": "hi"}, {"type": "done"}]]
    )

    def _pump_is_gone(callback: Callable[..., None], *args: object) -> None:
        raise RuntimeError("App is not running")

    async with app.run_test() as pilot:
        await pilot.pause()
        monkeypatch.setattr(app, "call_from_thread", _pump_is_gone)
        with caplog.at_level(logging.DEBUG, logger="mcp_coder.icoder.ui.stream_view"):
            app._stream_llm("hello")

        assert any(
            "call_from_thread dropped during shutdown" in record.getMessage()
            for record in caplog.records
        )
