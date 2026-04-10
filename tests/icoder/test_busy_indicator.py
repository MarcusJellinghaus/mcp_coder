"""Tests for BusyIndicator widget."""

from __future__ import annotations

import asyncio

import pytest
from textual.app import App, ComposeResult

from mcp_coder.icoder.ui.widgets.busy_indicator import BusyIndicator

pytestmark = pytest.mark.textual_integration


class BusyIndicatorApp(App[None]):
    """Minimal test app that hosts BusyIndicator."""

    def compose(self) -> ComposeResult:
        """Compose with BusyIndicator.

        Yields:
            BusyIndicator widget.
        """
        yield BusyIndicator()


@pytest.mark.asyncio
async def test_initial_state_shows_ready() -> None:
    """After mount, widget renders '✓ Ready'."""
    app = BusyIndicatorApp()
    async with app.run_test():
        indicator = app.query_one(BusyIndicator)
        assert indicator.label_text == "✓ Ready"


@pytest.mark.asyncio
async def test_show_busy_updates_label() -> None:
    """show_busy renders spinner + message + elapsed."""
    app = BusyIndicatorApp()
    async with app.run_test():
        indicator = app.query_one(BusyIndicator)
        indicator.show_busy("Thinking...")
        label = indicator.label_text
        assert "Thinking..." in label
        assert "[" in label and "s]" in label


@pytest.mark.asyncio
async def test_show_ready_resets() -> None:
    """After show_busy then show_ready, widget shows '✓ Ready'."""
    app = BusyIndicatorApp()
    async with app.run_test():
        indicator = app.query_one(BusyIndicator)
        indicator.show_busy("Thinking...")
        indicator.show_ready()
        assert indicator.label_text == "✓ Ready"


@pytest.mark.asyncio
async def test_show_busy_preserves_start_time() -> None:
    """Calling show_busy again while busy preserves the original start time."""
    app = BusyIndicatorApp()
    async with app.run_test():
        indicator = app.query_one(BusyIndicator)
        indicator.show_busy("A")
        await asyncio.sleep(0.05)
        indicator.show_busy("B")
        label = indicator.label_text
        assert "B" in label
        # Extract elapsed — should be > 0 since timer was not reset
        elapsed_str = label.split("[")[1].split("s]")[0]
        elapsed = float(elapsed_str)
        assert elapsed > 0.0


@pytest.mark.asyncio
async def test_show_busy_after_ready_resets_start_time() -> None:
    """After show_busy → show_ready → show_busy, elapsed resets to ~0."""
    app = BusyIndicatorApp()
    async with app.run_test():
        indicator = app.query_one(BusyIndicator)
        indicator.show_busy("A")
        await asyncio.sleep(0.05)
        indicator.show_ready()
        indicator.show_busy("B")
        label = indicator.label_text
        elapsed_str = label.split("[")[1].split("s]")[0]
        elapsed = float(elapsed_str)
        assert elapsed < 0.05


@pytest.mark.asyncio
async def test_spinner_frame_advances() -> None:
    """After a tick, the spinner character changes."""
    app = BusyIndicatorApp()
    async with app.run_test(size=(80, 24)) as pilot:
        indicator = app.query_one(BusyIndicator)
        indicator.show_busy("Working...")
        initial_char = indicator.label_text[0]
        # Wait for at least one tick (interval is 0.15s)
        await pilot.pause(delay=0.3)
        new_char = indicator.label_text[0]
        assert new_char != initial_char
