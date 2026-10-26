from __future__ import annotations

import json
import logging
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

import pytest

from mcp_coder.icoder.core.app_core import AppCore
from mcp_coder.icoder.core.event_log import EventLog
from mcp_coder.icoder.env_setup import RuntimeInfo
from mcp_coder.icoder.services.llm_service import FakeLLMService
from mcp_coder.icoder.ui.app import ICoderApp
from mcp_coder.icoder.ui.widgets.detail_modal import DetailModal
from mcp_coder.icoder.ui.widgets.input_area import InputArea
from mcp_coder.icoder.ui.widgets.output_log import ContentUnit, OutputLog
from mcp_coder.utils.mcp_verification import MCPServerInfo
from tests.icoder.test_app_pilot import _submit_and_wait

pytestmark = pytest.mark.textual_integration


async def test_stream_done_clears_renderer_fifo(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """After StreamDone, the renderer FIFO is empty (cleanup_pending → [])."""
    app = make_icoder_app(responses=[])
    async with app.run_test() as pilot:
        await pilot.pause()
        app._handle_stream_event(
            {
                "type": "tool_use_start",
                "name": "mcp__mcp-workspace__read_file",
                "args": {},
            }
        )
        app._handle_stream_event(
            {
                "type": "tool_result",
                "name": "mcp__mcp-workspace__read_file",
                "output": "o",
            }
        )
        app._handle_stream_event({"type": "done"})
        await pilot.pause()

        assert app._renderer.cleanup_pending() == []


async def test_banner_stays_on_append_text(
    fake_llm: FakeLLMService, event_log: EventLog
) -> None:
    """The startup banner is recorded but registers no clickable unit."""
    info = RuntimeInfo(
        mcp_coder_version="0.42.0",
        mcp_coder_utils_version="0.42.0",
        python_version="3.12.0",
        claude_code_version="1.2.3",
        tool_env_path="/fake/tool",
        project_venv_path="/fake/proj/.venv",
        project_dir="/fake/proj",
        env_vars={},
        mcp_servers=[
            MCPServerInfo(
                name="mcp-tools-py",
                path=Path("/fake/mcp-tools-py"),
                version="1.0",
            ),
        ],
    )
    app = ICoderApp(
        AppCore(llm_service=fake_llm, event_log=event_log, runtime_info=info)
    )
    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one(OutputLog)
        assert any("mcp-coder" in ln for ln in output.recorded_lines)
        # Banner lines are not part of the clickable registry.
        assert output.unit_at_line(0) is None
        assert output._units == {}


async def test_display_oneline_rebuilds_all_tool_units_as_oneline(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """/display oneline rebuilds existing tool blocks as tier-1 oneline."""
    from mcp_coder.icoder.core.commands.display import register_display

    app = make_icoder_app(responses=[])
    async with app.run_test() as pilot:
        register_display(app._core.registry, app._core)
        await pilot.pause()
        app._handle_stream_event(
            {
                "type": "tool_use_start",
                "name": "mcp__mcp-workspace__read_file",
                "args": {"file_path": "x.py"},
            }
        )
        app._handle_stream_event(
            {
                "type": "tool_result",
                "name": "mcp__mcp-workspace__read_file",
                "output": "line1\nline2",
            }
        )
        await pilot.pause()
        output = app.query_one(OutputLog)
        # Default tier is compressed → box-drawing header present.
        assert any("┌" in ln for ln in output.rendered_lines)

        input_area = app.query_one(InputArea)
        input_area.focus()
        await pilot.pause()
        input_area.insert("/display oneline")
        await pilot.press("enter")
        await pilot.pause()

        lines = output.rendered_lines
        # Tool now renders as a single tier-1 gear summary, no box chars.
        assert any("⚙" in ln for ln in lines)
        assert not any("┌" in ln for ln in lines)


async def test_display_compressed_wipes_per_unit_overrides(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """/display compressed discards a manual per-tool oneline override."""
    from mcp_coder.icoder.core.commands.display import register_display

    app = make_icoder_app(responses=[])
    async with app.run_test() as pilot:
        register_display(app._core.registry, app._core)
        await pilot.pause()
        app._handle_stream_event(
            {
                "type": "tool_use_start",
                "name": "mcp__mcp-workspace__read_file",
                "args": {"file_path": "x.py"},
            }
        )
        app._handle_stream_event(
            {
                "type": "tool_result",
                "name": "mcp__mcp-workspace__read_file",
                "output": "line1\nline2",
            }
        )
        await pilot.pause()
        output = app.query_one(OutputLog)
        tool = next(u for u in output._units.values() if u.kind == "tool")
        # Manually flip this one tool to oneline.
        output.toggle_unit_tier(tool.id)
        await pilot.pause()
        assert any("⚙" in ln for ln in output.rendered_lines)

        input_area = app.query_one(InputArea)
        input_area.focus()
        await pilot.pause()
        input_area.insert("/display compressed")
        await pilot.press("enter")
        await pilot.pause()

        lines = output.rendered_lines
        # Override wiped → tool back to compressed (box header present).
        assert any("┌" in ln for ln in lines)


async def test_resumed_divider_is_not_a_unit(
    make_icoder_app: Callable[..., ICoderApp],
    tmp_path: Path,
) -> None:
    """The dim 'Resumed' divider written on resume is not a clickable unit."""
    log_path = tmp_path / "icoder_2026-05-01T10-00-00.jsonl"
    events = [
        {"t": 0.0, "event": "session_start", "provider": "claude"},
        {"t": 0.1, "event": "input_received", "text": "prior"},
    ]
    log_path.write_text(
        "\n".join(json.dumps(ev) for ev in events) + "\n", encoding="utf-8"
    )
    app = make_icoder_app(responses=[])
    async with app.run_test() as pilot:
        await pilot.pause()
        app.do_resume(log_path)
        await pilot.pause()
        output = app.query_one(OutputLog)
        # The divider is in the append history and on screen (it survives
        # rebuild), but it is not a clickable unit (no range covers it).
        assert any("Resumed" in ln for ln in output.recorded_lines)
        assert any("Resumed" in ln for ln in output.rendered_lines)
        divider_line = next(
            i for i, ln in enumerate(output.rendered_lines) if "Resumed" in ln
        )
        assert output.unit_at_line(divider_line) is None


async def test_tool_block_creates_clickable_unit(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """A ToolStart + ToolResult pair becomes a single clickable tool unit."""
    app = make_icoder_app(responses=[])
    async with app.run_test() as pilot:
        await pilot.pause()
        app._handle_stream_event(
            {
                "type": "tool_use_start",
                "name": "mcp__mcp-workspace__read_file",
                "args": {"file_path": "x.py"},
            }
        )
        app._handle_stream_event(
            {
                "type": "tool_result",
                "name": "mcp__mcp-workspace__read_file",
                "output": "line1\nline2",
            }
        )
        await pilot.pause()
        output = app.query_one(OutputLog)
        tool_units = [u for u in output._units.values() if u.kind == "tool"]
        assert len(tool_units) == 1
        assert tool_units[0].output == "line1\nline2"
        # Every rendered line of the block resolves to the one tool unit.
        resolved_ids: set[str] = set()
        for i in range(len(output.rendered_lines)):
            resolved = output.unit_at_line(i)
            if resolved is not None:
                resolved_ids.add(resolved.id)
        assert resolved_ids == {tool_units[0].id}


async def test_assistant_text_creates_clickable_turn(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """Streamed assistant text registers a single clickable turn unit."""
    app = make_icoder_app(responses=[])
    async with app.run_test() as pilot:
        await pilot.pause()
        app._handle_stream_event({"type": "text_delta", "text": "hello\nworld\n"})
        app._handle_stream_event({"type": "done"})
        await pilot.pause()
        output = app.query_one(OutputLog)
        turn_units = [u for u in output._units.values() if u.kind == "assistant_turn"]
        assert len(turn_units) == 1
        assert output.unit_at_line(0) is turn_units[0]
        assert "hello" in output.rendered_lines
        assert "world" in output.rendered_lines


async def test_last_unit_returns_most_recent_inserted_unit_dict_order(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """A mid-turn tool becomes last_unit; later turn text does not change it."""
    app = make_icoder_app(responses=[])
    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one(OutputLog)
        app._handle_stream_event({"type": "text_delta", "text": "before\n"})
        app._handle_stream_event(
            {
                "type": "tool_use_start",
                "name": "mcp__mcp-workspace__read_file",
                "args": {},
            }
        )
        await pilot.pause()
        last = output.last_unit()
        assert last is not None and last.kind == "tool"

        # More turn text arrives, but the tool stays the most-recent unit.
        app._handle_stream_event({"type": "text_delta", "text": "after\n"})
        app._handle_stream_event(
            {
                "type": "tool_result",
                "name": "mcp__mcp-workspace__read_file",
                "output": "out",
            }
        )
        await pilot.pause()
        last = output.last_unit()
        assert last is not None and last.kind == "tool"

        turn_id = next(
            u.id for u in output._units.values() if u.kind == "assistant_turn"
        )
        tool_id = next(u.id for u in output._units.values() if u.kind == "tool")
        turn_ranges = [r for r in output._ranges if r[2] == turn_id]
        tool_ranges = [r for r in output._ranges if r[2] == tool_id]
        assert len(turn_ranges) >= 2
        assert len(tool_ranges) == 1
        # The tool range sits between the turn's range entries.
        assert turn_ranges[0][0] < tool_ranges[0][0] < turn_ranges[-1][0]


async def test_cancel_synthesizes_cancelled_tool_unit(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """An orphaned tool start resolves to a cancelled tool unit."""
    app = make_icoder_app(responses=[])
    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one(OutputLog)
        app._handle_stream_event(
            {
                "type": "tool_use_start",
                "name": "mcp__mcp-workspace__read_file",
                "args": {"file_path": "x.py"},
            }
        )
        await pilot.pause()

        # Simulate the cancel-path orphan cleanup.
        app._cleanup_orphan_tools()
        await pilot.pause()

        tool = next(u for u in output._units.values() if u.kind == "tool")
        assert tool.output == "(cancelled)"
        assert tool.is_error is True
        assert tool.duration_ms is None
        assert any("(cancelled)" in ln for ln in output.rendered_lines)


async def test_same_tool_out_of_order_results_pair_by_run_id(
    make_icoder_app: Callable[..., ICoderApp],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Two calls to the same tool pair by tool_run_id, not by arrival order."""
    app = make_icoder_app(responses=[])
    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one(OutputLog)
        app._handle_stream_event(
            {
                "type": "tool_use_start",
                "name": "mcp__mcp-workspace__read_file",
                "args": {"file_path": "a.py"},
                "tool_run_id": "run-a",
            }
        )
        app._handle_stream_event(
            {
                "type": "tool_use_start",
                "name": "mcp__mcp-workspace__read_file",
                "args": {"file_path": "b.py"},
                "tool_run_id": "run-b",
            }
        )
        with caplog.at_level(logging.WARNING):
            # The gated call (a) resolves *after* the ungated one (b).
            app._handle_stream_event(
                {
                    "type": "tool_result",
                    "name": "mcp__mcp-workspace__read_file",
                    "output": "b output",
                    "tool_run_id": "run-b",
                }
            )
            app._handle_stream_event(
                {
                    "type": "tool_result",
                    "name": "mcp__mcp-workspace__read_file",
                    "output": "a output",
                    "tool_run_id": "run-a",
                }
            )
        await pilot.pause()

        tool_units = [u for u in output._units.values() if u.kind == "tool"]
        assert len(tool_units) == 2
        by_arg = {(u.args or {})["file_path"]: u for u in tool_units}
        assert by_arg["a.py"].output == "a output"
        assert by_arg["b.py"].output == "b output"
        assert "desync" not in caplog.text


async def test_cancel_resolves_the_open_same_name_unit(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """Orphan cleanup cancels the still-open unit, not the completed one."""
    app = make_icoder_app(responses=[])
    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one(OutputLog)
        app._handle_stream_event(
            {
                "type": "tool_use_start",
                "name": "mcp__mcp-workspace__read_file",
                "args": {"file_path": "a.py"},
                "tool_run_id": "run-a",
            }
        )
        app._handle_stream_event(
            {
                "type": "tool_use_start",
                "name": "mcp__mcp-workspace__read_file",
                "args": {"file_path": "b.py"},
                "tool_run_id": "run-b",
            }
        )
        app._handle_stream_event(
            {
                "type": "tool_result",
                "name": "mcp__mcp-workspace__read_file",
                "output": "a output",
                "tool_run_id": "run-a",
            }
        )
        await pilot.pause()

        # Cancel while the second (same-name) call is still open.
        app._cleanup_orphan_tools()
        await pilot.pause()

        by_arg = {
            (u.args or {})["file_path"]: u
            for u in output._units.values()
            if u.kind == "tool"
        }
        assert by_arg["a.py"].output == "a output"
        assert by_arg["a.py"].is_error is False
        assert by_arg["b.py"].output == "(cancelled)"
        assert by_arg["b.py"].is_error is True


def _make_click_tool_unit(
    unit_id: str = "A",
    *,
    output_lines: tuple[str, ...] = (),
    total_lines: int = 0,
) -> ContentUnit:
    """Build a tool ContentUnit for click / F2 pilot tests."""
    return ContentUnit(
        id=unit_id,
        kind="tool",
        timestamp=datetime(2026, 6, 24, 12, 0, 0),
        tool_name="read_file",
        args={"path": "src/main.py"},
        output_lines=output_lines,
        total_lines=total_lines,
    )


async def test_f2_with_no_content_is_silent_noop(icoder_app: ICoderApp) -> None:
    """Pressing F2 with no registered units does nothing (no modal, no crash)."""
    async with icoder_app.run_test() as pilot:
        await pilot.pause()

        await pilot.press("f2")
        await pilot.pause()

        assert len(icoder_app.screen_stack) == 1
        assert icoder_app.is_running


async def test_f2_opens_modal_for_last_unit(icoder_app: ICoderApp) -> None:
    """Pressing F2 opens a DetailModal for the most recent unit."""
    async with icoder_app.run_test() as pilot:
        await pilot.pause()
        output = icoder_app.query_one(OutputLog)
        output.append_unit(_make_click_tool_unit("A"), ["line1"])
        await pilot.pause()

        await pilot.press("f2")
        await pilot.pause()

        assert isinstance(icoder_app.screen, DetailModal)


async def test_double_click_emits_content_detail_opened_event(
    icoder_app: ICoderApp, event_log: EventLog
) -> None:
    """A pilot double click on a unit emits content_detail_opened."""
    async with icoder_app.run_test() as pilot:
        await pilot.pause()
        output = icoder_app.query_one(OutputLog)
        output.append_unit(_make_click_tool_unit("A"), ["line1"])
        await pilot.pause()

        await pilot.click(OutputLog, offset=(0, 0), times=2)
        await pilot.pause()

        events = [entry.event for entry in event_log.entries]
        assert "content_detail_opened" in events


async def test_single_click_emits_tool_tier_toggled_event(
    icoder_app: ICoderApp, event_log: EventLog
) -> None:
    """A pilot single click on a tool unit emits tool_tier_toggled after debounce."""
    async with icoder_app.run_test() as pilot:
        await pilot.pause()
        output = icoder_app.query_one(OutputLog)
        output.append_unit(
            _make_click_tool_unit("A", output_lines=("o1",), total_lines=1), ["s"]
        )
        await pilot.pause()

        await pilot.click(OutputLog, offset=(0, 0))
        await pilot.pause(0.6)

        events = [entry.event for entry in event_log.entries]
        assert "tool_tier_toggled" in events


async def test_user_input_creates_clickable_unit(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """Submitting input registers a clickable user_input unit at its line."""
    app = make_icoder_app(responses=[[{"type": "done"}]])
    async with app.run_test() as pilot:
        await _submit_and_wait(app, pilot, text="hello there")
        output = app.query_one(OutputLog)
        unit = output.unit_at_line(0)
        assert unit is not None
        assert unit.kind == "user_input"
        assert unit.full_text == "hello there"
