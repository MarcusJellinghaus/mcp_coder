"""Persistent MCP client manager for long-lived MCP server connections.

Owns MCP server connections for the app's lifetime via a background daemon
thread with its own asyncio event loop. Lazy: connects on first tools() call.
"""

from __future__ import annotations

import asyncio
import logging
import threading
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, cast

from mcp_coder.llm.providers.langchain.agent import (  # noqa: PLC2701
    _sanitize_tool_schema,
)

logger = logging.getLogger(__name__)


def filter_tools_by_declaration(
    tools: list[Any],
    canonical_name_of: Callable[[Any], str | None],
    declared: tuple[str, ...] | list[str],
) -> tuple[list[Any], list[str]]:
    """Narrow ``tools`` to the exact MCP tokens in ``declared``.

    Returns ``(filtered_tools, warnings)``. ``declared`` is assumed
    truthy/non-empty (the caller treats a falsy declaration as "no
    narrowing"). Fail-closed: an empty allow-set yields an empty tool list;
    un-parseable tokens are dropped (never widen the set) and produce a
    warning.

    Args:
        tools: Live tool objects to narrow. Never mutated.
        canonical_name_of: Maps a tool to its ``mcp__server__tool`` token,
            or ``None`` when unknown.
        declared: Declared allow-list tokens from a skill's ``SKILL.md``.

    Returns:
        A tuple of the kept tools (a new list) and human-readable warning
        strings (empty when all tokens are exact or non-MCP).
    """
    allow: set[str] = set()
    warnings: list[str] = []
    for token in declared:
        if token.startswith("mcp__") and "*" not in token and "(" not in token:
            allow.add(token)  # exact mcp__server__tool
        elif token.startswith("mcp__") or token.startswith("@"):
            warnings.append(
                f"Skill tool declaration '{token}' is not supported yet "
                f"and was ignored; the skill runs with a reduced tool set."
            )
        # else: non-MCP / Bash-style / bare -> ignored, no warning
    filtered = [t for t in tools if canonical_name_of(t) in allow]
    return filtered, warnings


@dataclass(frozen=True)
class MCPServerStatus:
    """Status of a single MCP server connection."""

    name: str
    tool_count: int
    connected: bool


class MCPManager:
    """Persistent MCP client with background event loop.

    Owns MCP server connections for the app's lifetime.
    Lazy: connects on first tools() call, not at construction.

    Not thread-safe: callers must ensure tools() and close() are not called concurrently.
    """

    def __init__(
        self,
        server_config: dict[str, dict[str, object]],
    ) -> None:
        self._server_names = list(server_config.keys())
        self._server_config = server_config
        self._cached_tools: list[Any] | None = None
        self._client: Any | None = None
        self._tool_counts: dict[str, int] = {}

        # Create a dedicated event loop on a daemon thread
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(
            target=self._loop.run_forever,
            daemon=True,
            name="mcp-manager-loop",
        )
        self._thread.start()

    def canonical_name(self, tool: Any) -> str | None:
        """Return the stamped ``mcp__server__tool`` identity, or None if absent.

        Reads the ``mcp_canonical_name`` key stamped onto each tool's
        ``metadata`` during discovery. Pure and cache-safe: never triggers
        re-discovery and never mutates the tool.

        Args:
            tool: A LangChain tool object produced by discovery.

        Returns:
            The canonical ``mcp__server__tool`` token, or ``None`` when the
            metadata or key is missing or the stamped value is not a string.
        """
        meta = getattr(tool, "metadata", None) or {}
        value = meta.get("mcp_canonical_name")
        return value if isinstance(value, str) else None

    def tools(self) -> list[Any]:
        """Return cached LangChain tools. Connects lazily on first call.

        On failure, clears cache so the next call retries.
        """
        if self._cached_tools is not None:
            return self._cached_tools

        try:
            future = asyncio.run_coroutine_threadsafe(
                self._connect_and_discover(), self._loop
            )
            self._cached_tools = future.result(timeout=60)
        except Exception:
            # Clear so next call retries
            self._cached_tools = None
            self._client = None
            raise

        return self._cached_tools

    async def _connect_and_discover(self) -> list[Any]:
        """Connect to MCP servers and discover tools (runs on background loop).

        Returns:
            List of discovered LangChain-compatible tools from all servers.
        """
        from langchain_mcp_adapters.client import MultiServerMCPClient
        from langchain_mcp_adapters.tools import convert_mcp_tool_to_langchain_tool

        client = MultiServerMCPClient(cast(Any, self._server_config))
        self._client = client
        all_tools: list[Any] = []
        tool_counts: dict[str, int] = {}

        for server_name, connection in client.connections.items():
            count = 0
            async with client.session(server_name) as session:
                raw_tools = await session.list_tools()
                for tool in raw_tools.tools:
                    sanitized = _sanitize_tool_schema(tool.inputSchema)
                    tool = tool.model_copy(update={"inputSchema": sanitized})
                    lc_tool = convert_mcp_tool_to_langchain_tool(
                        None,
                        tool,
                        connection=connection,
                        server_name=server_name,
                    )
                    lc_tool.metadata = {
                        **(lc_tool.metadata or {}),
                        "mcp_canonical_name": f"mcp__{server_name}__{tool.name}",
                    }
                    all_tools.append(lc_tool)
                    count += 1
            tool_counts[server_name] = count

        self._tool_counts = tool_counts
        return all_tools

    def status(self) -> list[MCPServerStatus]:
        """Return connection status for each configured server."""
        connected = self._cached_tools is not None
        return [
            MCPServerStatus(
                name=name,
                tool_count=self._tool_counts.get(name, 0),
                connected=connected,
            )
            for name in self._server_names
        ]

    def close(self) -> None:
        """Shut down MCP servers, stop event loop, join thread."""
        if self._client is not None:
            try:
                future = asyncio.run_coroutine_threadsafe(
                    self._client.__aexit__(None, None, None), self._loop
                )
                future.result(timeout=5)
            except Exception:  # noqa: BLE001
                logger.debug("Error closing MCP client", exc_info=True)
            self._client = None

        if self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
            self._thread.join(timeout=5)

        self._cached_tools = None
        self._tool_counts = {}
