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


def _make_user_input_unit(unit_id: str, text: str = "hello") -> ContentUnit:
    """Build a user_input ContentUnit for tests."""
    return ContentUnit(
        id=unit_id,
        kind="user_input",
        timestamp=datetime(2026, 6, 24, 12, 0, 0),
        full_text=text,
    )


async def test_effective_tier_defaults_to_compressed() -> None:
    """A freshly registered tool unit resolves to the compressed default."""
    app = _RegistryApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one(OutputLog)
        output.append_unit(_make_tool_unit("A"), ["l1"])
        await pilot.pause()

        assert output.effective_tier("A") == "compressed"


async def test_toggle_unit_tier_flips_state() -> None:
    """toggle_unit_tier flips compressed → oneline → compressed."""
    app = _RegistryApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one(OutputLog)
        output.append_unit(_make_tool_unit("A"), ["l1"])
        await pilot.pause()

        assert output.toggle_unit_tier("A") == "oneline"
        assert output.effective_tier("A") == "oneline"
        assert output.toggle_unit_tier("A") == "compressed"
        assert output.effective_tier("A") == "compressed"


async def test_toggle_unit_tier_non_tool_raises_or_noops() -> None:
    """Toggling a user_input unit raises ValueError (only tools toggle)."""
    app = _RegistryApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one(OutputLog)
        output.append_unit(_make_user_input_unit("U"), ["> hello"])
        await pilot.pause()

        with pytest.raises(ValueError):
            output.toggle_unit_tier("U")


async def test_rebuild_is_idempotent() -> None:
    """Two consecutive rebuilds produce identical ranges."""
    app = _RegistryApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one(OutputLog)
        output.append_unit(
            _make_tool_unit("A", output_lines=("o1", "o2"), total_lines=2), ["start"]
        )
        output.append_unit(_make_tool_unit("B"), ["s2"])
        await pilot.pause()

        output.rebuild()
        ranges1 = list(output._ranges)
        output.rebuild()
        ranges2 = list(output._ranges)

        assert ranges1 == ranges2


async def test_rebuild_after_toggle_renders_new_tier() -> None:
    """Toggling to oneline collapses the compressed block to one line."""
    app = _RegistryApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one(OutputLog)
        unit = _make_tool_unit("A", output_lines=("o1", "o2"), total_lines=2)
        output.append_unit(unit, ["start"])
        await pilot.pause()

        output.toggle_unit_tier("A")  # → oneline, triggers rebuild
        await pilot.pause()

        assert len(output.rendered_lines) == 1
        assert "read_file" in output.rendered_lines[0]


async def test_set_tool_display_default_wipes_overrides() -> None:
    """set_tool_display_default clears per-unit overrides (hard reset)."""
    app = _RegistryApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one(OutputLog)
        output.append_unit(
            _make_tool_unit("A", output_lines=("o1",), total_lines=1), ["s1"]
        )
        output.append_unit(
            _make_tool_unit("B", output_lines=("o2",), total_lines=1), ["s2"]
        )
        output.toggle_unit_tier("A")
        output.toggle_unit_tier("B")
        await pilot.pause()
        assert output.effective_tier("A") == "oneline"

        output.set_tool_display_default("compressed")
        await pilot.pause()

        assert output.effective_tier("A") == "compressed"
        assert output.effective_tier("B") == "compressed"
        assert output._tool_tier_overrides == {}


async def test_set_tool_display_default_triggers_rebuild() -> None:
    """Changing the default re-renders the screen, not just the state."""
    app = _RegistryApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one(OutputLog)
        unit = _make_tool_unit("A", output_lines=("o1", "o2"), total_lines=2)
        output.append_unit(unit, ["start"])
        output.toggle_unit_tier("A")  # → oneline
        await pilot.pause()
        before = list(output.rendered_lines)
        assert len(before) == 1

        output.set_tool_display_default("compressed")
        await pilot.pause()
        after = list(output.rendered_lines)

        assert after != before
        assert len(after) > 1


async def test_on_resize_triggers_rebuild() -> None:
    """on_resize re-renders from the registry, picking up unit changes."""
    app = _RegistryApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one(OutputLog)
        output.append_unit(
            _make_tool_unit("A", output_lines=("o1",), total_lines=1), ["s"]
        )
        output.rebuild()
        await pilot.pause()

        # Mutate the stored unit directly (bypassing update_unit_and_rerender)
        # so only a rebuild triggered by on_resize would surface the change.
        import dataclasses

        output._units["A"] = dataclasses.replace(
            output._units["A"], output_lines=("CHANGED",), total_lines=1
        )
        output.on_resize(object())
        await pilot.pause()

        assert any("CHANGED" in ln for ln in output.rendered_lines)


async def test_rebuild_does_not_mutate_recorded() -> None:
    """rebuild() leaves the recorded append-history untouched."""
    app = _RegistryApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one(OutputLog)
        output.append_unit(
            _make_tool_unit("A", output_lines=("o1",), total_lines=1), ["s1", "s2"]
        )
        await pilot.pause()
        before = list(output.recorded_lines)

        output.rebuild()

        assert output.recorded_lines == before


async def test_toggle_for_assistant_turn_unit_noop_or_raise() -> None:
    """Toggling an assistant_turn unit raises ValueError (only tools toggle)."""
    app = _RegistryApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one(OutputLog)
        turn = _make_turn_unit("T")
        output.append_unit(turn, [])
        await pilot.pause()

        with pytest.raises(ValueError):
            output.toggle_unit_tier("T")


async def test_rebuild_with_pending_tool_renders_start_only() -> None:
    """An in-flight tool (no output yet) renders start lines without a footer."""
    app = _RegistryApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one(OutputLog)
        unit = _make_tool_unit("A", output_lines=(), total_lines=0)
        output.append_unit(unit, ["placeholder"])
        await pilot.pause()

        output.rebuild()
        await pilot.pause()
        assert not any("done" in ln for ln in output.rendered_lines)

        output.update_unit_and_rerender(
            "A",
            output_lines=("a", "b"),
            total_lines=2,
            truncated=False,
            duration_ms=42,
            is_error=False,
        )
        await pilot.pause()

        joined = "\n".join(output.rendered_lines)
        assert "done" in joined
        assert "a" in joined
        assert "b" in joined


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
