"""End-to-end pipeline tests for tool output visibility in ICoderApp."""

from __future__ import annotations

from collections.abc import Callable

import pytest

from mcp_coder.icoder.core.app_core import AppCore
from mcp_coder.icoder.core.event_log import EventLog
from mcp_coder.icoder.services.llm_service import FakeLLMService
from mcp_coder.icoder.ui.app import ICoderApp
from mcp_coder.icoder.ui.widgets.busy_indicator import BusyIndicator
from mcp_coder.icoder.ui.widgets.output_log import OutputLog
from mcp_coder.llm.types import StreamEvent

pytestmark = pytest.mark.textual_integration


@pytest.fixture
def make_icoder_app(
    event_log: EventLog,
) -> Callable[..., ICoderApp]:
    """Factory to create ICoderApp with custom FakeLLM responses."""

    def _factory(
        *,
        responses: list[list[StreamEvent]] | None = None,
    ) -> ICoderApp:
        llm = FakeLLMService(responses=responses or [])
        return ICoderApp(
            AppCore(llm_service=llm, event_log=event_log),
        )

    return _factory


async def test_tool_output_list_directory(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """List directory tool output lines appear in recorded output."""
    app = make_icoder_app(responses=[])
    async with app.run_test() as pilot:
        await pilot.pause()
        app._handle_stream_event(
            {
                "type": "tool_use_start",
                "name": "mcp__workspace__list_directory",
                "args": {},
            }
        )
        app._handle_stream_event(
            {
                "type": "tool_result",
                "name": "mcp__workspace__list_directory",
                "output": '{"result": ["file1.py", "file2.py", "src/"]}',
            }
        )
        lines = app.query_one(OutputLog).recorded_lines
        joined = "\n".join(lines)
        assert "file1.py" in joined
        assert "file2.py" in joined
        assert "src/" in joined
        assert "└ done" in joined


async def test_tool_output_read_file(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """Read file tool output lines appear in recorded output."""
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
        app._handle_stream_event(
            {
                "type": "tool_result",
                "name": "mcp__workspace__read_file",
                "output": '{"result": "line1\\nline2\\nline3"}',
            }
        )
        lines = app.query_one(OutputLog).recorded_lines
        joined = "\n".join(lines)
        assert "line1" in joined
        assert "line2" in joined
        assert "line3" in joined
        assert "└ done" in joined


async def test_tool_output_truncated(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """Truncated tool output shows truncation marker."""
    long_content = "\\n".join(f"line{i}" for i in range(30))
    app = make_icoder_app(responses=[])
    async with app.run_test() as pilot:
        await pilot.pause()
        app._handle_stream_event(
            {
                "type": "tool_use_start",
                "name": "mcp__workspace__read_file",
                "args": {"file_path": "big.py"},
            }
        )
        app._handle_stream_event(
            {
                "type": "tool_result",
                "name": "mcp__workspace__read_file",
                "output": '{"result": "' + long_content + '"}',
            }
        )
        lines = app.query_one(OutputLog).recorded_lines
        joined = "\n".join(lines)
        assert "truncated" in joined
        assert "skipped" in joined


async def test_tool_output_empty(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """Empty tool output still shows done footer."""
    app = make_icoder_app(responses=[])
    async with app.run_test() as pilot:
        await pilot.pause()
        app._handle_stream_event(
            {
                "type": "tool_use_start",
                "name": "mcp__workspace__read_file",
                "args": {"file_path": "empty.py"},
            }
        )
        app._handle_stream_event(
            {
                "type": "tool_result",
                "name": "mcp__workspace__read_file",
                "output": "",
            }
        )
        lines = app.query_one(OutputLog).recorded_lines
        joined = "\n".join(lines)
        assert "└ done" in joined


async def test_busy_indicator_thinking_after_tool_result(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """Busy indicator shows 'Thinking about ...' after tool result is rendered."""
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
        app._handle_stream_event(
            {
                "type": "tool_result",
                "name": "mcp__workspace__read_file",
                "output": '{"result": "hello"}',
            }
        )
        indicator = app.query_one(BusyIndicator)
        assert "Thinking about workspace > read_file..." in indicator.label_text


async def test_busy_indicator_resets_on_error_only_stream(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """Busy indicator shows ready after stream yields only an error event (no done)."""
    error_only: list[list[StreamEvent]] = [
        [{"type": "error", "message": "something went wrong"}],
    ]
    app = make_icoder_app(responses=error_only)
    async with app.run_test() as pilot:
        # Type input and press enter to trigger _stream_llm
        await pilot.press("h", "i")
        await pilot.press("enter")
        # Allow the background worker to finish
        await pilot.pause(delay=0.5)
        indicator = app.query_one(BusyIndicator)
        assert indicator.label_text == "✓ Ready"
