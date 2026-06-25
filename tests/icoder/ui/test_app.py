"""End-to-end pipeline tests for tool output visibility in ICoderApp."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

import pytest
from textual.widgets import Static

from mcp_coder.icoder.core.event_log import EventLog
from mcp_coder.icoder.env_setup import RuntimeInfo
from mcp_coder.icoder.ui.app import ICoderApp
from mcp_coder.icoder.ui.widgets.busy_indicator import BusyIndicator
from mcp_coder.icoder.ui.widgets.input_area import InputArea
from mcp_coder.icoder.ui.widgets.output_log import OutputLog
from mcp_coder.icoder.ui.widgets.session_picker import SessionPickerScreen
from mcp_coder.llm.types import StreamEvent

pytestmark = pytest.mark.textual_integration


async def test_tool_output_list_directory(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """List directory tool output lines appear in the rendered screen."""
    app = make_icoder_app(responses=[])
    async with app.run_test() as pilot:
        await pilot.pause()
        app._handle_stream_event(
            {
                "type": "tool_use_start",
                "name": "mcp__mcp-workspace__list_directory",
                "args": {},
            }
        )
        app._handle_stream_event(
            {
                "type": "tool_result",
                "name": "mcp__mcp-workspace__list_directory",
                "output": '{"result": ["file1.py", "file2.py", "src/"]}',
            }
        )
        lines = app.query_one(OutputLog).rendered_lines
        joined = "\n".join(lines)
        assert "file1.py" in joined
        assert "file2.py" in joined
        assert "src/" in joined
        assert "└ done" in joined


async def test_tool_output_read_file(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """Read file tool output lines appear in the rendered screen."""
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
                "output": '{"result": "line1\\nline2\\nline3"}',
            }
        )
        lines = app.query_one(OutputLog).rendered_lines
        joined = "\n".join(lines)
        assert "line1" in joined
        assert "line2" in joined
        assert "line3" in joined
        assert "└ done" in joined


async def test_tool_output_truncated(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """Truncated tool output shows truncation marker."""
    long_content = "\\n".join(f"line{i}" for i in range(30))
    app = make_icoder_app(responses=[])
    async with app.run_test() as pilot:
        await pilot.pause()
        app._handle_stream_event(
            {
                "type": "tool_use_start",
                "name": "mcp__mcp-workspace__read_file",
                "args": {"file_path": "big.py"},
            }
        )
        app._handle_stream_event(
            {
                "type": "tool_result",
                "name": "mcp__mcp-workspace__read_file",
                "output": '{"result": "' + long_content + '"}',
            }
        )
        lines = app.query_one(OutputLog).rendered_lines
        joined = "\n".join(lines)
        assert "truncated" in joined
        assert "skipped" in joined


async def test_tool_output_empty(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """Empty tool output still shows done footer."""
    app = make_icoder_app(responses=[])
    async with app.run_test() as pilot:
        await pilot.pause()
        app._handle_stream_event(
            {
                "type": "tool_use_start",
                "name": "mcp__mcp-workspace__read_file",
                "args": {"file_path": "empty.py"},
            }
        )
        app._handle_stream_event(
            {
                "type": "tool_result",
                "name": "mcp__mcp-workspace__read_file",
                "output": "",
            }
        )
        lines = app.query_one(OutputLog).rendered_lines
        joined = "\n".join(lines)
        assert "└ done" in joined


async def test_busy_indicator_thinking_after_tool_result(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """Busy indicator shows 'Thinking about ...' after tool result is rendered."""
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
                "output": '{"result": "hello"}',
            }
        )
        indicator = app.query_one(BusyIndicator)
        assert "Thinking about mcp-workspace > read_file..." in indicator.label_text


async def test_banner_renders_mcp_coder_utils_version(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """on_mount banner includes the mcp-coder-utils version line."""
    runtime_info = RuntimeInfo(
        mcp_coder_version="9.9.9",
        mcp_coder_utils_version="1.2.3",
        python_version="3.12.0",
        claude_code_version="unknown",
        tool_env_path="/tmp/tool-env",
        project_venv_path="/tmp/proj-venv",
        project_dir="/tmp/proj",
        env_vars={},
        mcp_servers=[],
    )
    app = make_icoder_app(responses=[], runtime_info=runtime_info)
    async with app.run_test() as pilot:
        await pilot.pause()
        joined = "\n".join(app.query_one(OutputLog).recorded_lines)
        assert any(
            line.startswith("mcp-coder-utils 1.2.3") for line in joined.splitlines()
        ), joined


async def test_busy_indicator_resets_on_error_only_stream(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """Busy indicator shows ready after stream yields only an error event (no done)."""
    error_only: list[list[StreamEvent]] = [
        [{"type": "error", "message": "something went wrong"}],
    ]
    app = make_icoder_app(responses=error_only)
    async with app.run_test() as pilot:
        # Type input and press enter to trigger _stream_llm
        await pilot.press("h", "i")
        await pilot.press("enter")
        # Allow the background worker to finish
        await pilot.pause(delay=0.5)
        indicator = app.query_one(BusyIndicator)
        assert indicator.label_text == "✓ Ready"


async def test_status_version_label_has_mcp_coder_prefix(
    make_icoder_app: Callable[..., ICoderApp],
    tmp_path: Path,
) -> None:
    """Status-bar version label is prefixed with 'mcp-coder '."""
    runtime_info = RuntimeInfo(
        mcp_coder_version="9.9.9",
        mcp_coder_utils_version="1.2.3",
        python_version="3.12.0",
        claude_code_version="unknown",
        tool_env_path="/tmp/tool-env",
        project_venv_path="/tmp/proj-venv",
        project_dir=str(tmp_path),
        env_vars={},
        mcp_servers=[],
    )
    app = make_icoder_app(runtime_info=runtime_info)
    async with app.run_test() as pilot:
        await pilot.pause()
        widget = app.query_one("#status-version", Static)
        assert "mcp-coder v9.9.9" in str(widget.render())


# --- /load command + do_resume + open_picker_for_load ---


def _write_log(path: Path, events: list[dict[str, object]]) -> None:
    """Write a JSONL log file with the given events."""
    lines = [json.dumps(ev) for ev in events]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


async def test_do_resume_clears_replays_and_renders_divider_and_banner(
    make_icoder_app: Callable[..., ICoderApp],
    tmp_path: Path,
) -> None:
    """do_resume clears, replays a fixture, then renders Resumed + banner."""
    log_path = tmp_path / "icoder_2026-05-01T10-00-00.jsonl"
    _write_log(
        log_path,
        [
            {"t": 0.0, "event": "session_start", "provider": "claude"},
            {"t": 0.1, "event": "input_received", "text": "old prompt"},
            {"t": 0.2, "event": "llm_request_start", "text": "old prompt"},
            {
                "t": 0.3,
                "event": "stream_event",
                "type": "text_delta",
                "text": "old reply",
            },
            {"t": 0.4, "event": "stream_event", "type": "done"},
            {"t": 0.5, "event": "llm_request_end"},
        ],
    )
    runtime_info = RuntimeInfo(
        mcp_coder_version="9.9.9",
        mcp_coder_utils_version="1.2.3",
        python_version="3.12.0",
        claude_code_version="unknown",
        tool_env_path="/tmp/tool-env",
        project_venv_path="/tmp/proj-venv",
        project_dir=str(tmp_path),
        env_vars={},
        mcp_servers=[],
    )
    app = make_icoder_app(responses=[], runtime_info=runtime_info)
    async with app.run_test() as pilot:
        await pilot.pause()
        # Pre-existing output we expect to be cleared by do_resume:
        output = app.query_one(OutputLog)
        output.append_text("LIVE LINE BEFORE RESUME")
        await pilot.pause()
        app.do_resume(log_path)
        await pilot.pause()
        joined = "\n".join(output.recorded_lines)
        # Old live line was wiped by output.clear()
        assert "LIVE LINE BEFORE RESUME" not in joined
        # Replay rendered prior input + reply
        assert "> old prompt" in joined
        assert "old reply" in joined
        # Resumed divider rendered
        assert "Resumed" in joined
        # Live banner re-rendered (mcp-coder version line)
        assert "mcp-coder 9.9.9" in joined


async def test_do_resume_order_replay_before_divider_before_banner(
    make_icoder_app: Callable[..., ICoderApp],
    tmp_path: Path,
) -> None:
    """Resumed divider appears between replay output and the live banner."""
    log_path = tmp_path / "icoder_2026-05-01T10-00-00.jsonl"
    _write_log(
        log_path,
        [
            {"t": 0.0, "event": "session_start", "provider": "claude"},
            {"t": 0.1, "event": "input_received", "text": "the prior turn"},
        ],
    )
    runtime_info = RuntimeInfo(
        mcp_coder_version="9.9.9",
        mcp_coder_utils_version="1.2.3",
        python_version="3.12.0",
        claude_code_version="unknown",
        tool_env_path="/tmp/tool-env",
        project_venv_path="/tmp/proj-venv",
        project_dir=str(tmp_path),
        env_vars={},
        mcp_servers=[],
    )
    app = make_icoder_app(responses=[], runtime_info=runtime_info)
    async with app.run_test() as pilot:
        await pilot.pause()
        app.do_resume(log_path)
        await pilot.pause()
        lines = app.query_one(OutputLog).recorded_lines
        joined = "\n".join(lines)
        # Find positions
        replay_pos = joined.find("> the prior turn")
        divider_pos = joined.find("Resumed")
        banner_pos = joined.rfind("mcp-coder 9.9.9")
        assert -1 < replay_pos < divider_pos < banner_pos


async def test_open_picker_for_load_with_no_logs_renders_message(
    make_icoder_app: Callable[..., ICoderApp],
    tmp_path: Path,
) -> None:
    """`/load` with empty logs dir renders message and does not push a picker."""
    runtime_info = RuntimeInfo(
        mcp_coder_version="9.9.9",
        mcp_coder_utils_version="1.2.3",
        python_version="3.12.0",
        claude_code_version="unknown",
        tool_env_path="/tmp/tool-env",
        project_venv_path="/tmp/proj-venv",
        project_dir=str(tmp_path),
        env_vars={},
        mcp_servers=[],
    )
    app = make_icoder_app(responses=[], runtime_info=runtime_info)
    async with app.run_test() as pilot:
        await pilot.pause()
        screen_count_before = len(app.screen_stack)
        app.open_picker_for_load()
        await pilot.pause()
        joined = "\n".join(app.query_one(OutputLog).recorded_lines)
        assert "No previous sessions in this project." in joined
        # No new screen pushed
        assert len(app.screen_stack) == screen_count_before


async def test_load_input_with_no_logs_does_not_push_picker(
    make_icoder_app: Callable[..., ICoderApp],
    tmp_path: Path,
) -> None:
    """Submitting `/load` without any prior logs renders message; no picker."""
    runtime_info = RuntimeInfo(
        mcp_coder_version="9.9.9",
        mcp_coder_utils_version="1.2.3",
        python_version="3.12.0",
        claude_code_version="unknown",
        tool_env_path="/tmp/tool-env",
        project_venv_path="/tmp/proj-venv",
        project_dir=str(tmp_path),
        env_vars={},
        mcp_servers=[],
    )
    app = make_icoder_app(responses=[], runtime_info=runtime_info)
    async with app.run_test() as pilot:
        await pilot.pause()
        screen_count_before = len(app.screen_stack)
        input_area = app.query_one(InputArea)
        input_area.focus()
        await pilot.pause()
        input_area.insert("/load")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        joined = "\n".join(app.query_one(OutputLog).recorded_lines)
        assert "No previous sessions in this project." in joined
        assert len(app.screen_stack) == screen_count_before


async def test_open_picker_for_load_with_logs_pushes_picker(
    make_icoder_app: Callable[..., ICoderApp],
    tmp_path: Path,
) -> None:
    """`/load` with a fixture log pushes SessionPickerScreen."""
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    log_path = logs_dir / "icoder_2026-05-01T10-00-00.jsonl"
    _write_log(
        log_path,
        [
            {"t": 0.0, "event": "session_start", "provider": "claude"},
            {"t": 0.1, "event": "input_received", "text": "hello"},
        ],
    )
    runtime_info = RuntimeInfo(
        mcp_coder_version="9.9.9",
        mcp_coder_utils_version="1.2.3",
        python_version="3.12.0",
        claude_code_version="unknown",
        tool_env_path="/tmp/tool-env",
        project_venv_path="/tmp/proj-venv",
        project_dir=str(tmp_path),
        env_vars={},
        mcp_servers=[],
    )
    app = make_icoder_app(responses=[], runtime_info=runtime_info)
    async with app.run_test() as pilot:
        await pilot.pause()
        app.open_picker_for_load()
        await pilot.pause()
        # SessionPickerScreen now on top of the stack
        assert isinstance(app.screen, SessionPickerScreen)


async def test_open_picker_escape_does_not_change_state(
    make_icoder_app: Callable[..., ICoderApp],
    tmp_path: Path,
) -> None:
    """Esc on the picker closes it without changing session_id, output, or path."""
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    log_path = logs_dir / "icoder_2026-05-01T10-00-00.jsonl"
    _write_log(
        log_path,
        [
            {"t": 0.0, "event": "session_start", "provider": "claude"},
            {"t": 0.1, "event": "input_received", "text": "hello"},
        ],
    )
    runtime_info = RuntimeInfo(
        mcp_coder_version="9.9.9",
        mcp_coder_utils_version="1.2.3",
        python_version="3.12.0",
        claude_code_version="unknown",
        tool_env_path="/tmp/tool-env",
        project_venv_path="/tmp/proj-venv",
        project_dir=str(tmp_path),
        env_vars={},
        mcp_servers=[],
    )
    app = make_icoder_app(responses=[], runtime_info=runtime_info)
    async with app.run_test() as pilot:
        await pilot.pause()
        sid_before = app._core.session_id
        log_path_before = app._core.event_log.current_path
        recorded_before = list(app.query_one(OutputLog).recorded_lines)
        app.open_picker_for_load()
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
        # No state change
        assert app._core.session_id == sid_before
        assert app._core.event_log.current_path == log_path_before
        assert app.query_one(OutputLog).recorded_lines == recorded_before


# --- resume_log_path startup behavior (Step 11) ---


async def test_on_mount_with_resume_log_path_triggers_do_resume(
    event_log: EventLog,
    tmp_path: Path,
) -> None:
    """When ICoderApp is constructed with resume_log_path, on_mount calls do_resume."""
    from mcp_coder.icoder.core.app_core import AppCore
    from mcp_coder.icoder.services.llm_service import FakeLLMService

    log_path = tmp_path / "icoder_2026-05-01T10-00-00.jsonl"
    _write_log(
        log_path,
        [
            {"t": 0.0, "event": "session_start", "provider": "claude"},
            {"t": 0.1, "event": "input_received", "text": "old prompt"},
            {"t": 0.2, "event": "llm_request_start", "text": "old prompt"},
            {
                "t": 0.3,
                "event": "stream_event",
                "type": "text_delta",
                "text": "old reply",
            },
            {"t": 0.4, "event": "stream_event", "type": "done"},
            {"t": 0.5, "event": "llm_request_end"},
        ],
    )
    runtime_info = RuntimeInfo(
        mcp_coder_version="9.9.9",
        mcp_coder_utils_version="1.2.3",
        python_version="3.12.0",
        claude_code_version="unknown",
        tool_env_path="/tmp/tool-env",
        project_venv_path="/tmp/proj-venv",
        project_dir=str(tmp_path),
        env_vars={},
        mcp_servers=[],
    )
    app = ICoderApp(
        AppCore(
            llm_service=FakeLLMService(responses=[]),
            event_log=event_log,
            runtime_info=runtime_info,
        ),
        resume_log_path=log_path,
    )
    async with app.run_test() as pilot:
        await pilot.pause()
        joined = "\n".join(app.query_one(OutputLog).recorded_lines)
        # do_resume effects: prior input is replayed
        assert "> old prompt" in joined
        assert "old reply" in joined
        # Resumed divider rendered
        assert "Resumed" in joined
        # Live banner re-rendered after divider
        assert "mcp-coder 9.9.9" in joined


async def test_do_resume_re_records_events_into_new_log(
    make_icoder_app: Callable[..., ICoderApp],
    tmp_path: Path,
) -> None:
    """do_resume re-records replayed events into the rotated event log file."""
    log_path = tmp_path / "icoder_2026-05-01T10-00-00.jsonl"
    _write_log(
        log_path,
        [
            {"t": 0.0, "event": "session_start", "provider": "claude"},
            {"t": 0.1, "event": "input_received", "text": "hello"},
            {"t": 0.2, "event": "llm_request_start", "text": "hello"},
            {
                "t": 0.3,
                "event": "stream_event",
                "type": "text_delta",
                "text": "hi",
            },
            {"t": 0.4, "event": "stream_event", "type": "done"},
            {"t": 0.5, "event": "llm_request_end"},
        ],
    )
    runtime_info = RuntimeInfo(
        mcp_coder_version="9.9.9",
        mcp_coder_utils_version="1.2.3",
        python_version="3.12.0",
        claude_code_version="unknown",
        tool_env_path="/tmp/tool-env",
        project_venv_path="/tmp/proj-venv",
        project_dir=str(tmp_path),
        env_vars={},
        mcp_servers=[],
    )
    app = make_icoder_app(responses=[], runtime_info=runtime_info)
    async with app.run_test() as pilot:
        await pilot.pause()
        app.do_resume(log_path)
        await pilot.pause()
        new_log_path = app._core.event_log.current_path
        # Read the new log to confirm replay events were re-emitted.
        from mcp_coder.icoder.core.event_log import iter_events

        events_in_new = list(iter_events(new_log_path))
        kinds = [e.get("event") for e in events_in_new]
        # The rotated log starts with a freshly-emitted session_start
        # (so the picker can see it); the source log's session_start is
        # NOT replayed. Other replayed events ARE re-emitted.
        assert kinds[0] == "session_start"
        assert events_in_new[0].get("provider") == "claude"
        assert kinds.count("session_start") == 1
        assert "input_received" in kinds
        assert "stream_event" in kinds
