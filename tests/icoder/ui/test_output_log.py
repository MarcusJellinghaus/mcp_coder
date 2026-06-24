"""Unit tests for OutputLog widget.

Existing-test audit (step 5): every test below that asserts on
``recorded_lines`` checks **emission semantics** ("was this text
appended?") — these correctly stay on ``recorded_lines`` (append history).
No existing test asserts screen-state semantics, so there is nothing to
migrate to ``rendered_lines`` yet (that migration target lands with the
tier toggle in step 6).
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import Mock, call

import pytest
from rich.markdown import Markdown
from textual.app import App, ComposeResult

from mcp_coder.icoder.ui.widgets.output_log import ContentUnit, OutputLog

pytestmark = pytest.mark.textual_integration


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


def _make_turn_unit(unit_id: str) -> ContentUnit:
    """Build an assistant_turn ContentUnit for tests."""
    return ContentUnit(
        id=unit_id,
        kind="assistant_turn",
        timestamp=datetime(2026, 6, 24, 12, 0, 0),
    )


class _RegistryApp(App[None]):
    """Minimal app hosting a single OutputLog for registry tests."""

    def compose(self) -> ComposeResult:
        yield OutputLog()


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


async def test_append_unit_registers_unit_and_range() -> None:
    """append_unit registers the unit and one range covering its lines."""
    app = _RegistryApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one(OutputLog)
        unit = _make_tool_unit("A")
        output.append_unit(unit, ["l1", "l2", "l3"])
        await pilot.pause()

        assert "A" in output._units
        assert len(output._ranges) == 1
        start, end, uid = output._ranges[0]
        assert uid == "A"
        assert end - start == 3
        assert output.unit_at_line(0) is unit


async def test_unit_at_line_returns_none_outside_range() -> None:
    """unit_at_line returns None for a line past any registered range."""
    app = _RegistryApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one(OutputLog)
        output.append_unit(_make_tool_unit("A"), ["l1", "l2"])
        await pilot.pause()

        assert output.unit_at_line(99) is None


async def test_unit_at_line_disjoint_ranges() -> None:
    """Each line resolves to its unit; gaps between ranges resolve to None."""
    app = _RegistryApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one(OutputLog)
        unit_a = _make_tool_unit("A")
        unit_b = _make_tool_unit("B")
        output.append_unit(unit_a, ["a1", "a2"])
        output.append_unit(unit_b, ["b1", "b2"])
        await pilot.pause()

        (start_a, end_a, _), (start_b, end_b, _) = output._ranges
        assert output.unit_at_line(start_a) is unit_a
        assert output.unit_at_line(end_a - 1) is unit_a
        assert output.unit_at_line(start_b) is unit_b
        assert output.unit_at_line(end_b - 1) is unit_b


async def test_extend_open_unit_adds_range_per_line() -> None:
    """extend_open_unit creates one range entry per line, same unit_id."""
    app = _RegistryApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one(OutputLog)
        turn = _make_turn_unit("T")
        output.append_unit(turn, [])
        output.extend_open_unit("T", ["x", "y", "z"])
        await pilot.pause()

        assert len(output._ranges) == 3
        assert all(uid == "T" for _, _, uid in output._ranges)
        for start, _, _ in output._ranges:
            assert output.unit_at_line(start) is turn


async def test_extend_open_unit_interleaves_with_tool() -> None:
    """Turn lines and an interleaved tool resolve to the right units."""
    app = _RegistryApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one(OutputLog)
        turn = _make_turn_unit("T")
        tool = _make_tool_unit("X")
        output.append_unit(turn, [])
        output.extend_open_unit("T", ["t1", "t2"])
        output.append_unit(tool, ["tool1"])
        output.extend_open_unit("T", ["t3", "t4"])
        await pilot.pause()

        assert len(output._ranges) == 5
        # tool range resolves to the tool unit
        tool_range = next(r for r in output._ranges if r[2] == "X")
        assert output.unit_at_line(tool_range[0]) is tool
        # turn ranges resolve to the turn unit
        turn_ranges = [r for r in output._ranges if r[2] == "T"]
        assert len(turn_ranges) == 4
        for start, _, _ in turn_ranges:
            assert output.unit_at_line(start) is turn


async def test_last_unit_returns_most_recent() -> None:
    """last_unit returns the most recently registered unit."""
    app = _RegistryApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one(OutputLog)
        output.append_unit(_make_tool_unit("A"), ["a"])
        output.append_unit(_make_tool_unit("B"), ["b"])
        await pilot.pause()

        last = output.last_unit()
        assert last is not None
        assert last.id == "B"


async def test_last_unit_none_when_empty() -> None:
    """last_unit returns None when no units are registered."""
    app = _RegistryApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one(OutputLog)
        assert output.last_unit() is None


async def test_rendered_lines_reflects_screen_state() -> None:
    """rendered_lines matches the logical lines written via append_unit."""
    app = _RegistryApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one(OutputLog)
        output.append_unit(_make_tool_unit("A"), ["a1", "a2"])
        turn = _make_turn_unit("T")
        output.append_unit(turn, [])
        output.extend_open_unit("T", ["t1"])
        await pilot.pause()

        assert output.rendered_lines == ["a1", "a2", "t1"]


async def test_recorded_lines_independent_of_units() -> None:
    """append_unit grows recorded + screen; append_text adds no unit/range."""
    app = _RegistryApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one(OutputLog)
        output.append_unit(_make_tool_unit("A"), ["a1", "a2"])
        await pilot.pause()

        assert output.recorded_lines == ["a1", "a2"]
        assert output.rendered_lines == ["a1", "a2"]

        output.append_text("banner")
        await pilot.pause()

        assert "banner" in output.recorded_lines
        # append_text does NOT create a unit or range or screen line
        assert len(output._units) == 1
        assert len(output._ranges) == 1
        assert "banner" not in output.rendered_lines


async def test_clear_state_wipes_all_state() -> None:
    """clear_state empties every backing store including tier overrides."""
    app = _RegistryApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one(OutputLog)
        output.append_unit(_make_tool_unit("A"), ["a1"])
        output._tool_tier_overrides["A"] = "oneline"
        output.append_text("banner")
        await pilot.pause()

        output.clear_state()

        assert output._units == {}
        assert output._script == []
        assert output._ranges == []
        assert output._screen_lines == []
        assert output.recorded_lines == []
        assert output._tool_tier_overrides == {}


async def test_wrapped_line_range_uses_buffer_index() -> None:
    """A long wrapping line spans multiple buffer lines in its range."""
    app = _RegistryApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one(OutputLog)
        long_line = "x" * 400
        output.append_unit(_make_tool_unit("A"), [long_line])
        await pilot.pause()

        start, end, _ = output._ranges[0]
        # One logical line wrapped to N buffer lines: span > 1.
        assert end - start > 1


async def test_extend_open_unit_raises_for_tool_kind() -> None:
    """extend_open_unit raises ValueError for a tool unit."""
    app = _RegistryApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one(OutputLog)
        output.append_unit(_make_tool_unit("A"), ["a"])
        await pilot.pause()

        with pytest.raises(ValueError):
            output.extend_open_unit("A", ["x"])


async def test_update_unit_and_rerender_replaces_and_rebuilds() -> None:
    """update_unit_and_rerender swaps fields and re-renders the body."""
    app = _RegistryApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one(OutputLog)
        output.append_unit(_make_tool_unit("A"), ["start line"])
        await pilot.pause()

        output.update_unit_and_rerender(
            "A",
            output="X",
            output_lines=("X",),
            total_lines=1,
            truncated=False,
            duration_ms=42,
            is_error=False,
        )
        await pilot.pause()

        assert output._units["A"].output == "X"
        joined = "\n".join(output.rendered_lines)
        assert "X" in joined


async def test_content_unit_parent_id_defaults_none() -> None:
    """ContentUnit constructed without parent_id has parent_id None (v1)."""
    unit = ContentUnit(
        id="A",
        kind="tool",
        timestamp=datetime(2026, 6, 24, 12, 0, 0),
    )
    assert unit.parent_id is None


async def test_append_unit_assistant_turn_with_empty_lines_no_script_entry() -> None:
    """An empty assistant_turn registers the unit but adds no script entry."""
    app = _RegistryApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one(OutputLog)
        turn = _make_turn_unit("T")
        output.append_unit(turn, [])
        await pilot.pause()

        assert "T" in output._units
        assert output._script == []

        output.rebuild()
        await pilot.pause()

        # No script entry → rebuild walks past the empty turn entirely.
        assert output.rendered_lines == []
