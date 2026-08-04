"""Tests for the iCoder enforcement gateway (Step 3 of I2.3, TDD).

Exercises the gateway in isolation with fake tool objects and a fake async
handler — no live MCP server, no agent. Covers the two enforcement seams:

* :meth:`LangchainEnforcementGateway.filter_tools` — turn-level visibility:
  unconditional ``NEVER`` hidden, arg-scoped ``NEVER`` kept visible.
* :meth:`LangchainEnforcementGateway.interceptor` — call-level enforcement:
  ``ALWAYS`` passes through, ``NEVER``/``AFTER_APPROVAL`` deny.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from mcp_coder.icoder.permissions import (
    ArgPredicate,
    Matcher,
    PermissionConfig,
    PermissionFrame,
    Policy,
    Rule,
)
from mcp_coder.icoder.permissions.gateway import (
    _DENY_ASK,
    _DENY_NEVER,
    LangchainEnforcementGateway,
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


def _request(server_name: str, name: str, args: dict[str, Any] | None = None) -> Any:
    """Build a fake adapter request object."""
    return SimpleNamespace(server_name=server_name, name=name, args=args or {})


class _Handler:
    """A fake async tool handler that records whether it was awaited."""

    def __init__(self, result: Any) -> None:
        self.result = result
        self.awaited = False

    async def __call__(self, request: Any) -> Any:
        self.awaited = True
        return self.result


@pytest.fixture(autouse=True)
def _fake_deny_bridge(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stub the langchain deny bridge so gateway tests need no ``langchain_core``.

    The real ``ToolMessage`` shape is covered by the provider bridge test; here
    we only need the gateway to hand the bridge the correct text, so a plain
    namespace mirroring the deny shape suffices.
    """

    def _fake(text: str, name: str) -> Any:
        return SimpleNamespace(content=text, status="error", name=name, type="tool")

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
    """``ask`` denies at call level with the approval text (M2 has no prompt yet)."""
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
