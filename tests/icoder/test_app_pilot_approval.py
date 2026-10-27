from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from textual.pilot import Pilot
from textual.widgets import Static, TextArea

from mcp_coder.icoder.core.app_core import AppCore
from mcp_coder.icoder.core.event_log import EventLog
from mcp_coder.icoder.permissions.approval import ApprovalDecision
from mcp_coder.icoder.permissions.gateway import LangchainEnforcementGateway
from mcp_coder.icoder.permissions.loader import load_permission_config
from mcp_coder.icoder.permissions.matcher import matches
from mcp_coder.icoder.permissions.model import Matcher, PermissionConfig, Policy, Rule
from mcp_coder.icoder.permissions.resolver import resolve
from mcp_coder.icoder.services.llm_service import FakeLLMService
from mcp_coder.icoder.ui.app import ICoderApp
from mcp_coder.icoder.ui.widgets.approval_modal import ApprovalModal
from mcp_coder.icoder.ui.widgets.output_log import OutputLog
from tests.icoder._app_pilot_approval_helpers import (
    _APPROVAL_TOOL,
    _approval_event,
    _author_project_ask,
    _isolate_user_layer,
    _open_modal_and_press,
    _RecordingEngine,
)

pytestmark = pytest.mark.textual_integration

_LONG_CMD = "x" * 300


def _recording_app(
    fake_llm: FakeLLMService, event_log: EventLog
) -> tuple[ICoderApp, _RecordingEngine]:
    """Build an ICoderApp around a recording engine (no gateway)."""
    engine = _RecordingEngine()
    app = ICoderApp(
        AppCore(llm_service=fake_llm, event_log=event_log, approval_engine=engine)
    )
    return app, engine


async def test_session_grant_is_honoured_by_resolve(
    fake_llm: FakeLLMService, event_log: EventLog
) -> None:
    """Choice 2 goes through the real gateway: the authored ask now resolves ALWAYS."""
    authored_ask = Rule(
        Matcher(server="srv", tool="do_it"), Policy.AFTER_APPROVAL, "project"
    )
    gateway = LangchainEnforcementGateway(PermissionConfig(rules=(authored_ask,)))
    engine = _RecordingEngine()
    app = ICoderApp(
        AppCore(
            llm_service=fake_llm,
            event_log=event_log,
            approval_engine=engine,
            permission_gateway=gateway,
        )
    )
    async with app.run_test() as pilot:
        assert (
            resolve(_APPROVAL_TOOL, {}, None, gateway._config).policy
            is Policy.AFTER_APPROVAL
        )
        await _open_modal_and_press(app, pilot, "2")

        assert (
            resolve(_APPROVAL_TOOL, {}, None, gateway._config).policy is Policy.ALWAYS
        )
        assert len(engine.resolved) == 1


async def test_session_grant_does_not_survive_a_reload(
    fake_llm: FakeLLMService,
    event_log: EventLog,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A session grant lives in memory only: a fresh load still asks (design §8.4)."""
    _isolate_user_layer(tmp_path, monkeypatch)
    _author_project_ask(tmp_path)
    gateway = LangchainEnforcementGateway(load_permission_config(tmp_path))
    engine = _RecordingEngine()
    app = ICoderApp(
        AppCore(
            llm_service=fake_llm,
            event_log=event_log,
            approval_engine=engine,
            permission_gateway=gateway,
        )
    )
    async with app.run_test() as pilot:
        await _open_modal_and_press(app, pilot, "2")
        assert (
            resolve(_APPROVAL_TOOL, {}, None, gateway._config).policy is Policy.ALWAYS
        )

    reloaded = load_permission_config(tmp_path)
    assert not reloaded.degraded
    assert all(rule.layer != "runtime" for rule in reloaded.rules)
    assert resolve(_APPROVAL_TOOL, {}, None, reloaded).policy is Policy.AFTER_APPROVAL


async def test_replayed_log_pushes_no_approval_modal(
    event_log: EventLog,
) -> None:
    """approval_request never reaches the .jsonl, so a resume pushes no modal."""
    fake = FakeLLMService(responses=[[_approval_event(), {"type": "done"}]])
    core = AppCore(llm_service=fake, event_log=event_log)
    list(core.stream_llm("use the tool"))
    log_path = event_log.current_path
    assert "approval_request" not in log_path.read_text(encoding="utf-8")

    app = ICoderApp(core)
    async with app.run_test() as pilot:
        await pilot.pause()
        app.do_resume(log_path)
        await pilot.pause()

        assert len(app.screen_stack) == 1
        assert not isinstance(app.screen, ApprovalModal)


@pytest.mark.parametrize(
    ("key", "outcome", "scope"),
    [
        ("1", "allow", "once"),
        ("2", "allow", "session"),
        ("4", "deny", "once"),
    ],
)
async def test_approval_choice_resolves_pending_with_decision(
    fake_llm: FakeLLMService,
    event_log: EventLog,
    key: str,
    outcome: str,
    scope: str,
) -> None:
    """One keypress on the modal reaches resolve_pending with the matching decision."""
    app, engine = _recording_app(fake_llm, event_log)
    async with app.run_test() as pilot:
        await _open_modal_and_press(app, pilot, key)

        assert len(engine.resolved) == 1
        approval_id, decision = engine.resolved[0]
        assert approval_id == "a1"
        assert decision.outcome == outcome
        assert decision.scope == scope
        assert decision.reason is None


async def test_allow_once_writes_no_runtime_rule(
    fake_llm: FakeLLMService, event_log: EventLog, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Choice 1 grants nothing beyond this call."""
    added: list[Rule] = []
    monkeypatch.setattr(
        AppCore, "add_runtime_rule", lambda self, rule: added.append(rule)
    )
    app, _ = _recording_app(fake_llm, event_log)
    async with app.run_test() as pilot:
        await _open_modal_and_press(app, pilot, "1")

        assert added == []


async def test_session_choice_writes_a_runtime_rule(
    fake_llm: FakeLLMService, event_log: EventLog, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Choice 2 adds exactly one runtime ALWAYS rule matching the tool."""
    added: list[Rule] = []
    monkeypatch.setattr(
        AppCore, "add_runtime_rule", lambda self, rule: added.append(rule)
    )
    app, _ = _recording_app(fake_llm, event_log)
    async with app.run_test() as pilot:
        await _open_modal_and_press(app, pilot, "2")

        assert len(added) == 1
        rule = added[0]
        assert rule.layer == "runtime"
        assert rule.policy is Policy.ALWAYS
        assert rule.matcher is not None
        assert matches(rule.matcher, _APPROVAL_TOOL)


async def test_cancel_turn_cancels_and_never_resolves(
    fake_llm: FakeLLMService, event_log: EventLog
) -> None:
    """Choice 5 cancels the turn through the engine channel and answers nothing."""
    app, engine = _recording_app(fake_llm, event_log)
    async with app.run_test() as pilot:
        await _open_modal_and_press(app, pilot, "5")

        assert engine.cancel_calls == 1
        assert engine.resolved == []
        assert app._cancel_event.is_set()


async def test_ctrl_c_does_not_cancel_the_turn(
    fake_llm: FakeLLMService, event_log: EventLog, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ctrl+C on the open modal copies; it neither cancels nor resolves."""
    app, engine = _recording_app(fake_llm, event_log)
    monkeypatch.setattr(app, "copy_to_clipboard", lambda _text: None)
    async with app.run_test() as pilot:
        await _open_modal_and_press(app, pilot, "ctrl+c")

        assert engine.cancel_calls == 0
        assert engine.resolved == []
        assert isinstance(app.screen, ApprovalModal)


async def _push_approval_modal(
    app: ICoderApp, pilot: Pilot[Any], tmp_path: Path
) -> tuple[list[ApprovalDecision | None], Path]:
    """Push one ApprovalModal and return the dismiss recorder + persist target."""
    persist_target = tmp_path / ".icoder" / "settings.local.json"
    got: list[ApprovalDecision | None] = []
    app.push_screen(
        ApprovalModal(
            tool_name="mcp__srv__do_it",
            args={"path": "a.txt", "cmd": _LONG_CMD},
            source="project",
            persist_target=persist_target,
        ),
        got.append,
    )
    await pilot.pause()
    return got, persist_target


def _approval_prompt_text(app: ICoderApp) -> str:
    """Return the rendered text of the modal's ``#approval-prompt`` Static."""
    return str(app.screen.query_one("#approval-prompt", Static).render())


async def test_approval_modal_cancel_dismisses_with_none(
    icoder_app: ICoderApp, tmp_path: Path
) -> None:
    """Choice 5 dismisses with None — the caller cancels the turn."""
    async with icoder_app.run_test() as pilot:
        got, _ = await _push_approval_modal(icoder_app, pilot, tmp_path)
        await pilot.press("5")
        await pilot.pause()

        assert got == [None]


async def test_approval_modal_ctrl_c_copies_and_does_not_dismiss(
    icoder_app: ICoderApp, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ctrl+C copies the args text and leaves the modal open."""
    copied: list[str] = []
    monkeypatch.setattr(icoder_app, "copy_to_clipboard", copied.append)
    async with icoder_app.run_test() as pilot:
        got, _ = await _push_approval_modal(icoder_app, pilot, tmp_path)
        await pilot.press("ctrl+c")
        await pilot.pause()

        assert copied
        assert _LONG_CMD in copied[0]
        assert got == []
        assert isinstance(icoder_app.screen, ApprovalModal)


async def test_approval_request_pushes_the_modal(
    fake_llm: FakeLLMService, event_log: EventLog
) -> None:
    """An approval_request pushes an ApprovalModal for the tool and answers nothing yet."""
    engine = _RecordingEngine()
    app = ICoderApp(
        AppCore(llm_service=fake_llm, event_log=event_log, approval_engine=engine)
    )
    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one(OutputLog)
        before = list(output.recorded_lines)

        app._handle_stream_event(_approval_event())
        await pilot.pause()

        assert isinstance(app.screen, ApprovalModal)
        assert _APPROVAL_TOOL in _approval_prompt_text(app)
        assert engine.resolved == []
        # Nothing rendered, and no turn/tool state was touched.
        assert output.recorded_lines == before
        assert app._current_turn_id is None
        assert not app._open_tool_units


async def test_cancel_stream_also_cancels_pending_approvals(
    fake_llm: FakeLLMService, event_log: EventLog
) -> None:
    """Escape sets the cancel event AND reaches the engine (FINDINGS §4)."""
    engine = _RecordingEngine()
    app = ICoderApp(
        AppCore(llm_service=fake_llm, event_log=event_log, approval_engine=engine)
    )
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()

        assert engine.cancel_calls == 1
        assert app._cancel_event.is_set()


async def test_approval_modal_states_the_over_grant(
    icoder_app: ICoderApp, tmp_path: Path
) -> None:
    """The prompt names the tool and says a remember grant covers any arguments."""
    async with icoder_app.run_test() as pilot:
        await _push_approval_modal(icoder_app, pilot, tmp_path)
        prompt = _approval_prompt_text(icoder_app)
        assert "with any arguments" in prompt
        assert "mcp__srv__do_it" in prompt


async def test_approval_modal_args_widget_holds_full_args(
    icoder_app: ICoderApp, tmp_path: Path
) -> None:
    """A 300-char single-line value reaches the TextArea verbatim, no ellipsis."""
    async with icoder_app.run_test() as pilot:
        await _push_approval_modal(icoder_app, pilot, tmp_path)
        text = icoder_app.screen.query_one("#approval-args", TextArea).text
        assert _LONG_CMD in text
        assert "cmd" in text
        assert "..." not in text


async def test_approval_modal_shows_persist_target_and_summary(
    icoder_app: ICoderApp, tmp_path: Path
) -> None:
    """Choice 3 is confirmed inline: target file plus a one-line write summary."""
    async with icoder_app.run_test() as pilot:
        _, persist_target = await _push_approval_modal(icoder_app, pilot, tmp_path)
        prompt = _approval_prompt_text(icoder_app)
        assert str(persist_target) in prompt
        assert "allow" in prompt
        assert "mcp__srv__do_it" in prompt


@pytest.mark.parametrize(
    ("key", "outcome", "scope"),
    [
        ("1", "allow", "once"),
        ("2", "allow", "session"),
        ("3", "allow", "persist"),
        ("4", "deny", "once"),
        ("escape", "deny", "once"),
    ],
)
async def test_approval_modal_choice_dismisses_with_decision(
    icoder_app: ICoderApp, tmp_path: Path, key: str, outcome: str, scope: str
) -> None:
    """One keypress dismisses with the matching decision; reason stays None."""
    async with icoder_app.run_test() as pilot:
        got, _ = await _push_approval_modal(icoder_app, pilot, tmp_path)
        await pilot.press(key)
        await pilot.pause()

        assert len(got) == 1
        decision = got[0]
        assert decision is not None
        assert decision.outcome == outcome
        assert decision.scope == scope
        assert decision.reason is None
