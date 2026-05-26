"""Unit tests for OutputLog widget."""

from __future__ import annotations

from unittest.mock import Mock, call

import pytest
from rich.markdown import Markdown

from mcp_coder.icoder.ui.widgets.output_log import OutputLog

pytestmark = pytest.mark.textual_integration


async def test_output_log_write_records_text() -> None:
    """OutputLog.write() with a Rich renderable also appends to _recorded."""
    from textual.app import App, ComposeResult

    class TestApp(App[None]):
        def compose(self) -> ComposeResult:
            yield OutputLog()

    app = TestApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one(OutputLog)

        # Write a Markdown renderable
        md = Markdown("# Hello\n**bold**")
        output.write(md)
        await pilot.pause()

        # The write override should record the markup text
        assert len(output.recorded_lines) >= 1
        joined = "\n".join(output.recorded_lines)
        assert "Hello" in joined
        assert "bold" in joined


async def test_output_log_append_text_records() -> None:
    """OutputLog.append_text() records text in _recorded (existing behavior)."""
    from textual.app import App, ComposeResult

    class TestApp(App[None]):
        def compose(self) -> ComposeResult:
            yield OutputLog()

    app = TestApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one(OutputLog)
        output.append_text("plain text")
        assert "plain text" in output.recorded_lines


async def test_mirror_called_for_blank_line_spacer() -> None:
    """OutputLog.write('') invokes mirror but does NOT pollute _recorded."""
    from textual.app import App, ComposeResult

    mock = Mock()

    class TestApp(App[None]):
        def compose(self) -> ComposeResult:
            yield OutputLog(mirror=mock)

    app = TestApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one(OutputLog)

        output.write("")
        await pilot.pause()

        assert mock.call_args_list == [call("")]
        assert output.recorded_lines == []


async def test_mirror_called_for_markdown_write() -> None:
    """OutputLog.write(Markdown(...)) mirrors the same markup recorded."""
    from textual.app import App, ComposeResult

    mock = Mock()

    class TestApp(App[None]):
        def compose(self) -> ComposeResult:
            yield OutputLog(mirror=mock)

    app = TestApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one(OutputLog)

        output.write(Markdown("# Hello\n**bold**"))
        await pilot.pause()

        assert mock.call_count == 1
        (mirrored,) = mock.call_args.args
        assert isinstance(mirrored, str)
        assert mirrored != ""
        assert "Hello" in mirrored


async def test_mirror_called_for_append_text() -> None:
    """OutputLog.append_text() mirrors both plain and styled writes."""
    from textual.app import App, ComposeResult

    mock = Mock()

    class TestApp(App[None]):
        def compose(self) -> ComposeResult:
            yield OutputLog(mirror=mock)

    app = TestApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one(OutputLog)

        output.append_text("plain")
        output.append_text("styled", style="dim")
        await pilot.pause()

        assert mock.call_args_list == [call("plain"), call("styled")]


async def test_no_mirror_when_callback_is_none() -> None:
    """OutputLog() with default mirror=None still works and records correctly."""
    from textual.app import App, ComposeResult

    class TestApp(App[None]):
        def compose(self) -> ComposeResult:
            yield OutputLog()

    app = TestApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one(OutputLog)

        output.write("")
        output.write(Markdown("x"))
        output.append_text("y")
        await pilot.pause()

        joined = "\n".join(output.recorded_lines)
        assert "x" in joined
        assert "y" in output.recorded_lines
        assert "" not in output.recorded_lines
