"""Textual pilot integration tests for ICoderApp."""

from __future__ import annotations

import pytest

from mcp_coder.icoder.core.app_core import AppCore
from mcp_coder.icoder.core.event_log import EventLog
from mcp_coder.icoder.services.llm_service import FakeLLMService
from mcp_coder.icoder.ui.app import ICoderApp
from mcp_coder.icoder.ui.widgets.input_area import InputArea
from mcp_coder.icoder.ui.widgets.output_log import OutputLog

pytestmark = pytest.mark.textual_integration


@pytest.fixture
def icoder_app(fake_llm: FakeLLMService, event_log: EventLog) -> ICoderApp:
    """Create ICoderApp with fake dependencies."""
    app_core = AppCore(llm_service=fake_llm, event_log=event_log)
    return ICoderApp(app_core)


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
