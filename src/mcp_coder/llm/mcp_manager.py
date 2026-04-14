"""Persistent MCP client manager for long-lived MCP server connections.

Owns MCP server connections for the app's lifetime via a background daemon
thread with its own asyncio event loop. Lazy: connects on first tools() call.
"""

from __future__ import annotations

import asyncio
import logging
import threading
from dataclasses import dataclass
from typing import Any, cast

from mcp_coder.llm.providers.langchain.agent import (  # noqa: PLC2701
    _sanitize_tool_schema,
)

logger = logging.getLogger(__name__)


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
