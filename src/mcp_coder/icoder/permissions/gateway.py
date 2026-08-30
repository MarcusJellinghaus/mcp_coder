"""Enforcement gateway for the iCoder permission system (the langchain seam).

Sits between MCP tool discovery (``MCPManager``) and the langchain agent, and
enforces the 3-valued policy at two seams using only the pure I2.1 resolver and
I2.2 loader:

* **Turn level** — :meth:`LangchainEnforcementGateway.filter_tools` hides a tool
  from the model when it is *unconditionally* ``NEVER``. An arg-scoped ``never``
  stays visible (predicate matching is parse-only in M2) and is refused later at
  call level.
* **Call level** — :meth:`LangchainEnforcementGateway.interceptor` is the async
  ``langchain-mcp-adapters`` hook: ``ALWAYS`` passes through to the real handler;
  ``NEVER`` returns a deny ``ToolMessage``; ``AFTER_APPROVAL`` asks the injected
  :class:`ApprovalEngine` and then runs the call or denies. Every deny
  ``ToolMessage`` is built by the provider bridge
  (:func:`build_deny_tool_message`) so this module never imports
  ``langchain_core`` — and it is built **here**, never in the engine, which must
  stay a leaf (R6).

Frame *construction* lives elsewhere: the pure
:func:`mcp_coder.icoder.permissions.skill_frame.build_frame` maps any skill
declaration to a :class:`PermissionFrame`, and ``AppCore`` installs the resolved
frame per turn via :meth:`LangchainEnforcementGateway.begin_turn`. This gateway
is enforcement-only — it never parses tokens or builds frames.

Adapter request/result/handler objects are annotated ``Any``: this module imports
only the pure permission core (resolver/model/matcher) plus the provider deny
bridge — never ``langchain_core`` or ``langchain_mcp_adapters`` directly.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import replace
from typing import Any

from mcp_coder.icoder.permissions.approval import ApprovalEngine
from mcp_coder.icoder.permissions.model import (
    Degraded,
    Frame,
    Layer,
    PermissionConfig,
    PermissionFrame,
    Policy,
    Rule,
    Source,
)
from mcp_coder.icoder.permissions.resolver import resolve
from mcp_coder.llm.providers.langchain.permission_bridge import (
    build_deny_tool_message,
)

_DENY_NEVER = "This tool is disabled by permission policy."
# Fail-closed fallback: an ``ask`` reached the seam with no engine able to prompt.
_DENY_ASK = "This tool requires approval — not yet available."
# R11 — canonical wording for a real refusal. Used unless the decision carries
# its own ``reason`` (see the AFTER_APPROVAL branch of :meth:`interceptor`).
_DENY_USER = (
    "Tool call denied by the user. Do not retry this call — choose a "
    "different approach, or ask the user what they would prefer."
)


def _source_label(source: Source) -> str:
    """Flatten a :class:`Decision` source to a JSON-safe plain string.

    Args:
        source: The tagged-union source of the decision that asked.

    Returns:
        The layer name for a :class:`Layer`, else ``"frame"`` / ``"default"``.
    """
    if isinstance(source, Layer):
        return source.name
    if isinstance(source, Frame):
        return "frame"
    # ``Degraded`` never reaches here: :meth:`interceptor` denies every
    # ``Degraded``-sourced decision before it can ask (R15). No branch for it.
    return "default"


class LangchainEnforcementGateway:
    """Turn- and call-level permission enforcement over the pure resolver.

    A single instance is built at iCoder startup from the loaded
    :class:`PermissionConfig`. The per-turn frame is held on a mutable field
    (``_frame``) set by :meth:`begin_turn`; both the turn filter and the
    interceptor read it. This is valid under the sequential-turn assumption.
    """

    def __init__(
        self,
        config: PermissionConfig,
        approval_engine: ApprovalEngine | None = None,
    ) -> None:
        """Store the immutable config, the engine, and an empty per-turn frame.

        Args:
            config: The merged permission config for this session.
            approval_engine: The engine that prompts on ``AFTER_APPROVAL``.
                ``None`` (or a detached engine) makes every ``ask`` fail closed.
        """
        self._config = config
        self._engine = approval_engine
        self._frame: PermissionFrame | None = None

    def add_runtime_rule(self, rule: Rule) -> None:
        """Append a rule to the in-memory ``runtime`` layer.

        Written by the approval UI (I3.3) when a user grants a durable scope;
        the engine never writes here. ``PermissionConfig`` is frozen, so this
        rebinds one attribute — atomic under the GIL, hence no lock, and both
        :meth:`filter_tools` and :meth:`interceptor` read ``self._config`` live.

        A rule added mid-turn **is** visible to every later call-level
        :func:`resolve`, but it cannot un-hide a ``never`` tool in the same
        turn: :meth:`filter_tools` is a turn-start snapshot.

        Args:
            rule: The runtime-layer rule to append.
        """
        self._config = replace(self._config, rules=self._config.rules + (rule,))

    def begin_turn(self, frame: PermissionFrame | None) -> None:
        """Install the frame active for the coming turn.

        Args:
            frame: The per-turn permission frame, or ``None`` for config-only.
        """
        self._frame = frame

    def filter_tools(
        self, tools: list[Any], canonical_name_of: Callable[[Any], str | None]
    ) -> list[Any]:
        """Return a filtered copy of ``tools`` with unconditional NEVERs hidden.

        Never mutates the input list. A tool is hidden only when its decision is
        ``NEVER`` **and** the matched rule is unconditional (absent, or its
        matcher carries no arg predicate). An arg-scoped ``never`` stays visible
        and is refused at call level (predicate matching is parse-only in M2).

        Args:
            tools: The discovered tool objects.
            canonical_name_of: Maps a tool to its ``mcp__server__tool`` name, or
                ``None`` for a non-MCP tool (never hidden).

        Returns:
            A new list holding the kept tools.
        """
        kept: list[Any] = []
        for tool in tools:
            name = canonical_name_of(tool)
            if name is None:
                kept.append(tool)
                continue
            decision = resolve(name, {}, self._frame, self._config)
            if decision.policy is not Policy.NEVER:
                kept.append(tool)
                continue
            rule = decision.matched_rule
            if rule is not None and rule.matcher.arg is not None:
                kept.append(tool)  # arg-scoped never -> visible, refused at call
        return kept

    async def interceptor(
        self, request: Any, handler: Callable[[Any], Awaitable[Any]]
    ) -> Any:
        """Enforce policy on a single tool call (the adapter's async hook).

        Reconstructs the canonical name from ``request.server_name`` +
        ``request.name`` and resolves it. ``ALWAYS`` awaits the real ``handler``;
        ``NEVER`` denies; ``AFTER_APPROVAL`` pauses on the approval engine and
        then runs the call or denies.

        Args:
            request: The adapter tool-call request (``.server_name``, ``.name``,
                ``.args``, plus ``.runtime`` carrying the emitted
                ``tool_call_id`` inside a langgraph run).
            handler: The downstream async handler that performs the real call.

        Returns:
            The real handler result when the call is permitted, else a deny
            ``ToolMessage`` carrying the emitted ``tool_call_id``.
        """
        canonical = f"mcp__{request.server_name}__{request.name}"
        decision = resolve(canonical, request.args, self._frame, self._config)
        tool_call_id = (
            getattr(getattr(request, "runtime", None), "tool_call_id", None) or ""
        )
        if decision.policy is Policy.ALWAYS:
            return await handler(request)
        if decision.policy is Policy.NEVER:
            return build_deny_tool_message(_DENY_NEVER, request.name, tool_call_id)

        # AFTER_APPROVAL. A degraded config short-circuits to ``ask`` *before*
        # any rule is consulted, so prompting here would mean a modal on every
        # MCP call for the whole session, with no session grant able to stop it
        # (R15). Deny outright instead — never emit.
        if isinstance(decision.source, Degraded):
            return build_deny_tool_message(_DENY_NEVER, request.name, tool_call_id)
        engine = self._engine
        if engine is None or not engine.is_attached():
            # Fail closed rather than await a future nobody could resolve.
            return build_deny_tool_message(_DENY_ASK, request.name, tool_call_id)
        # ``CancelledError`` from the engine must PROPAGATE — it is how a
        # cancelled turn unwinds a parked interceptor. Never wrap this in a
        # ``try/except``: swallowing it would strand the agent thread.
        approved = await engine.request_approval(
            tool_name=canonical,
            args=request.args,
            source=_source_label(decision.source),
        )
        if approved.outcome == "allow":
            return await handler(request)
        # ``reason`` lets the answering side override the wording. Step 9's
        # interim UI auto-deny and the engine's own fail-closed deny both use
        # it, so a call nobody was asked about is not reported to the model as
        # a user denial.
        text = approved.reason or _DENY_USER
        return build_deny_tool_message(text, request.name, tool_call_id)
