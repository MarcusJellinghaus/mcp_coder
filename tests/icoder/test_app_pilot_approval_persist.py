from __future__ import annotations

import json
from pathlib import Path

import pytest

from mcp_coder.icoder.core.app_core import AppCore
from mcp_coder.icoder.core.event_log import EventLog
from mcp_coder.icoder.env_setup import RuntimeInfo
from mcp_coder.icoder.permissions.approval import ApprovalDecision
from mcp_coder.icoder.permissions.gateway import LangchainEnforcementGateway
from mcp_coder.icoder.permissions.loader import load_permission_config
from mcp_coder.icoder.permissions.matcher import matches
from mcp_coder.icoder.permissions.model import Policy, Rule
from mcp_coder.icoder.permissions.resolver import resolve
from mcp_coder.icoder.services.llm_service import FakeLLMService
from mcp_coder.icoder.ui.app import ICoderApp
from mcp_coder.icoder.ui.widgets.output_log import OutputLog
from tests.icoder.test_app_pilot import (
    _APPROVAL_TOOL,
    _author_project_ask,
    _isolate_user_layer,
    _open_modal_and_press,
    _RecordingEngine,
)

pytestmark = pytest.mark.textual_integration


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
