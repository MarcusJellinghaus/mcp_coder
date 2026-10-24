"""Step 9 wiring: CLI -> gateway / ``RealLLMService`` / ``AppCore``.

Four concerns are covered here:

* **Identity wiring** — ``execute_icoder`` builds exactly ONE
  :class:`ApprovalEngine` on the ``langchain`` + ``mcp_config`` path and hands
  the *same object* to the gateway, the LLM service and ``AppCore``; outside
  that path engine and gateway stay ``None`` and the three ``AppCore``
  delegators are safe no-ops.
* **Forwarding** — ``RealLLMService.stream`` passes its ``approval_bridge``
  through to ``prompt_llm_stream`` on every turn.
* **R16** — a turn the engine reports as cancelled writes neither
  ``llm_request_end`` nor a session record; an uncancelled turn (and a turn with
  no engine at all) is unchanged.
* **R5 + runtime rules** — ``approval_request`` never reaches the session
  ``.jsonl``, and ``AppCore.add_runtime_rule`` grants the tool on a later turn.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from mcp_coder.icoder.core.app_core import AppCore
from mcp_coder.icoder.core.event_log import EventLog
from mcp_coder.icoder.permissions import (
    Matcher,
    PermissionConfig,
    Policy,
    Rule,
)
from mcp_coder.icoder.permissions.approval import ApprovalDecision, ApprovalEngine
from mcp_coder.icoder.permissions.gateway import (
    _DENY_ASK,
    LangchainEnforcementGateway,
)
from mcp_coder.icoder.services.llm_service import FakeLLMService, RealLLMService
from mcp_coder.llm.types import StreamEvent
from tests.icoder.conftest import make_icoder_args, patch_icoder_deps

# ======================================================================
# Helpers
# ======================================================================


def _install_fake_manager(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patch ``MCPManager`` so no real thread/loop starts."""

    def fake_init(
        self: object, server_config: object, tool_interceptors: object = None
    ) -> None:
        object.__setattr__(self, "_server_names", [])
        object.__setattr__(self, "_server_config", server_config)
        object.__setattr__(self, "_cached_tools", None)
        object.__setattr__(self, "_client", None)
        object.__setattr__(self, "_tool_counts", {})
        object.__setattr__(self, "_loop", None)
        object.__setattr__(self, "_thread", None)

    monkeypatch.setattr("mcp_coder.cli.commands.icoder.MCPManager.__init__", fake_init)
    monkeypatch.setattr(
        "mcp_coder.cli.commands.icoder.MCPManager.close", lambda self: None
    )


def _capture_llm_kwargs(
    monkeypatch: pytest.MonkeyPatch, captured: list[dict[str, Any]]
) -> None:
    """Patch ``RealLLMService.__init__`` to record its keyword arguments."""

    def fake_init(self: object, **kwargs: Any) -> None:
        captured.append(kwargs)

    monkeypatch.setattr(
        "mcp_coder.icoder.services.llm_service.RealLLMService.__init__", fake_init
    )


def _capture_app_core(monkeypatch: pytest.MonkeyPatch) -> list[AppCore]:
    """Patch ``ICoderApp.__init__`` to capture the constructed ``AppCore``.

    Returns:
        The list that receives each constructed core (one per CLI run).
    """
    from mcp_coder.icoder.ui.app import ICoderApp

    captured: list[AppCore] = []

    def capturing_init(self: object, app_core: AppCore, **_kw: Any) -> None:
        captured.append(app_core)

    monkeypatch.setattr(ICoderApp, "__init__", capturing_init)
    return captured


def _rule(policy: Policy, layer: str = "user") -> Rule:
    """Build a rule for ``mcp__s__t`` with the given policy and layer."""
    return Rule(matcher=Matcher(server="s", tool="t"), policy=policy, layer=layer)


def _request(tool_call_id: str = "call_1") -> Any:
    """Build a fake adapter request for ``mcp__s__t``."""
    return SimpleNamespace(
        server_name="s",
        name="t",
        args={},
        runtime=SimpleNamespace(tool_call_id=tool_call_id),
    )


class _Handler:
    """A fake async tool handler that records whether it was awaited."""

    def __init__(self, result: Any) -> None:
        self.result = result
        self.awaited = False

    async def __call__(self, request: Any) -> Any:
        self.awaited = True
        return self.result


class _AbortedEngine(ApprovalEngine):
    """Engine stub reporting an aborted turn (subclassed, so the type holds)."""

    @property
    def turn_aborted(self) -> bool:
        return True


@pytest.fixture
def fake_deny_bridge(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stub the langchain deny bridge so these tests need no ``langchain_core``."""

    def _fake(text: str, name: str, tool_call_id: str) -> Any:
        return SimpleNamespace(content=text, status="error", name=name)

    monkeypatch.setattr(
        "mcp_coder.icoder.permissions.gateway.build_deny_tool_message", _fake
    )


# ======================================================================
# 1-2. CLI identity wiring
# ======================================================================


def test_cli_builds_one_engine_shared_by_gateway_service_and_core(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """One ``ApprovalEngine`` reaches gateway, service and core — by identity."""
    from mcp_coder.cli.commands.icoder import execute_icoder

    (tmp_path / "logs").mkdir()
    patch_icoder_deps(monkeypatch, tmp_path)
    monkeypatch.setattr(
        "mcp_coder.cli.commands.icoder._load_mcp_server_config",
        lambda *_a, **_kw: {"srv": {"transport": "stdio"}},
    )
    _install_fake_manager(monkeypatch)
    llm_calls: list[dict[str, Any]] = []
    _capture_llm_kwargs(monkeypatch, llm_calls)
    cores = _capture_app_core(monkeypatch)

    assert execute_icoder(make_icoder_args(tmp_path)) == 0

    assert len(llm_calls) == 1
    engine = llm_calls[0]["approval_bridge"]
    gateway = llm_calls[0]["gateway"]
    assert isinstance(engine, ApprovalEngine)
    assert isinstance(gateway, LangchainEnforcementGateway)
    # Identity, not equality: the three holders share ONE live engine.
    assert gateway._engine is engine
    assert len(cores) == 1
    assert cores[0]._approval_engine is engine
    assert cores[0]._permission_gateway is gateway


def test_non_langchain_leaves_engine_and_gateway_none(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Claude + no mcp_config: no engine, no gateway, delegators are no-ops."""
    from mcp_coder.cli.commands.icoder import execute_icoder

    (tmp_path / "logs").mkdir()
    patch_icoder_deps(monkeypatch, tmp_path)
    monkeypatch.setattr(
        "mcp_coder.cli.commands.icoder.resolve_llm_method",
        lambda _: ("claude", None),
    )
    monkeypatch.setattr(
        "mcp_coder.cli.commands.icoder.parse_llm_method_from_args",
        lambda _: "claude",
    )
    monkeypatch.setattr(
        "mcp_coder.cli.commands.icoder.resolve_mcp_config_path",
        lambda *a, **_kw: None,
    )
    llm_calls: list[dict[str, Any]] = []
    _capture_llm_kwargs(monkeypatch, llm_calls)
    cores = _capture_app_core(monkeypatch)

    assert execute_icoder(make_icoder_args(tmp_path)) == 0

    assert llm_calls[0]["approval_bridge"] is None
    assert llm_calls[0]["gateway"] is None
    core = cores[0]
    assert core._approval_engine is None
    assert core._permission_gateway is None
    # All three delegators must be harmless without their handles.
    core.resolve_pending("unknown", ApprovalDecision("deny", "once"))
    core.cancel_pending_approvals()
    core.add_runtime_rule(_rule(Policy.ALWAYS, layer="runtime"))


# ======================================================================
# 3. RealLLMService forwards the bridge
# ======================================================================


def test_stream_forwards_approval_bridge(monkeypatch: pytest.MonkeyPatch) -> None:
    """``RealLLMService.stream`` hands its bridge to ``prompt_llm_stream``."""
    captured: dict[str, Any] = {}

    def mock_stream(question: str, **kwargs: Any) -> Any:
        captured.update(kwargs)
        yield {"type": "done"}

    monkeypatch.setattr(
        "mcp_coder.icoder.services.llm_service.prompt_llm_stream", mock_stream
    )
    engine = ApprovalEngine()
    service = RealLLMService(
        provider="langchain", project_dir="/test/project", approval_bridge=engine
    )

    list(service.stream("hi"))

    assert captured["approval_bridge"] is engine


def test_stream_forwards_none_without_a_bridge(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No bridge injected -> ``approval_bridge=None`` reaches the provider."""
    captured: dict[str, Any] = {}

    def mock_stream(question: str, **kwargs: Any) -> Any:
        captured.update(kwargs)
        yield {"type": "done"}

    monkeypatch.setattr(
        "mcp_coder.icoder.services.llm_service.prompt_llm_stream", mock_stream
    )
    service = RealLLMService(provider="claude", project_dir="/test/project")

    list(service.stream("hi"))

    assert captured["approval_bridge"] is None


# ======================================================================
# 4-5. R16 — the cancelled turn leaves no record
# ======================================================================


def test_cancelled_turn_writes_no_request_end_and_no_session(
    fake_llm: FakeLLMService, event_log: EventLog, monkeypatch: pytest.MonkeyPatch
) -> None:
    """R16: engine reports the turn aborted -> no ``llm_request_end``, no store."""
    stored: list[tuple[Any, ...]] = []
    monkeypatch.setattr(
        "mcp_coder.icoder.core.app_core.store_session",
        lambda *a, **kw: stored.append(a),
    )
    core = AppCore(
        llm_service=fake_llm,
        event_log=event_log,
        approval_engine=_AbortedEngine(),
    )

    list(core.stream_llm("hi"))

    assert stored == []
    assert not any(e.event == "llm_request_end" for e in event_log.entries)


def test_shutdown_cancel_with_nothing_pending_still_records_the_turn(
    fake_llm: FakeLLMService, event_log: EventLog, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Quitting during an approval-free turn must not discard its record.

    ``on_unmount`` fires ``cancel_all()`` on every quit, so gating R16 on
    ``cancelled`` would drop the ``llm_request_end`` and the session record of a
    turn that finished normally. ``turn_aborted`` stays down because nothing was
    parked, so this turn is recorded like any other.
    """
    stored: list[tuple[Any, ...]] = []
    monkeypatch.setattr(
        "mcp_coder.icoder.core.app_core.store_session",
        lambda *a, **kw: stored.append(a),
    )
    engine = ApprovalEngine()
    engine.attach(lambda event: None)
    engine.cancel_all()  # the shutdown hook, with no approval in flight
    core = AppCore(llm_service=fake_llm, event_log=event_log, approval_engine=engine)

    list(core.stream_llm("hi"))

    assert engine.cancelled is True
    assert engine.turn_aborted is False
    assert len(stored) == 1
    assert any(e.event == "llm_request_end" for e in event_log.entries)


@pytest.mark.parametrize("with_engine", [False, True])
def test_normal_turn_still_stores(
    with_engine: bool,
    fake_llm: FakeLLMService,
    event_log: EventLog,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An uncancelled turn (engine present or absent) records as before."""
    stored: list[tuple[Any, ...]] = []
    monkeypatch.setattr(
        "mcp_coder.icoder.core.app_core.store_session",
        lambda *a, **kw: stored.append(a),
    )
    core = AppCore(
        llm_service=fake_llm,
        event_log=event_log,
        approval_engine=ApprovalEngine() if with_engine else None,
    )

    list(core.stream_llm("hi"))

    assert len(stored) == 1
    assert any(e.event == "llm_request_end" for e in event_log.entries)


# ======================================================================
# 6. R5 — approval_request is transient
# ======================================================================


def test_approval_request_never_reaches_the_session_log(
    event_log: EventLog,
) -> None:
    """The transient event types are absent from the ``.jsonl``; others stay."""
    events: list[StreamEvent] = [
        {"type": "text_delta", "text": "hi"},
        {"type": "raw_line", "line": "{...}"},
        {"type": "approval_request", "approval_id": "a1", "tool_name": "mcp__s__t"},
        {"type": "tool_result", "name": "t", "output": "ok"},
        {"type": "done"},
    ]
    core = AppCore(llm_service=FakeLLMService(responses=[events]), event_log=event_log)

    yielded = list(core.stream_llm("hi"))

    # The live consumer still sees every event; only the log is filtered.
    assert [e["type"] for e in yielded] == [e["type"] for e in events]
    logged = [
        json.loads(line)
        for line in event_log.current_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    stream_types = [e.get("type") for e in logged if e["event"] == "stream_event"]
    assert "approval_request" not in stream_types
    assert "raw_line" not in stream_types
    assert stream_types == ["text_delta", "tool_result", "done"]


# ======================================================================
# 7. scope=session end to end (engine-free)
# ======================================================================


@pytest.mark.usefixtures("fake_deny_bridge")
async def test_add_runtime_rule_grants_the_tool_on_a_later_turn(
    fake_llm: FakeLLMService, event_log: EventLog
) -> None:
    """``AppCore.add_runtime_rule`` -> the gateway resolves ALWAYS afterwards."""
    gateway = LangchainEnforcementGateway(
        PermissionConfig(rules=(_rule(Policy.AFTER_APPROVAL),))
    )
    core = AppCore(
        llm_service=fake_llm, event_log=event_log, permission_gateway=gateway
    )

    gateway.begin_turn(None)
    denied = await gateway.interceptor(_request(), _Handler(object()))
    assert denied.content == _DENY_ASK  # ask with no engine -> fail closed

    core.add_runtime_rule(_rule(Policy.ALWAYS, layer="runtime"))

    gateway.begin_turn(None)  # a subsequent turn
    sentinel = object()
    handler = _Handler(sentinel)
    result = await gateway.interceptor(_request(), handler)

    assert handler.awaited
    assert result is sentinel
