"""Tests for the iCoder enforcement gateway (Step 3 of I2.3 / Step 6 of I3.2, TDD).

Exercises the gateway in isolation with fake tool objects and a fake async
handler — no live MCP server, no agent. Covers the two enforcement seams:

* :meth:`LangchainEnforcementGateway.filter_tools` — turn-level visibility:
  unconditional ``NEVER`` hidden, arg-scoped ``NEVER`` kept visible.
* :meth:`LangchainEnforcementGateway.interceptor` — call-level enforcement:
  ``ALWAYS`` passes through, ``NEVER`` denies, and ``AFTER_APPROVAL`` asks the
  injected :class:`ApprovalEngine` (denying outright under a degraded config,
  and failing closed when no engine is attached).
"""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from types import SimpleNamespace
from typing import Any

import pytest

from mcp_coder.icoder.permissions import (
    ArgPredicate,
    Default,
    Frame,
    Layer,
    Matcher,
    PermissionConfig,
    PermissionFrame,
    Policy,
    Rule,
)
from mcp_coder.icoder.permissions.approval import ApprovalDecision, ApprovalEngine
from mcp_coder.icoder.permissions.gateway import (
    _DENY_ASK,
    _DENY_NEVER,
    _DENY_USER,
    LangchainEnforcementGateway,
    _source_label,
)


def _rule(
    server: str,
    tool: str,
    policy: Policy,
    *,
    arg: ArgPredicate | None = None,
    layer: str = "user",
) -> Rule:
    """Build a Rule from a concrete server/tool, policy, and optional arg."""
    return Rule(
        matcher=Matcher(server=server, tool=tool, arg=arg),
        policy=policy,
        layer=layer,
    )


def _tool(canonical: str | None) -> SimpleNamespace:
    """Build a fake tool object carrying its canonical name."""
    return SimpleNamespace(canonical=canonical)


def _canonical_of(tool: Any) -> str | None:
    """Resolve a fake tool's canonical name."""
    return tool.canonical  # type: ignore[no-any-return]


def _request(
    server_name: str,
    name: str,
    args: dict[str, Any] | None = None,
    tool_call_id: str = "call_1",
) -> Any:
    """Build a fake adapter request, incl. the langgraph runtime ToolNode injects."""
    return SimpleNamespace(
        server_name=server_name,
        name=name,
        args=args or {},
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


class _FakeEngine(ApprovalEngine):
    """A scripted engine: records every ask, then answers or raises.

    Subclasses the real engine so the gateway's ``ApprovalEngine`` parameter
    type is honoured without a cast, while never touching a future or a loop.
    """

    def __init__(
        self,
        decision: ApprovalDecision | None = None,
        *,
        attached: bool = True,
        raises: type[BaseException] | None = None,
    ) -> None:
        """Script one answer, the attached state, and an optional raise.

        Args:
            decision: The answer to return (defaults to a plain allow).
            attached: What :meth:`is_attached` reports.
            raises: Exception type raised instead of answering.
        """
        super().__init__()
        self.decision = decision or ApprovalDecision("allow")
        self.attached = attached
        self.raises = raises
        self.asked: list[tuple[str, dict[str, object], str]] = []

    def is_attached(self) -> bool:
        """Report the scripted attached state.

        Returns:
            ``True`` when this stub pretends to hold an event sink.
        """
        return self.attached

    async def request_approval(
        self, *, tool_name: str, args: Mapping[str, object], source: str
    ) -> ApprovalDecision:
        """Record the ask, then raise or return the scripted decision.

        Args:
            tool_name: The canonical tool name the gateway asked about.
            args: The call arguments.
            source: The flattened decision provenance.

        Returns:
            The scripted :class:`ApprovalDecision`.

        Raises:
            BaseException: The scripted ``raises`` type, when one was given.
        """
        self.asked.append((tool_name, dict(args), source))
        if self.raises is not None:
            raise self.raises()
        return self.decision


@pytest.fixture(autouse=True)
def _fake_deny_bridge(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stub the langchain deny bridge so gateway tests need no ``langchain_core``.

    The real ``ToolMessage`` shape is covered by the provider bridge test; here
    we only need the gateway to hand the bridge the correct text **and**
    tool_call id, so a plain namespace mirroring the deny shape suffices.
    """

    def _fake(text: str, name: str, tool_call_id: str) -> Any:
        return SimpleNamespace(
            content=text,
            status="error",
            name=name,
            tool_call_id=tool_call_id,
            type="tool",
        )

    monkeypatch.setattr(
        "mcp_coder.icoder.permissions.gateway.build_deny_tool_message", _fake
    )


# ======================================================================
# filter_tools (turn level)
# ======================================================================


def test_filter_tools_drops_never_keeps_always_and_ask() -> None:
    """Unconditional ``never`` is hidden; ``always`` and ``ask`` stay visible."""
    config = PermissionConfig(
        rules=(
            _rule("s", "n", Policy.NEVER),
            _rule("s", "a", Policy.ALWAYS),
            _rule("s", "k", Policy.AFTER_APPROVAL),
        )
    )
    gateway = LangchainEnforcementGateway(config)
    never_tool = _tool("mcp__s__n")
    always_tool = _tool("mcp__s__a")
    ask_tool = _tool("mcp__s__k")

    kept = gateway.filter_tools([never_tool, always_tool, ask_tool], _canonical_of)

    assert never_tool not in kept
    assert always_tool in kept
    assert ask_tool in kept


def test_filter_tools_does_not_mutate_input() -> None:
    """The input list is never mutated; a new list is returned (cache-safe)."""
    config = PermissionConfig(rules=(_rule("s", "n", Policy.NEVER),))
    gateway = LangchainEnforcementGateway(config)
    never_tool = _tool("mcp__s__n")
    always_tool = _tool("mcp__s__a")
    tools = [never_tool, always_tool]
    original = list(tools)

    kept = gateway.filter_tools(tools, _canonical_of)

    assert tools == original  # unchanged: both tools still present
    assert kept is not tools


def test_filter_tools_keeps_frame_elevated_never() -> None:
    """A config-``never`` tool elevated by a synthetic frame stays visible."""
    config = PermissionConfig(rules=(_rule("s", "t", Policy.NEVER),))
    gateway = LangchainEnforcementGateway(config)
    frame = PermissionFrame(base="inherit", allow=(Matcher("s", "t"),))
    gateway.begin_turn(frame)
    tool = _tool("mcp__s__t")

    kept = gateway.filter_tools([tool], _canonical_of)

    assert tool in kept


def test_filter_tools_keeps_arg_scoped_never_visible() -> None:
    """An arg-scoped ``never`` stays visible (refused later at call level)."""
    arg = ArgPredicate(name="command", value="push")
    config = PermissionConfig(rules=(_rule("git", "push", Policy.NEVER, arg=arg),))
    gateway = LangchainEnforcementGateway(config)
    tool = _tool("mcp__git__push")

    kept = gateway.filter_tools([tool], _canonical_of)

    assert tool in kept


def test_filter_tools_keeps_non_mcp_tool() -> None:
    """A tool whose canonical name is ``None`` is never hidden."""
    config = PermissionConfig(rules=(_rule("s", "t", Policy.NEVER),))
    gateway = LangchainEnforcementGateway(config)
    tool = _tool(None)

    kept = gateway.filter_tools([tool], _canonical_of)

    assert tool in kept


# ======================================================================
# interceptor (call level)
# ======================================================================


@pytest.mark.asyncio
async def test_interceptor_always_passes_through() -> None:
    """``always`` awaits the real handler and returns its result unchanged."""
    config = PermissionConfig(rules=(_rule("s", "t", Policy.ALWAYS),))
    gateway = LangchainEnforcementGateway(config)
    sentinel = object()
    handler = _Handler(sentinel)

    result = await gateway.interceptor(_request("s", "t"), handler)

    assert handler.awaited
    assert result is sentinel


@pytest.mark.asyncio
async def test_interceptor_never_denies_without_awaiting_handler() -> None:
    """``never`` denies with the never text; the real handler is not awaited."""
    config = PermissionConfig(rules=(_rule("s", "t", Policy.NEVER),))
    gateway = LangchainEnforcementGateway(config)
    handler = _Handler(object())

    result = await gateway.interceptor(_request("s", "t"), handler)

    assert not handler.awaited
    assert result.status == "error"
    assert result.content == _DENY_NEVER


@pytest.mark.asyncio
async def test_interceptor_ask_denies_with_approval_text() -> None:
    """``ask`` with no engine injected fails closed with the fallback text."""
    config = PermissionConfig(rules=(_rule("s", "t", Policy.AFTER_APPROVAL),))
    gateway = LangchainEnforcementGateway(config)
    handler = _Handler(object())

    result = await gateway.interceptor(_request("s", "t"), handler)

    assert not handler.awaited
    assert result.status == "error"
    assert result.content == _DENY_ASK


@pytest.mark.asyncio
async def test_interceptor_skill_elevated_never_stays_callable() -> None:
    """A config-``never`` elevated by the active frame is called, not denied."""
    config = PermissionConfig(rules=(_rule("s", "t", Policy.NEVER),))
    gateway = LangchainEnforcementGateway(config)
    frame = PermissionFrame(base="inherit", allow=(Matcher("s", "t"),))
    gateway.begin_turn(frame)
    sentinel = object()
    handler = _Handler(sentinel)

    result = await gateway.interceptor(_request("s", "t"), handler)

    assert handler.awaited
    assert result is sentinel


@pytest.mark.asyncio
async def test_interceptor_never_carries_tool_call_id() -> None:
    """A ``never`` denial carries the emitted tool_call id (history stays paired)."""
    config = PermissionConfig(rules=(_rule("s", "t", Policy.NEVER),))
    gateway = LangchainEnforcementGateway(config)
    handler = _Handler(object())

    result = await gateway.interceptor(
        _request("s", "t", tool_call_id="call_7"), handler
    )

    assert result.content == _DENY_NEVER
    assert result.tool_call_id == "call_7"


@pytest.mark.asyncio
async def test_interceptor_ask_carries_tool_call_id() -> None:
    """A fail-closed ``ask`` denial carries the emitted id (same bridge call)."""
    config = PermissionConfig(rules=(_rule("s", "t", Policy.AFTER_APPROVAL),))
    gateway = LangchainEnforcementGateway(config)
    handler = _Handler(object())

    result = await gateway.interceptor(
        _request("s", "t", tool_call_id="call_7"), handler
    )

    assert result.content == _DENY_ASK
    assert result.tool_call_id == "call_7"


@pytest.mark.asyncio
async def test_interceptor_deny_without_runtime_uses_empty_id() -> None:
    """No ``runtime`` on the request (outside a graph) -> the id falls back to ``""``."""
    config = PermissionConfig(rules=(_rule("s", "t", Policy.NEVER),))
    gateway = LangchainEnforcementGateway(config)
    handler = _Handler(object())
    request = SimpleNamespace(server_name="s", name="t", args={})

    result = await gateway.interceptor(request, handler)

    assert result.content == _DENY_NEVER
    assert result.tool_call_id == ""


@pytest.mark.asyncio
async def test_interceptor_reconstructs_canonical_name() -> None:
    """``server_name`` + ``name`` reconstruct the canonical name the rule matches."""
    config = PermissionConfig(rules=(_rule("s", "t", Policy.NEVER),))
    gateway = LangchainEnforcementGateway(config)
    handler = _Handler(object())

    result = await gateway.interceptor(_request("s", "t"), handler)

    assert not handler.awaited  # the mcp__s__t rule matched -> denied
    assert result.content == _DENY_NEVER


@pytest.mark.asyncio
async def test_interceptor_disambiguates_same_bare_name_across_servers() -> None:
    """Same bare tool name on two servers resolves per canonical server identity."""
    config = PermissionConfig(
        rules=(
            _rule("a", "run", Policy.NEVER),
            _rule("b", "run", Policy.ALWAYS),
        )
    )
    gateway = LangchainEnforcementGateway(config)
    sentinel = object()
    handler_a = _Handler(object())
    handler_b = _Handler(sentinel)

    result_a = await gateway.interceptor(_request("a", "run"), handler_a)
    result_b = await gateway.interceptor(_request("b", "run"), handler_b)

    assert not handler_a.awaited
    assert result_a.status == "error"
    assert handler_b.awaited
    assert result_b is sentinel


@pytest.mark.asyncio
async def test_interceptor_honours_latest_frame() -> None:
    """``begin_turn`` overwrites the active frame; the interceptor reads the latest."""
    config = PermissionConfig(rules=(_rule("s", "t", Policy.NEVER),))
    gateway = LangchainEnforcementGateway(config)
    gateway.begin_turn(None)  # would deny on its own
    frame = PermissionFrame(base="inherit", allow=(Matcher("s", "t"),))
    gateway.begin_turn(frame)  # elevates
    sentinel = object()
    handler = _Handler(sentinel)

    result = await gateway.interceptor(_request("s", "t"), handler)

    assert handler.awaited
    assert result is sentinel


# ======================================================================
# interceptor: the real AFTER_APPROVAL branch (Step 6 of I3.2)
# ======================================================================


@pytest.mark.asyncio
async def test_interceptor_ask_allowed_runs_the_real_handler() -> None:
    """An ``allow`` answer awaits the real handler and returns its result."""
    config = PermissionConfig(rules=(_rule("s", "t", Policy.AFTER_APPROVAL),))
    engine = _FakeEngine(ApprovalDecision("allow"))
    gateway = LangchainEnforcementGateway(config, engine)
    sentinel = object()
    handler = _Handler(sentinel)

    result = await gateway.interceptor(_request("s", "t", {"path": "x"}), handler)

    assert handler.awaited
    assert result is sentinel
    assert engine.asked == [("mcp__s__t", {"path": "x"}, "user")]


@pytest.mark.asyncio
async def test_interceptor_ask_denied_uses_user_wording_and_real_id() -> None:
    """A ``deny`` answer returns the R11 wording with the emitted tool_call id."""
    config = PermissionConfig(rules=(_rule("s", "t", Policy.AFTER_APPROVAL),))
    engine = _FakeEngine(ApprovalDecision("deny"))
    gateway = LangchainEnforcementGateway(config, engine)
    handler = _Handler(object())

    result = await gateway.interceptor(
        _request("s", "t", tool_call_id="call_9"), handler
    )

    assert not handler.awaited
    assert result.status == "error"
    assert result.content == _DENY_USER
    assert result.tool_call_id == "call_9"


@pytest.mark.asyncio
async def test_interceptor_ask_denied_reason_overrides_user_wording() -> None:
    """A deny carrying ``reason`` reports that text, not the user-deny wording."""
    config = PermissionConfig(rules=(_rule("s", "t", Policy.AFTER_APPROVAL),))
    engine = _FakeEngine(ApprovalDecision("deny", "once", reason="no prompt reachable"))
    gateway = LangchainEnforcementGateway(config, engine)
    handler = _Handler(object())

    result = await gateway.interceptor(_request("s", "t"), handler)

    assert not handler.awaited
    assert result.content == "no prompt reachable"


@pytest.mark.asyncio
async def test_interceptor_ask_propagates_cancelled_error() -> None:
    """``CancelledError`` from the engine unwinds the turn, never a deny."""
    config = PermissionConfig(rules=(_rule("s", "t", Policy.AFTER_APPROVAL),))
    engine = _FakeEngine(raises=asyncio.CancelledError)
    gateway = LangchainEnforcementGateway(config, engine)
    handler = _Handler(object())

    with pytest.raises(asyncio.CancelledError):
        await gateway.interceptor(_request("s", "t"), handler)

    assert not handler.awaited


@pytest.mark.asyncio
async def test_interceptor_degraded_denies_without_asking() -> None:
    """A degraded config denies outright — no approval is ever requested (R15)."""
    config = PermissionConfig(
        rules=(_rule("s", "t", Policy.ALWAYS),),
        degraded=True,
        errors=("bad json",),
    )
    engine = _FakeEngine(ApprovalDecision("allow"))
    gateway = LangchainEnforcementGateway(config, engine)
    handler = _Handler(object())

    result = await gateway.interceptor(
        _request("s", "t", tool_call_id="call_3"), handler
    )

    assert not handler.awaited
    assert result.content == _DENY_NEVER
    assert result.tool_call_id == "call_3"
    assert engine.asked == []


@pytest.mark.asyncio
async def test_interceptor_ask_without_engine_fails_closed() -> None:
    """No engine at all -> the fallback deny, with the emitted tool_call id."""
    config = PermissionConfig(rules=(_rule("s", "t", Policy.AFTER_APPROVAL),))
    gateway = LangchainEnforcementGateway(config, None)
    handler = _Handler(object())

    result = await gateway.interceptor(
        _request("s", "t", tool_call_id="call_4"), handler
    )

    assert not handler.awaited
    assert result.content == _DENY_ASK
    assert result.tool_call_id == "call_4"


@pytest.mark.asyncio
async def test_interceptor_ask_with_detached_engine_fails_closed() -> None:
    """A detached engine is never asked: nothing would resolve that future."""
    config = PermissionConfig(rules=(_rule("s", "t", Policy.AFTER_APPROVAL),))
    engine = _FakeEngine(ApprovalDecision("allow"), attached=False)
    gateway = LangchainEnforcementGateway(config, engine)
    handler = _Handler(object())

    result = await gateway.interceptor(
        _request("s", "t", tool_call_id="call_5"), handler
    )

    assert not handler.awaited
    assert result.content == _DENY_ASK
    assert result.tool_call_id == "call_5"
    assert engine.asked == []


# ======================================================================
# runtime-rule store + source flattening
# ======================================================================


@pytest.mark.asyncio
async def test_add_runtime_rule_grants_later_calls_in_the_same_turn() -> None:
    """A runtime ``always`` added mid-turn makes the next call pass through (R14)."""
    config = PermissionConfig(rules=(_rule("s", "t", Policy.AFTER_APPROVAL),))
    gateway = LangchainEnforcementGateway(config)
    first = await gateway.interceptor(_request("s", "t"), _Handler(object()))

    assert first.content == _DENY_ASK  # ask, nobody attached -> fail closed

    gateway.add_runtime_rule(_rule("s", "t", Policy.ALWAYS, layer="runtime"))
    sentinel = object()
    handler = _Handler(sentinel)

    result = await gateway.interceptor(_request("s", "t"), handler)

    assert handler.awaited
    assert result is sentinel


def test_add_runtime_rule_keeps_the_original_rules() -> None:
    """The store appends: earlier rules survive the frozen-config rebind."""
    authored = _rule("s", "other", Policy.NEVER)
    gateway = LangchainEnforcementGateway(PermissionConfig(rules=(authored,)))

    gateway.add_runtime_rule(_rule("s", "t", Policy.ALWAYS, layer="runtime"))
    kept = gateway.filter_tools([_tool("mcp__s__other")], _canonical_of)

    assert kept == []  # the authored never still hides its tool


def test_source_label_flattens_every_reachable_source() -> None:
    """``Layer``/``Default``/``Frame`` flatten to plain JSON-safe strings."""
    assert _source_label(Layer("project")) == "project"
    assert _source_label(Default()) == "default"
    assert _source_label(Frame()) == "frame"
