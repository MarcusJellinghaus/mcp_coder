"""Textual pilot integration tests for ICoderApp."""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import queue
import threading
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest
from textual.pilot import Pilot
from textual.widgets import Static

from mcp_coder.icoder.core.app_core import AppCore
from mcp_coder.icoder.core.event_log import EventLog
from mcp_coder.icoder.env_setup import RuntimeInfo
from mcp_coder.icoder.permissions.approval import ApprovalDecision, ApprovalEngine
from mcp_coder.icoder.permissions.gateway import LangchainEnforcementGateway
from mcp_coder.icoder.permissions.loader import load_permission_config
from mcp_coder.icoder.permissions.matcher import matches
from mcp_coder.icoder.permissions.model import Matcher, PermissionFrame, Policy, Rule
from mcp_coder.icoder.permissions.resolver import resolve
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


# --- Streaming buffer regression tests (a–e + edge cases) ---


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


# --- Streaming edge-case regression tests (f–h) ---


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


# --- BusyIndicator integration tests ---


# --- Plain text rendering tests (Step 3) ---


# --- Cancel / Escape key tests ---


# --- Step 9: append_unit migration (clickable units + orphan cleanup) ---


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


# --- Step 9: approval_request branch + the direct UI -> engine cancel channel ---

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


# --- #1046 step 2: ApprovalModal pushed directly (no stream wiring yet) ---

# --- #1046 step 3: modal pushed from the stream + once/session scopes applied ---


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


# --- #1046 step 5: persist choice writes .icoder/settings.local.json ---

_UNPARSEABLE_TOOL = "mcp__srv__do__it"  # three ``__`` parts: parse_matcher rejects


def _runtime_info(project_dir: Path) -> RuntimeInfo:
    """Build a RuntimeInfo whose ``project_dir`` is ``project_dir``."""
    return RuntimeInfo(
        mcp_coder_version="0.42.0",
        mcp_coder_utils_version="0.42.0",
        python_version="3.12.0",
        claude_code_version="1.2.3",
        tool_env_path="/fake/tool",
        project_venv_path="/fake/proj/.venv",
        project_dir=str(project_dir),
        env_vars={},
        mcp_servers=[],
    )


def _persist_app(
    fake_llm: FakeLLMService,
    event_log: EventLog,
    project_dir: Path,
    gateway: LangchainEnforcementGateway | None = None,
) -> tuple[ICoderApp, _RecordingEngine, Path]:
    """Build an ICoderApp rooted at ``project_dir``; return it with its persist target."""
    engine = _RecordingEngine()
    app = ICoderApp(
        AppCore(
            llm_service=fake_llm,
            event_log=event_log,
            approval_engine=engine,
            permission_gateway=gateway,
            runtime_info=_runtime_info(project_dir),
        )
    )
    return app, engine, project_dir / ".icoder" / "settings.local.json"


def _spy_runtime_rules(monkeypatch: pytest.MonkeyPatch) -> list[Rule]:
    """Replace ``AppCore.add_runtime_rule`` with a recorder and return its list."""
    added: list[Rule] = []
    monkeypatch.setattr(
        AppCore, "add_runtime_rule", lambda self, rule: added.append(rule)
    )
    return added


async def test_persist_choice_writes_the_rule_to_settings_local(
    fake_llm: FakeLLMService, event_log: EventLog, tmp_path: Path
) -> None:
    """Choice 3 creates settings.local.json with the tool in ``allow`` exactly once."""
    app, _, target = _persist_app(fake_llm, event_log, tmp_path)
    async with app.run_test() as pilot:
        await _open_modal_and_press(app, pilot, "3")

    assert target.is_file()
    data = json.loads(target.read_text(encoding="utf-8"))
    assert data["allow"].count(_APPROVAL_TOOL) == 1


async def test_persist_choice_also_applies_the_runtime_rule(
    fake_llm: FakeLLMService,
    event_log: EventLog,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Choice 3 is live this process too: one runtime ALWAYS rule, not only a file."""
    added = _spy_runtime_rules(monkeypatch)
    app, _, _ = _persist_app(fake_llm, event_log, tmp_path)
    async with app.run_test() as pilot:
        await _open_modal_and_press(app, pilot, "3")

    assert len(added) == 1
    assert added[0].layer == "runtime"
    assert added[0].policy is Policy.ALWAYS
    assert added[0].matcher is not None
    assert matches(added[0].matcher, _APPROVAL_TOOL)


async def test_persist_choice_resolves_pending_with_persist_scope(
    fake_llm: FakeLLMService,
    event_log: EventLog,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Choice 3 reaches resolve_pending with ("allow", "persist"), after the write."""
    app, engine, target = _persist_app(fake_llm, event_log, tmp_path)
    file_existed_at_resolve: list[bool] = []
    original = engine.resolve_pending

    def _resolve(approval_id: str, decision: ApprovalDecision) -> None:
        file_existed_at_resolve.append(target.is_file())
        original(approval_id, decision)

    monkeypatch.setattr(engine, "resolve_pending", _resolve)
    async with app.run_test() as pilot:
        await _open_modal_and_press(app, pilot, "3")

    assert len(engine.resolved) == 1
    approval_id, decision = engine.resolved[0]
    assert approval_id == "a1"
    assert (decision.outcome, decision.scope) == ("allow", "persist")
    assert file_existed_at_resolve == [True]


async def test_persist_end_to_end_yields_always_after_reload(
    fake_llm: FakeLLMService,
    event_log: EventLog,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An authored project ``ask`` + a persisted local ``allow`` resolve ALWAYS on reload.

    The only test proving #1046 and #1154 compose: before step 1 the authored
    ``ask`` beat the persisted ``allow`` at equal specificity and this returned
    AFTER_APPROVAL.
    """
    _isolate_user_layer(tmp_path, monkeypatch)
    _author_project_ask(tmp_path)
    gateway = LangchainEnforcementGateway(load_permission_config(tmp_path))
    app, engine, _ = _persist_app(fake_llm, event_log, tmp_path, gateway)
    async with app.run_test() as pilot:
        assert (
            resolve(_APPROVAL_TOOL, {}, None, gateway._config).policy
            is Policy.AFTER_APPROVAL
        )
        await _open_modal_and_press(app, pilot, "3")
        assert (
            resolve(_APPROVAL_TOOL, {}, None, gateway._config).policy is Policy.ALWAYS
        )
    assert len(engine.resolved) == 1

    reloaded = load_permission_config(tmp_path)
    assert not reloaded.degraded
    assert resolve(_APPROVAL_TOOL, {}, None, reloaded).policy is Policy.ALWAYS


async def test_unparseable_tool_name_is_never_written_to_disk(
    fake_llm: FakeLLMService,
    event_log: EventLog,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A name parse_matcher rejects grants nothing, writes nothing, still resolves.

    One rejected token would fail the whole ``local`` layer on the next launch
    and drive every tool to ASK, so the guard must run before the write.
    """
    _isolate_user_layer(tmp_path, monkeypatch)
    _author_project_ask(tmp_path)
    added = _spy_runtime_rules(monkeypatch)
    app, engine, target = _persist_app(fake_llm, event_log, tmp_path)
    async with app.run_test() as pilot:
        await _open_modal_and_press(app, pilot, "3", tool_name=_UNPARSEABLE_TOOL)
        log_text = "\n".join(app.query_one(OutputLog).recorded_lines)
        assert len(app.screen_stack) == 1

    assert not target.exists()
    assert added == []
    assert len(engine.resolved) == 1
    decision = engine.resolved[0][1]
    assert (decision.outcome, decision.scope) == ("allow", "persist")
    assert "Could not remember" in log_text
    assert _UNPARSEABLE_TOOL in log_text

    reloaded = load_permission_config(tmp_path)
    assert reloaded.degraded is False


@pytest.mark.parametrize(
    "content",
    [
        pytest.param(None, id="target-is-a-directory"),
        pytest.param(b'{"allow": ["\xff\xfe"]}', id="invalid-utf8"),
        pytest.param(b'{"allow": [', id="malformed"),
        pytest.param(b'["x"]', id="non-object-root"),
        pytest.param(b'{"allow": "mcp__a__b"}', id="non-list-section"),
        pytest.param(
            b'{"ask": [], "ask": ["mcp__srv__do_it"]}', id="duplicate-key-move"
        ),
    ],
)
async def test_persist_write_failure_degrades_to_a_session_grant(
    fake_llm: FakeLLMService,
    event_log: EventLog,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    content: bytes | None,
) -> None:
    """A failed write (OSError or PersistError) still grants the session and resolves.

    The last five seeds prove PersistError lands in the ``except OSError``
    branch instead of escaping onto the UI thread and wedging the turn.
    """
    added = _spy_runtime_rules(monkeypatch)
    app, engine, target = _persist_app(fake_llm, event_log, tmp_path)
    if content is None:
        target.mkdir(parents=True)
    else:
        target.parent.mkdir(parents=True)
        target.write_bytes(content)

    async with app.run_test() as pilot:
        await _open_modal_and_press(app, pilot, "3")
        log_text = "\n".join(app.query_one(OutputLog).recorded_lines)
        assert len(app.screen_stack) == 1

    assert len(added) == 1
    assert added[0].policy is Policy.ALWAYS
    assert len(engine.resolved) == 1
    assert engine.resolved[0][1].scope == "persist"
    assert "Could not write the permission rule" in log_text
    assert f"{_APPROVAL_TOOL} is allowed for this session only" in log_text
    if content is not None:
        assert target.read_bytes() == content


# --- Step 10: shutdown hook + closed-app guard (R9) ---

#: Hard cap on the quit-with-an-approval-pending case, deliberately far below
#: the provider's 300s inactivity timeout: a stall must fail fast rather than
#: pass for a stalled-then-timed-out turn.
_QUIT_TIMEOUT = 30.0


class _ApprovalPendingLLMService:
    """Fake service reproducing ``_ask_agent_stream``'s two-loop topology.

    ``ApprovalEngine.request_approval`` runs on a background thread with its own
    ``asyncio.run`` loop (the stand-in agent loop) and the emitted event travels
    through a ``queue.Queue``, so the Textual worker parks in ``q.get`` while the
    approval future lives on a *different* loop -- exactly the shape R9 is about,
    without needing a real agent.
    """

    def __init__(self, engine: ApprovalEngine) -> None:
        self._engine = engine
        self.agent_thread: threading.Thread | None = None
        #: Set once the UI has handled the emitted event and the consumer has
        #: gone back to ``q.get`` -- i.e. the approval is genuinely pending.
        self.dispatched = threading.Event()

    def stream(
        self, question: str, *, frame: PermissionFrame | None = None
    ) -> Iterator[StreamEvent]:
        q: queue.Queue[StreamEvent | None] = queue.Queue()

        async def _ask() -> None:
            try:
                await self._engine.request_approval(
                    tool_name="mcp__srv__do_it", args={}, source="project"
                )
            finally:
                q.put(None)  # sentinel, like the provider's producer half

        def _agent_main() -> None:
            # Production keeps the CancelledError off ``asyncio.run``: the
            # provider's ``_run`` wraps its ``run_agent_stream`` drain in an
            # ``except asyncio.CancelledError`` and returns normally, so the
            # agent thread exits quietly with the sentinel already queued. This
            # fake has no drain to wrap -- ``_ask`` is the whole coroutine --
            # so it catches at the thread top instead. Same observable result,
            # which is what the pilot tests below assert: a silent thread exit
            # and no stray traceback over a live Textual screen.
            with contextlib.suppress(BaseException):  # pylint: disable=broad-exception-caught
                asyncio.run(_ask())

        self._engine.attach(q.put)
        thread = threading.Thread(target=_agent_main, daemon=True)
        self.agent_thread = thread
        thread.start()
        try:
            while True:
                event = q.get(timeout=_QUIT_TIMEOUT)
                if event is None:
                    return
                yield event
                self.dispatched.set()
        finally:
            # Same order as the provider: detach (cancelling what is left)
            # BEFORE the join, so a parked interceptor unwinds while it waits.
            self._engine.detach()
            thread.join(timeout=5)

    @property
    def provider(self) -> str:
        return "claude"

    @property
    def session_id(self) -> str | None:
        return None

    def reset_session(self) -> None:
        pass

    def set_session_id(self, session_id: str | None) -> None:
        pass


async def test_quit_with_approval_pending_exits_and_unwinds_worker(
    event_log: EventLog, monkeypatch: pytest.MonkeyPatch
) -> None:
    """R9 on the real exit path: quitting with an approval pending must not hang.

    Asserting only that ``on_unmount`` called ``cancel_pending_approvals()``
    would be a proxy for the hook, not for R9 -- it would stay green while the
    unwound worker blocked forever in ``call_from_thread`` against a dead
    message pump. So this drives the whole path: the app exits, the parked
    agent thread dies, and the ``_stream_llm`` worker body returns.
    """
    engine = ApprovalEngine()
    service = _ApprovalPendingLLMService(engine)
    app = ICoderApp(
        AppCore(llm_service=service, event_log=event_log, approval_engine=engine)
    )

    # Textual thread workers run in a pooled, reused thread, so ``is_alive()``
    # says nothing about the worker *body*. Wrap it instead: the event is set
    # only once ``_stream_llm`` actually returns.
    worker_done = threading.Event()
    worker_error: list[BaseException] = []
    original_stream_llm = app._stream_llm

    def _tracked(text: str, skill_name: str | None = None) -> None:
        try:
            original_stream_llm(text, skill_name)
        except BaseException as exc:  # pylint: disable=broad-exception-caught
            worker_error.append(exc)
        finally:
            worker_done.set()

    monkeypatch.setattr(app, "_stream_llm", _tracked)

    async def _turn_then_quit() -> None:
        async with app.run_test() as pilot:
            await _submit_and_wait(app, pilot, text="use the tool")
            for _ in range(200):
                if service.dispatched.is_set():
                    break
                await pilot.pause(delay=0.05)
            assert service.dispatched.is_set(), (
                "the approval_request never reached the UI"
            )
            assert engine.pending() == 1, "nothing pending: R9 is not being exercised"
            app.exit()
            await pilot.pause()

    await asyncio.wait_for(_turn_then_quit(), timeout=_QUIT_TIMEOUT)

    assert not app.is_running, "the app did not exit"
    assert engine.cancelled, "on_unmount never reached the engine"
    # Both halves of R9 in one pair of asserts. Without the closed-app guard the
    # worker tail's ``call_from_thread`` hops reach a torn-down app: either they
    # block on a loop this (blocking) wait is keeping busy, or they run and
    # explode on the cleared widget tree.
    assert worker_done.wait(timeout=10.0), "the _stream_llm worker body never returned"
    assert worker_error == [], f"the worker tail hit a torn-down app: {worker_error!r}"
    assert service.agent_thread is not None
    assert service.agent_thread.is_alive() is False, (
        "the parked approval future was never cancelled"
    )


async def test_shutdown_guard_drops_every_ui_call_from_worker_tail(
    make_icoder_app: Callable[..., ICoderApp], monkeypatch: pytest.MonkeyPatch
) -> None:
    """With ``_shutting_down`` set, the worker issues no ``call_from_thread``.

    Driven from the UI thread on purpose: with the guard up not a single
    cross-thread hop is attempted, so the body is free to run here -- and the
    call the tail would otherwise make (``_reset_busy_indicator``, on the
    ``elif not _error_handled`` branch) is the exact one that hangs a quit.
    """
    app = make_icoder_app(
        responses=[[{"type": "text_delta", "text": "hi"}, {"type": "done"}]]
    )
    async with app.run_test() as pilot:
        await pilot.pause()
        calls: list[Callable[..., None]] = []
        monkeypatch.setattr(
            app, "call_from_thread", lambda callback, *args: calls.append(callback)
        )
        app._shutting_down.set()

        app._stream_llm("hello")  # returns instead of blocking on a dead pump

        assert calls == []


async def test_shutdown_race_runtime_error_is_logged_not_propagated(
    make_icoder_app: Callable[..., ICoderApp],
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A ``RuntimeError`` in the race window is caught and logged, never raised.

    ``_shutting_down`` is deliberately NOT set here: this is the narrow window
    where the flag is still down but ``App._loop`` has already gone, so
    ``call_from_thread`` raises. It must not escape the worker.
    """
    app = make_icoder_app(
        responses=[[{"type": "text_delta", "text": "hi"}, {"type": "done"}]]
    )

    def _pump_is_gone(callback: Callable[..., None], *args: object) -> None:
        raise RuntimeError("App is not running")

    async with app.run_test() as pilot:
        await pilot.pause()
        monkeypatch.setattr(app, "call_from_thread", _pump_is_gone)
        with caplog.at_level(logging.DEBUG, logger="mcp_coder.icoder.ui.stream_view"):
            app._stream_llm("hello")

        assert any(
            "call_from_thread dropped during shutdown" in record.getMessage()
            for record in caplog.records
        )
