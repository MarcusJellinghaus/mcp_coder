from __future__ import annotations

from collections.abc import Callable, Iterator
from unittest.mock import MagicMock

import pytest

from mcp_coder.icoder.core.event_log import EventLog
from mcp_coder.icoder.permissions.model import PermissionFrame
from mcp_coder.icoder.ui.app import ICoderApp
from mcp_coder.icoder.ui.widgets.busy_indicator import BusyIndicator
from mcp_coder.icoder.ui.widgets.input_area import InputArea
from mcp_coder.icoder.ui.widgets.output_log import OutputLog
from mcp_coder.llm.types import StreamEvent
from tests.icoder.test_app_pilot import _submit_and_wait

pytestmark = pytest.mark.textual_integration


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
