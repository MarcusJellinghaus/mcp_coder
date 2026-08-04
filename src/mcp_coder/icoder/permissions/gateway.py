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
  ``NEVER``/``AFTER_APPROVAL`` return a deny ``ToolMessage`` built by the
  provider bridge (:func:`build_deny_tool_message`) so this module never imports
  ``langchain_core``.

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
from typing import Any

from mcp_coder.icoder.permissions.model import (
    PermissionConfig,
    PermissionFrame,
    Policy,
)
from mcp_coder.icoder.permissions.resolver import resolve
from mcp_coder.llm.providers.langchain.permission_bridge import (
    build_deny_tool_message,
)

_DENY_NEVER = "This tool is disabled by permission policy."
_DENY_ASK = "This tool requires approval — not yet available."


class LangchainEnforcementGateway:
    """Turn- and call-level permission enforcement over the pure resolver.

    A single instance is built at iCoder startup from the loaded
    :class:`PermissionConfig`. The per-turn frame is held on a mutable field
    (``_frame``) set by :meth:`begin_turn`; both the turn filter and the
    interceptor read it. This is valid under the sequential-turn assumption.
    """

    def __init__(self, config: PermissionConfig) -> None:
        """Store the immutable config and initialise an empty per-turn frame.

        Args:
            config: The merged permission config for this session.
        """
        self._config = config
        self._frame: PermissionFrame | None = None

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
        ``request.name``, resolves it, and either awaits the real ``handler``
        (``ALWAYS``) or returns a deny ``ToolMessage`` (``NEVER`` /
        ``AFTER_APPROVAL``).

        Args:
            request: The adapter tool-call request (``.server_name``, ``.name``,
                ``.args``).
            handler: The downstream async handler that performs the real call.

        Returns:
            The real handler result for ``ALWAYS``, else a deny ``ToolMessage``.
        """
        canonical = f"mcp__{request.server_name}__{request.name}"
        policy = resolve(canonical, request.args, self._frame, self._config).policy
        if policy is Policy.ALWAYS:
            return await handler(request)
        text = _DENY_ASK if policy is Policy.AFTER_APPROVAL else _DENY_NEVER
        return build_deny_tool_message(text, request.name)
