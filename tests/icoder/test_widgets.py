"""Tests for iCoder UI widgets (OutputLog, InputArea)."""

from __future__ import annotations

import pytest
from textual.app import App, ComposeResult

from mcp_coder.icoder.ui.widgets.input_area import InputArea
from mcp_coder.icoder.ui.widgets.output_log import OutputLog

pytestmark = pytest.mark.textual_integration


class WidgetTestApp(App[None]):
    """Minimal test app that hosts the widgets."""

    def compose(self) -> ComposeResult:
        """Compose with OutputLog and InputArea.

        Yields:
            OutputLog and InputArea widgets.
        """
        yield OutputLog()
        yield InputArea()


@pytest.mark.asyncio
async def test_output_log_append_text() -> None:
    """OutputLog.append_text adds content and records line."""
    app = WidgetTestApp()
    async with app.run_test():
        output = app.query_one(OutputLog)
        output.append_text("hello")
        assert output.recorded_lines == ["hello"]


@pytest.mark.asyncio
async def test_output_log_recorded_lines_property() -> None:
    """OutputLog.recorded_lines tracks all appended content."""
    app = WidgetTestApp()
    async with app.run_test():
        output = app.query_one(OutputLog)
        assert output.recorded_lines == []
        output.append_text("> hello world")
        assert "> hello world" in output.recorded_lines
        output.append_tool_use("read_file", "path.py", "ok")
        assert len(output.recorded_lines) == 2


@pytest.mark.asyncio
async def test_output_log_append_tool_use() -> None:
    """OutputLog.append_tool_use formats with gear and arrow."""
    app = WidgetTestApp()
    async with app.run_test():
        output = app.query_one(OutputLog)
        output.append_tool_use("read_file", "path.py", "ok")
        assert output.recorded_lines == ["\u2699 read_file(path.py) \u2192 ok"]


@pytest.mark.asyncio
async def test_output_log_append_text_with_style() -> None:
    """append_text with style still records plain text."""
    app = WidgetTestApp()
    async with app.run_test():
        output = app.query_one(OutputLog)
        output.append_text("hello", style="bold")
        assert output.recorded_lines == ["hello"]


@pytest.mark.asyncio
async def test_output_log_append_tool_use_with_style() -> None:
    """append_tool_use with style still records plain formatted line."""
    app = WidgetTestApp()
    async with app.run_test():
        output = app.query_one(OutputLog)
        output.append_tool_use("read", "x", "ok", style="bold")
        assert output.recorded_lines == ["\u2699 read(x) \u2192 ok"]


@pytest.mark.asyncio
async def test_output_log_append_text_no_style() -> None:
    """append_text without style works (backward compatibility)."""
    app = WidgetTestApp()
    async with app.run_test():
        output = app.query_one(OutputLog)
        output.append_text("hello")
        assert output.recorded_lines == ["hello"]


@pytest.mark.asyncio
async def test_input_area_enter_submits() -> None:
    """InputArea Enter posts InputSubmitted and clears input."""
    messages: list[InputArea.InputSubmitted] = []

    class SubmitApp(WidgetTestApp):
        def on_input_area_input_submitted(
            self, message: InputArea.InputSubmitted
        ) -> None:
            messages.append(message)

    app = SubmitApp()
    async with app.run_test() as pilot:
        input_area = app.query_one(InputArea)
        input_area.focus()
        await pilot.pause()
        input_area.insert("hello")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        assert len(messages) == 1
        assert messages[0].text == "hello"
        assert input_area.text == ""


@pytest.mark.asyncio
async def test_input_area_shift_enter_newline() -> None:
    """InputArea Shift-Enter inserts newline without submitting."""
    messages: list[InputArea.InputSubmitted] = []

    class SubmitApp(WidgetTestApp):
        def on_input_area_input_submitted(
            self, message: InputArea.InputSubmitted
        ) -> None:
            messages.append(message)

    app = SubmitApp()
    async with app.run_test() as pilot:
        input_area = app.query_one(InputArea)
        input_area.focus()
        await pilot.pause()
        input_area.insert("line1")
        await pilot.pause()
        await pilot.press("shift+enter")
        await pilot.pause()
        input_area.insert("line2")
        await pilot.pause()
        assert "\n" in input_area.text
        assert len(messages) == 0


@pytest.mark.asyncio
async def test_input_area_empty_enter_does_not_submit() -> None:
    """InputArea ignores Enter on empty input."""
    messages: list[InputArea.InputSubmitted] = []

    class SubmitApp(WidgetTestApp):
        def on_input_area_input_submitted(
            self, message: InputArea.InputSubmitted
        ) -> None:
            messages.append(message)

    app = SubmitApp()
    async with app.run_test() as pilot:
        input_area = app.query_one(InputArea)
        input_area.focus()
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        assert len(messages) == 0
