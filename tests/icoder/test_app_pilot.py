"""Textual pilot integration tests for ICoderApp."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from textual.pilot import Pilot
from textual.widgets import Static

from mcp_coder.icoder.core.app_core import AppCore
from mcp_coder.icoder.core.event_log import EventLog
from mcp_coder.icoder.env_setup import RuntimeInfo
from mcp_coder.icoder.permissions.approval import ApprovalDecision, ApprovalEngine
from mcp_coder.icoder.permissions.model import Matcher, PermissionFrame
from mcp_coder.icoder.permissions.skill_frame import SkillFrame
from mcp_coder.icoder.services.llm_service import FakeLLMService
from mcp_coder.icoder.ui.app import ICoderApp
from mcp_coder.icoder.ui.widgets.approval_modal import ApprovalModal
from mcp_coder.icoder.ui.widgets.input_area import InputArea
from mcp_coder.icoder.ui.widgets.output_log import OutputLog
from mcp_coder.llm.types import StreamEvent
from mcp_coder.utils.mcp_verification import ClaudeMCPStatus, MCPServerInfo

pytestmark = pytest.mark.textual_integration


async def test_app_launches(icoder_app: ICoderApp) -> None:
    """App launches without error."""
    async with icoder_app.run_test():
        assert icoder_app.is_running


async def test_input_focused_on_startup(icoder_app: ICoderApp) -> None:
    """Input area is focused on startup."""
    async with icoder_app.run_test() as pilot:
        await pilot.pause()
        focused = icoder_app.focused
        assert isinstance(focused, InputArea)


async def test_layout_structure(icoder_app: ICoderApp) -> None:
    """Output area is above input area."""
    async with icoder_app.run_test() as pilot:
        await pilot.pause()
        output = icoder_app.query_one(OutputLog)
        input_area = icoder_app.query_one(InputArea)
        assert output.region.y < input_area.region.y


async def test_submit_text(icoder_app: ICoderApp) -> None:
    """Typed text + Enter echoes to output and clears input."""
    async with icoder_app.run_test() as pilot:
        input_area = icoder_app.query_one(InputArea)
        input_area.focus()
        await pilot.pause()
        input_area.insert("hello world")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        output = icoder_app.query_one(OutputLog)
        assert "> hello world" in output.recorded_lines
        assert input_area.text == ""


async def test_clear_command(icoder_app: ICoderApp) -> None:
    """/clear command clears the output log."""
    async with icoder_app.run_test() as pilot:
        input_area = icoder_app.query_one(InputArea)
        input_area.focus()
        await pilot.pause()
        # First send /help to get some output
        input_area.insert("/help")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        # Then clear
        input_area.insert("/clear")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        output = icoder_app.query_one(OutputLog)
        assert len(output.recorded_lines) == 0


async def test_quit_command(icoder_app: ICoderApp) -> None:
    """/quit command exits the app."""
    async with icoder_app.run_test() as pilot:
        input_area = icoder_app.query_one(InputArea)
        input_area.focus()
        await pilot.pause()
        input_area.insert("/quit")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
    assert not icoder_app.is_running


async def test_shift_enter_newline(icoder_app: ICoderApp) -> None:
    """Shift-Enter inserts newline without submitting."""
    async with icoder_app.run_test() as pilot:
        input_area = icoder_app.query_one(InputArea)
        input_area.focus()
        await pilot.pause()
        input_area.insert("line1")
        await pilot.pause()
        await pilot.press("shift+enter")
        await pilot.pause()
        input_area.insert("line2")
        await pilot.pause()
        assert "\n" in input_area.text


async def _submit_and_wait(
    app: ICoderApp, pilot: Pilot[Any], text: str = "test"
) -> None:
    """Helper: focus input, type text, press enter, wait for worker."""
    input_area = app.query_one(InputArea)
    input_area.focus()
    await pilot.pause()
    input_area.insert(text)
    await pilot.press("enter")
    await pilot.pause(delay=0.5)


async def test_tui_renders_runtime_info_on_mount(
    fake_llm: FakeLLMService, event_log: EventLog
) -> None:
    """TUI output log shows runtime info on mount when RuntimeInfo is provided."""
    info = RuntimeInfo(
        mcp_coder_version="0.42.0",
        mcp_coder_utils_version="0.42.0",
        python_version="3.12.0",
        claude_code_version="1.2.3",
        tool_env_path="/fake/tool",
        project_venv_path="/fake/proj/.venv",
        project_dir="/fake/proj",
        env_vars={"MCP_CODER_VENV_PATH": "/fake/bin"},
        mcp_servers=[
            MCPServerInfo(
                name="mcp-tools-py",
                path=Path("/fake/mcp-tools-py"),
                version="1.0",
            ),
        ],
    )
    app_core = AppCore(llm_service=fake_llm, event_log=event_log, runtime_info=info)
    app = ICoderApp(app_core)

    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one(OutputLog)
        recorded = output.recorded_lines
        assert len(recorded) >= 1
        text = recorded[0]
        assert "mcp-coder 0.42.0" in text
        assert "mcp-tools-py 1.0" in text
        assert "Tool env:" in text
        assert "Project env:" in text
        assert "Project dir:" in text


async def test_on_mount_shows_connection_status(
    fake_llm: FakeLLMService, event_log: EventLog
) -> None:
    """on_mount() renders inline connection status when mcp_connection_status is set."""
    info = RuntimeInfo(
        mcp_coder_version="0.42.0",
        mcp_coder_utils_version="0.42.0",
        python_version="3.12.0",
        claude_code_version="1.2.3",
        tool_env_path="/fake/tool",
        project_venv_path="/fake/proj/.venv",
        project_dir="/fake/proj",
        env_vars={"MCP_CODER_VENV_PATH": "/fake/bin"},
        mcp_servers=[
            MCPServerInfo(
                name="mcp-tools-py",
                path=Path("/fake/mcp-tools-py"),
                version="1.0",
            ),
        ],
        mcp_connection_status=[
            ClaudeMCPStatus(name="mcp-tools-py", status_text="Connected", ok=True),
        ],
    )
    app_core = AppCore(llm_service=fake_llm, event_log=event_log, runtime_info=info)
    app = ICoderApp(app_core)

    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one(OutputLog)
        text = output.recorded_lines[0]
        assert "\u2713 Connected" in text
        assert "mcp-tools-py 1.0" in text


async def test_on_mount_no_connection_status_falls_back(
    fake_llm: FakeLLMService, event_log: EventLog
) -> None:
    """on_mount() with mcp_connection_status=None shows version-only (no crash)."""
    info = RuntimeInfo(
        mcp_coder_version="0.42.0",
        mcp_coder_utils_version="0.42.0",
        python_version="3.12.0",
        claude_code_version="1.2.3",
        tool_env_path="/fake/tool",
        project_venv_path="/fake/proj/.venv",
        project_dir="/fake/proj",
        env_vars={"MCP_CODER_VENV_PATH": "/fake/bin"},
        mcp_servers=[
            MCPServerInfo(
                name="mcp-tools-py",
                path=Path("/fake/mcp-tools-py"),
                version="1.0",
            ),
        ],
        mcp_connection_status=None,
    )
    app_core = AppCore(llm_service=fake_llm, event_log=event_log, runtime_info=info)
    app = ICoderApp(app_core)

    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one(OutputLog)
        text = output.recorded_lines[0]
        assert "mcp-tools-py 1.0" in text
        assert "\u2713" not in text
        assert "\u2717" not in text


# --- Status bar widget tests ---


async def test_status_bar_visible_on_startup(icoder_app: ICoderApp) -> None:
    """Status bar is visible with all three zones on startup."""
    async with icoder_app.run_test() as pilot:
        await pilot.pause()
        tokens = icoder_app.query_one("#status-tokens", Static)
        version = icoder_app.query_one("#status-version", Static)
        hint = icoder_app.query_one("#status-hint", Static)
        assert not tokens.has_class("hidden")
        assert version is not None
        assert hint is not None


async def test_status_bar_always_visible_when_typing(icoder_app: ICoderApp) -> None:
    """Status bar stays visible when input area has text (no hide-on-type)."""
    async with icoder_app.run_test() as pilot:
        input_area = icoder_app.query_one(InputArea)
        input_area.focus()
        await pilot.pause()
        input_area.insert("some text")
        await pilot.pause()
        hint = icoder_app.query_one("#status-hint", Static)
        version = icoder_app.query_one("#status-version", Static)
        assert hint is not None
        assert version is not None


async def test_token_display_updates_after_stream_with_usage(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """After stream with usage data, #status-tokens shows formatted counts."""
    app = make_icoder_app(
        responses=[
            [
                {"type": "text_delta", "text": "hello"},
                {
                    "type": "done",
                    "usage": {"input_tokens": 1200, "output_tokens": 800},
                },
            ]
        ]
    )
    async with app.run_test() as pilot:
        await _submit_and_wait(app, pilot)
        token_widget = app.query_one("#status-tokens", Static)
        # Use update() content via _content (internal) or render to string
        rendered = token_widget.render()
        text = str(rendered)
        assert "\u21931.2k" in text
        assert "\u2191800" in text
        assert not token_widget.has_class("hidden")


async def test_token_display_hidden_after_stream_without_usage(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """After stream without usage data, #status-tokens is hidden."""
    app = make_icoder_app(
        responses=[
            [
                {"type": "text_delta", "text": "hello"},
                {"type": "done"},
            ]
        ]
    )
    async with app.run_test() as pilot:
        await _submit_and_wait(app, pilot)
        token_widget = app.query_one("#status-tokens", Static)
        assert token_widget.has_class("hidden")


# --- Step 3: skill_name threading + permission_warning render ---


async def test_ui_worker_threads_skill_name_to_service(
    event_log: EventLog,
) -> None:
    """Submitting a skill command threads its frame to the LLM service.

    A command yielding ``SendToLLM(text="", skill_name=...)`` must resolve the
    skill's frame from the ``skill_frames`` snapshot and reach
    ``FakeLLMService.last_frame`` via the UI worker.
    """
    from mcp_coder.icoder.core.types import Command, Response, SendToLLM

    fake = FakeLLMService(responses=[[{"type": "done"}]])
    frame = PermissionFrame(base="inherit", allow=(Matcher("srv", "a"),))
    app = ICoderApp(
        AppCore(
            llm_service=fake,
            event_log=event_log,
            skill_frames={"tooled": SkillFrame(frame=frame)},
        )
    )
    app._core.registry.add_command(
        Command(
            name="/tooled",
            description="tooled skill",
            handler=lambda args: Response(
                actions=(SendToLLM(text="", skill_name="tooled"),)
            ),
        )
    )
    async with app.run_test() as pilot:
        await _submit_and_wait(app, pilot, text="/tooled")
        assert fake.last_frame is frame


async def test_permission_warning_event_renders_message_text(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """A permission_warning stream event renders its message in the output log."""
    app = make_icoder_app(responses=[])
    async with app.run_test() as pilot:
        await pilot.pause()
        app._handle_stream_event(
            {"type": "permission_warning", "message": "dropped mcp__srv__*"}
        )
        await pilot.pause()
        output = app.query_one(OutputLog)
        assert "dropped mcp__srv__*" in output.recorded_lines


# --- Step 5: startup permission notices (broken skills + degraded config) ---


async def test_startup_surfaces_both_notice_kinds(
    fake_llm: FakeLLMService, event_log: EventLog
) -> None:
    """Startup renders both a degraded-config line and a broken-skill line (#1061).

    Exercises the on_mount render path (not just the pure formatter + AppCore
    properties). ``runtime_info`` is None here, so the notices appearing proves
    they are rendered OUTSIDE the ``elif self._core.runtime_info`` banner branch.
    """
    core = AppCore(
        llm_service=fake_llm,
        event_log=event_log,
        skill_frames={
            "BrokenSkill": SkillFrame(
                frame=PermissionFrame(base="none"),
                blocked_reason="bad tools block",
            )
        },
        permission_degraded=True,
    )
    app = ICoderApp(core)
    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one(OutputLog)
        text = "\n".join(output.recorded_lines)
        # Both failure kinds surfaced; the skill is lower-cased to its command.
        assert "degraded" in text
        assert "/brokenskill is disabled: bad tools block" in text


async def test_startup_no_notices_when_healthy(
    fake_llm: FakeLLMService, event_log: EventLog
) -> None:
    """A healthy startup (no degraded config, no broken skill) renders no notices."""
    core = AppCore(
        llm_service=fake_llm,
        event_log=event_log,
        skill_frames={"ok": SkillFrame(frame=PermissionFrame(base="inherit"))},
        permission_degraded=False,
    )
    app = ICoderApp(core)
    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one(OutputLog)
        text = "\n".join(output.recorded_lines)
        assert "degraded" not in text
        assert "is disabled" not in text


async def test_resume_path_skips_startup_notices(
    fake_llm: FakeLLMService, event_log: EventLog, tmp_path: Path
) -> None:
    """The resume path skips startup permission notices (fresh-start only, #1061)."""
    log_path = tmp_path / "icoder_2026-05-01T10-00-00.jsonl"
    events = [
        {"t": 0.0, "event": "session_start", "provider": "claude"},
        {"t": 0.1, "event": "input_received", "text": "prior"},
    ]
    log_path.write_text(
        "\n".join(json.dumps(ev) for ev in events) + "\n", encoding="utf-8"
    )
    core = AppCore(
        llm_service=fake_llm,
        event_log=event_log,
        skill_frames={
            "brokenskill": SkillFrame(
                frame=PermissionFrame(base="none"),
                blocked_reason="bad tools block",
            )
        },
        permission_degraded=True,
    )
    app = ICoderApp(core, resume_log_path=log_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one(OutputLog)
        text = "\n".join(output.recorded_lines)
        assert "degraded" not in text
        assert "is disabled" not in text


_APPROVAL_TOOL = "mcp__srv__do_it"


def _approval_event(
    approval_id: str = "a1", tool_name: str = _APPROVAL_TOOL
) -> StreamEvent:
    """Build the ``approval_request`` event the engine would emit for the tool."""
    return {
        "type": "approval_request",
        "approval_id": approval_id,
        "tool_name": tool_name,
        "args": {"path": "a.txt"},
        "source": "project",
    }


class _RecordingEngine(ApprovalEngine):
    """Engine stub recording what the UI sends it (subclassed, so the type holds)."""

    def __init__(self) -> None:
        super().__init__()
        self.resolved: list[tuple[str, ApprovalDecision]] = []
        self.cancel_calls = 0

    def resolve_pending(self, approval_id: str, decision: ApprovalDecision) -> None:
        self.resolved.append((approval_id, decision))

    def cancel_all(self) -> None:
        self.cancel_calls += 1


def _isolate_user_layer(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Point the ``user`` layer at an empty dir under ``tmp_path``.

    ``_discover_layers`` reads a real machine path otherwise, so any
    ``load_permission_config(tmp_path)`` assertion would be environment-bound.
    """
    user_root = tmp_path / "user"
    user_root.mkdir(exist_ok=True)
    monkeypatch.setattr(
        "mcp_coder.icoder.permissions.loader.get_user_app_data_dir",
        lambda _app: user_root,
    )


def _author_project_ask(tmp_path: Path) -> None:
    """Write a ``project`` layer that gates the approval tool on ``ask``."""
    icoder = tmp_path / ".icoder"
    icoder.mkdir(exist_ok=True)
    (icoder / "settings.json").write_text(
        json.dumps({"ask": [_APPROVAL_TOOL]}), encoding="utf-8"
    )


async def _open_modal_and_press(
    app: ICoderApp,
    pilot: Pilot[Any],
    key: str,
    tool_name: str = _APPROVAL_TOOL,
) -> None:
    """Push the modal through the stream branch, then press ``key`` on it."""
    await pilot.pause()
    app._handle_stream_event(_approval_event(tool_name=tool_name))
    await pilot.pause()
    assert isinstance(app.screen, ApprovalModal)
    await pilot.press(key)
    await pilot.pause()
