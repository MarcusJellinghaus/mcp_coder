"""Click-handling tests for the OutputLog widget.

Covers single/double/triple click debounce semantics and button/range
filtering. Split out of ``test_output_log.py`` to keep each module under
the file-size limit.
"""

from __future__ import annotations

from datetime import datetime

import pytest
from textual.app import App, ComposeResult
from textual.events import Click

from mcp_coder.icoder.ui.widgets.output_log import ContentUnit, OutputLog

pytestmark = pytest.mark.textual_integration


def _make_click(widget: OutputLog, y: int, *, button: int = 1, chain: int = 1) -> Click:
    """Build a left-button Click event at relative line ``y``."""
    return Click(
        widget,
        x=0,
        y=y,
        delta_x=0,
        delta_y=0,
        button=button,
        shift=False,
        meta=False,
        ctrl=False,
        chain=chain,
    )


def _make_tool_unit(
    unit_id: str,
    *,
    tool_name: str = "read_file",
    output_lines: tuple[str, ...] = (),
    total_lines: int = 0,
) -> ContentUnit:
    """Build a tool ContentUnit for tests."""
    return ContentUnit(
        id=unit_id,
        kind="tool",
        timestamp=datetime(2026, 6, 24, 12, 0, 0),
        tool_name=tool_name,
        args={"path": "src/main.py"},
        output_lines=output_lines,
        total_lines=total_lines,
    )


def _make_user_input_unit(unit_id: str, text: str = "hello") -> ContentUnit:
    """Build a user_input ContentUnit for tests."""
    return ContentUnit(
        id=unit_id,
        kind="user_input",
        timestamp=datetime(2026, 6, 24, 12, 0, 0),
        full_text=text,
    )


class _RegistryApp(App[None]):
    """Minimal app hosting a single OutputLog for registry tests."""

    def compose(self) -> ComposeResult:
        yield OutputLog()


async def test_click_chain_3_ignored() -> None:
    """A triple click (chain=3) toggles nothing and opens no modal."""
    app = _RegistryApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one(OutputLog)
        output.append_unit(
            _make_tool_unit("A", output_lines=("o1",), total_lines=1), ["s"]
        )
        await pilot.pause()
        before = output.effective_tier("A")

        output.on_click(_make_click(output, 0, chain=3))
        await pilot.pause(0.3)

        assert output.effective_tier("A") == before
        assert output._pending_single is None
        assert len(app.screen_stack) == 1


async def test_click_right_button_ignored() -> None:
    """A right-button click (button=3) is a no-op."""
    app = _RegistryApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one(OutputLog)
        output.append_unit(
            _make_tool_unit("A", output_lines=("o1",), total_lines=1), ["s"]
        )
        await pilot.pause()
        before = output.effective_tier("A")

        output.on_click(_make_click(output, 0, button=3))
        await pilot.pause(0.3)

        assert output.effective_tier("A") == before
        assert len(app.screen_stack) == 1


async def test_click_on_blank_line_noop() -> None:
    """A click outside any registered range toggles nothing."""
    app = _RegistryApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one(OutputLog)
        output.append_unit(
            _make_tool_unit("A", output_lines=("o1",), total_lines=1), ["s"]
        )
        await pilot.pause()
        before = output.effective_tier("A")

        output.on_click(_make_click(output, 99, chain=1))
        await pilot.pause(0.3)

        assert output.effective_tier("A") == before
        assert output._pending_single is None


async def test_double_click_cancels_pending_single() -> None:
    """A chain-1 then chain-2 click never fires the single handler."""
    app = _RegistryApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one(OutputLog)
        output.append_unit(
            _make_tool_unit("A", output_lines=("o1",), total_lines=1), ["s"]
        )
        await pilot.pause()

        output.on_click(_make_click(output, 0, chain=1))
        output.on_click(_make_click(output, 0, chain=2))
        await pilot.pause(0.3)

        # Single handler cancelled → no tier override was recorded.
        assert output._tool_tier_overrides == {}
        assert output._pending_single is None


async def test_single_click_on_tool_toggles_after_debounce() -> None:
    """A single click on a tool unit flips its tier after the debounce."""
    app = _RegistryApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one(OutputLog)
        output.append_unit(
            _make_tool_unit("A", output_lines=("o1", "o2"), total_lines=2), ["start"]
        )
        await pilot.pause()
        before = output.effective_tier("A")

        output.on_click(_make_click(output, 0, chain=1))
        await pilot.pause(0.6)

        assert output.effective_tier("A") != before


async def test_single_click_on_user_input_noops() -> None:
    """A single click on a user_input unit records no tier override."""
    app = _RegistryApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one(OutputLog)
        output.append_unit(_make_user_input_unit("U"), ["> hello"])
        await pilot.pause()

        output.on_click(_make_click(output, 0, chain=1))
        await pilot.pause(0.3)

        assert output._tool_tier_overrides == {}
