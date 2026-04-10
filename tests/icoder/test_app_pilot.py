"""Textual pilot integration tests for ICoderApp."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest
from textual.pilot import Pilot
from textual.widgets import Static

from mcp_coder.icoder.core.app_core import AppCore
from mcp_coder.icoder.core.event_log import EventLog
from mcp_coder.icoder.env_setup import RuntimeInfo
from mcp_coder.icoder.services.llm_service import FakeLLMService, LLMService
from mcp_coder.icoder.ui.app import ICoderApp
from mcp_coder.icoder.ui.widgets.busy_indicator import BusyIndicator
from mcp_coder.icoder.ui.widgets.input_area import InputArea
from mcp_coder.icoder.ui.widgets.output_log import OutputLog
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

    def stream(self, question: str) -> Iterator[StreamEvent]:
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
                    "name": "mcp__workspace__read_file",
                    "args": {"file_path": "x.py"},
                },
                {
                    "type": "tool_result",
                    "name": "mcp__workspace__read_file",
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


# --- Input hint widget tests ---


async def test_hint_visible_when_input_empty(icoder_app: ICoderApp) -> None:
    """Hint widget is visible when input area is empty."""
    async with icoder_app.run_test() as pilot:
        await pilot.pause()
        hint = icoder_app.query_one("#input-hint", Static)
        assert not hint.has_class("hidden")


async def test_hint_hidden_when_input_has_text(icoder_app: ICoderApp) -> None:
    """Hint widget is hidden when input area has text."""
    async with icoder_app.run_test() as pilot:
        input_area = icoder_app.query_one(InputArea)
        input_area.focus()
        await pilot.pause()
        input_area.insert("some text")
        await pilot.pause()
        hint = icoder_app.query_one("#input-hint", Static)
        assert hint.has_class("hidden")


async def test_hint_reappears_after_submit(icoder_app: ICoderApp) -> None:
    """Hint widget reappears after submitting text (input becomes empty)."""
    async with icoder_app.run_test() as pilot:
        input_area = icoder_app.query_one(InputArea)
        input_area.focus()
        await pilot.pause()
        input_area.insert("hello")
        await pilot.pause()
        hint = icoder_app.query_one("#input-hint", Static)
        assert hint.has_class("hidden")
        await pilot.press("enter")
        await pilot.pause()
        assert not hint.has_class("hidden")


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
                "name": "mcp__workspace__read_file",
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


# --- Markdown rendering tests (Step 3) ---


async def test_tool_result_renders_markdown_by_default(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """Tool result output is rendered via Markdown when format_tools=True (default)."""
    app = make_icoder_app(
        responses=[
            [
                {
                    "type": "tool_use_start",
                    "name": "mcp__workspace__read_file",
                    "args": {"file_path": "x.py"},
                },
                {
                    "type": "tool_result",
                    "name": "mcp__workspace__read_file",
                    "output": "# Header\n**bold text**",
                },
                {"type": "done"},
            ]
        ],
    )
    async with app.run_test() as pilot:
        await _submit_and_wait(app, pilot)
        output = app.query_one(OutputLog)
        lines = output.recorded_lines
        # Tool start line should be present
        tool_start_lines = [ln for ln in lines if "┌" in ln]
        assert len(tool_start_lines) >= 1
        # With format_tools=True, tool result goes through write() as Markdown,
        # which records a text representation in _recorded
        result_lines = [ln for ln in lines if "done" in ln]
        assert len(result_lines) >= 1


async def test_tool_result_renders_plain_text_when_no_format(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """Tool result output is rendered as plain text when format_tools=False."""
    app = make_icoder_app(
        responses=[
            [
                {
                    "type": "tool_use_start",
                    "name": "mcp__workspace__read_file",
                    "args": {"file_path": "x.py"},
                },
                {
                    "type": "tool_result",
                    "name": "mcp__workspace__read_file",
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
        lines = output.recorded_lines
        # With format_tools=False, tool result goes through append_text (plain text)
        result_lines = [ln for ln in lines if "│" in ln]
        assert len(result_lines) >= 1
        # The raw pipe-prefixed lines should be in recorded_lines as a single string
        joined = "\n".join(lines)
        assert "# Header" in joined
        assert "**bold text**" in joined
