"""Tests for iCoder UI widgets (OutputLog, InputArea)."""

from __future__ import annotations

import pytest
from textual.app import App, ComposeResult

from mcp_coder.icoder.ui.widgets.input_area import (
    InputArea,
    _count_trailing_backslashes,
)
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
        output.append_text("\u250c read_file(path.py)")
        assert len(output.recorded_lines) == 2


@pytest.mark.asyncio
async def test_output_log_append_text_with_style() -> None:
    """append_text with style still records plain text."""
    app = WidgetTestApp()
    async with app.run_test():
        output = app.query_one(OutputLog)
        output.append_text("hello", style="bold")
        assert output.recorded_lines == ["hello"]


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


# --- Auto-grow tests ---


@pytest.mark.asyncio
async def test_input_area_grows_with_multiline() -> None:
    """InputArea height increases when multiline text is entered."""
    app = WidgetTestApp()
    async with app.run_test() as pilot:
        input_area = app.query_one(InputArea)
        input_area.focus()
        await pilot.pause()
        initial_height = input_area.styles.height
        input_area.insert("line1")
        await pilot.press("shift+enter")
        input_area.insert("line2")
        await pilot.press("shift+enter")
        input_area.insert("line3")
        await pilot.pause()
        assert input_area.styles.height != initial_height


@pytest.mark.asyncio
async def test_input_area_grows_with_wrapped_long_line() -> None:
    """InputArea height accounts for visual wrapping, not just logical lines."""

    class NarrowApp(App[None]):
        def compose(self) -> ComposeResult:
            yield InputArea()

    app = NarrowApp()
    async with app.run_test(size=(40, 20)) as pilot:
        input_area = app.query_one(InputArea)
        input_area.focus()
        await pilot.pause()
        # Single logical line that wraps multiple times in a 40-col terminal
        long_line = "A" * 120
        input_area.insert(long_line)
        await pilot.pause()
        # With only 1 logical line, document.line_count would be 1
        # so old height would be 1+2=3.
        # With wrapping, virtual_size.height should be > 1, giving a larger height.
        assert input_area.document.line_count == 1
        height_val = input_area.styles.height
        assert height_val is not None
        # Height should be more than what logical line_count + 2 would give
        # logical would give Scalar(3, ...), wrapped should give more
        from textual.css.scalar import Scalar

        if isinstance(height_val, Scalar):
            resolved = int(height_val.value)
        else:
            resolved = int(height_val)
        assert resolved > 3, f"Expected height > 3 for wrapped line, got {resolved}"


# --- History key integration tests ---


@pytest.mark.asyncio
async def test_input_area_up_recalls_history() -> None:
    """Up arrow on first line recalls the last history entry."""
    app = WidgetTestApp()
    async with app.run_test() as pilot:
        input_area = app.query_one(InputArea)
        input_area.focus()
        await pilot.pause()
        input_area.command_history.add("first")
        input_area.command_history.add("second")
        await pilot.press("up")
        await pilot.pause()
        assert input_area.text == "second"


@pytest.mark.asyncio
async def test_input_area_up_down_cycle() -> None:
    """Up then Down cycles through history and back to draft."""
    app = WidgetTestApp()
    async with app.run_test() as pilot:
        input_area = app.query_one(InputArea)
        input_area.focus()
        await pilot.pause()
        input_area.command_history.add("cmd1")
        input_area.insert("draft")
        await pilot.pause()
        await pilot.press("up")
        await pilot.pause()
        assert input_area.text == "cmd1"
        await pilot.press("down")
        await pilot.pause()
        assert input_area.text == "draft"


@pytest.mark.asyncio
async def test_input_area_up_no_history_no_change() -> None:
    """Up arrow with no history does not change the text."""
    app = WidgetTestApp()
    async with app.run_test() as pilot:
        input_area = app.query_one(InputArea)
        input_area.focus()
        await pilot.pause()
        input_area.insert("current")
        await pilot.pause()
        await pilot.press("up")
        await pilot.pause()
        assert input_area.text == "current"


@pytest.mark.asyncio
async def test_input_area_up_down_multiline_cursor_movement() -> None:
    """Up/Down in middle of multiline text moves cursor, not history."""
    app = WidgetTestApp()
    async with app.run_test() as pilot:
        input_area = app.query_one(InputArea)
        input_area.focus()
        await pilot.pause()
        input_area.command_history.add("old cmd")
        input_area.load_text("line1\nline2\nline3")
        input_area.move_cursor(input_area.document.end)
        await pilot.pause()
        await pilot.press("up")
        await pilot.pause()
        assert input_area.text == "line1\nline2\nline3"


@pytest.mark.asyncio
async def test_input_area_has_history_attribute() -> None:
    """InputArea exposes a CommandHistory instance."""
    app = WidgetTestApp()
    async with app.run_test():
        input_area = app.query_one(InputArea)
        assert hasattr(input_area, "command_history")
        from mcp_coder.icoder.core.command_history import CommandHistory

        assert isinstance(input_area.command_history, CommandHistory)


@pytest.mark.asyncio
async def test_input_area_no_registry_backward_compat() -> None:
    """InputArea() with no registry mounts and accepts text changes (no autocomplete behavior)."""
    app = WidgetTestApp()
    async with app.run_test() as pilot:
        input_area = app.query_one(InputArea)
        input_area.focus()
        await pilot.pause()
        input_area.insert("/hel")
        await pilot.pause()
        # Should not crash — no registry means autocomplete is skipped
        assert input_area.text == "/hel"
        assert input_area._registry is None  # noqa: SLF001


# --- _count_trailing_backslashes unit tests ---


@pytest.mark.parametrize(
    "text, expected",
    [
        ("hello\\", 1),
        ("hello\\\\", 2),
        ("hello\\\\\\", 3),
        ("hello\\\\\\\\", 4),
        ("\\", 1),
        ("hello", 0),
        ("", 0),
    ],
)
def test_count_trailing_backslashes(text: str, expected: int) -> None:
    """_count_trailing_backslashes counts consecutive trailing backslashes."""
    assert _count_trailing_backslashes(text) == expected


# --- Backslash+Enter mid-cursor tests ---


@pytest.mark.asyncio
async def test_backslash_enter_mid_text_inserts_newline() -> None:
    """Single backslash before cursor mid-text inserts newline at cursor position."""
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
        input_area.load_text("ABC \\DEF")
        # Position cursor after the backslash (col 5: A=0,B=1,C=2,' '=3,'\\'=4)
        input_area.move_cursor((0, 5))
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        assert len(messages) == 0, "Expected no submit for single backslash"
        assert input_area.text == "ABC \nDEF"


@pytest.mark.asyncio
async def test_backslash_enter_mid_text_double_backslash_submits() -> None:
    """Double backslash before cursor mid-text strips one and submits."""
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
        input_area.load_text("ABC \\\\DEF")
        # Position cursor after two backslashes (col 6)
        input_area.move_cursor((0, 6))
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        assert len(messages) == 1, "Expected submit for double backslash"
        assert messages[0].text == "ABC \\DEF"
        assert input_area.text == ""


# --- Backslash+Enter newline escape tests ---


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "input_text, expect_submit, expected_text",
    [
        pytest.param("hello\\", False, "hello\n", id="single-backslash-newline"),
        pytest.param("hello\\\\", True, "hello\\", id="double-backslash-submit"),
        pytest.param(
            "hello\\\\\\", False, "hello\\\\\n", id="triple-backslash-newline"
        ),
        pytest.param("hello\\\\\\\\", True, "hello\\\\\\", id="quad-backslash-submit"),
        pytest.param("\\", False, "\n", id="lone-backslash-newline"),
        pytest.param("hello", True, "hello", id="no-backslash-submit"),
    ],
)
async def test_backslash_enter_newline(
    input_text: str, expect_submit: bool, expected_text: str
) -> None:
    """Backslash+Enter inserts newline; double-backslash+Enter submits with one backslash stripped."""
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
        input_area.load_text(input_text)
        input_area.move_cursor(input_area.document.end)
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        if expect_submit:
            assert (
                len(messages) == 1
            ), f"Expected submit but got {len(messages)} messages"
            assert messages[0].text == expected_text
            assert input_area.text == ""
        else:
            assert (
                len(messages) == 0
            ), f"Expected no submit but got {len(messages)} messages"
            assert input_area.text == expected_text
