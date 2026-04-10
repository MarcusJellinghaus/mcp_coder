"""Unit tests for OutputLog widget."""

from __future__ import annotations

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
