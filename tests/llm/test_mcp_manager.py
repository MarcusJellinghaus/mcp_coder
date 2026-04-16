"""Tests for MCPManager persistent MCP client."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcp_coder.llm.providers.langchain.mcp_manager import MCPManager, MCPServerStatus


def _make_mock_tool(name: str = "test_tool") -> MagicMock:
    """Create a mock MCP tool with the expected interface."""
    tool = MagicMock()
    tool.inputSchema = {"type": "object", "properties": {}}
    tool.model_copy = MagicMock(return_value=tool)
    tool.name = name
    return tool


def _make_list_tools_result(tools: list[MagicMock]) -> SimpleNamespace:
    """Create a mock list_tools() result."""
    return SimpleNamespace(tools=tools)


def _build_mock_client(
    server_tools: dict[str, list[MagicMock]],
) -> MagicMock:
    """Build a mock MultiServerMCPClient with given servers and tools.

    Args:
        server_tools: mapping of server_name -> list of mock tools
    """
    client = MagicMock()

    connections: dict[str, MagicMock] = {}
    sessions: dict[str, AsyncMock] = {}

    for server_name, tools in server_tools.items():
        conn = MagicMock()
        connections[server_name] = conn

        session = AsyncMock()
        session.list_tools = AsyncMock(return_value=_make_list_tools_result(tools))
        sessions[server_name] = session

    client.connections = connections

    # client.session(name) returns an async context manager
    def _session_factory(name: str) -> AsyncMock:
        ctx = AsyncMock()
        ctx.__aenter__ = AsyncMock(return_value=sessions[name])
        ctx.__aexit__ = AsyncMock(return_value=False)
        return ctx

    client.session = MagicMock(side_effect=_session_factory)
    client.__aexit__ = AsyncMock(return_value=None)

    return client


def _patch_client_and_convert(
    server_tools: dict[str, list[MagicMock]],
) -> tuple[Any, Any, Any, Any]:
    """Create patches for MultiServerMCPClient and convert_mcp_tool_to_langchain_tool."""
    mock_client = _build_mock_client(server_tools)
    client_cls = patch(
        "langchain_mcp_adapters.client.MultiServerMCPClient",
        return_value=mock_client,
    )
    lc_tools_created: list[MagicMock] = []

    def _convert(*_args: Any, **_kwargs: Any) -> MagicMock:
        t = MagicMock(name=f"lc_tool_{len(lc_tools_created)}")
        lc_tools_created.append(t)
        return t

    convert_fn = patch(
        "langchain_mcp_adapters.tools.convert_mcp_tool_to_langchain_tool",
        side_effect=_convert,
    )
    return client_cls, convert_fn, lc_tools_created, mock_client


class TestMCPManagerTools:
    """Tests for MCPManager.tools() method."""

    def test_tools_returns_cached_tools(self) -> None:
        """After first call, second call returns same list without reconnecting."""
        tool1 = _make_mock_tool("tool_a")
        client_patch, convert_patch, _lc_tools, _mock_client = (
            _patch_client_and_convert({"server1": [tool1]})
        )

        with client_patch, convert_patch:
            manager = MCPManager({"server1": {"transport": "stdio"}})
            try:
                first = manager.tools()
                second = manager.tools()
                assert first is second
                assert len(first) == 1
            finally:
                manager.close()

    def test_tools_lazy_connect(self) -> None:
        """Constructor does NOT connect; connection happens on first tools() call."""
        client_patch, convert_patch, _, _mock_client = _patch_client_and_convert(
            {"server1": [_make_mock_tool()]}
        )

        with client_patch as client_cls:
            with convert_patch:
                manager = MCPManager({"server1": {"transport": "stdio"}})
                try:
                    # Not called yet at construction time
                    client_cls.assert_not_called()

                    # First tools() triggers connection
                    manager.tools()
                    client_cls.assert_called_once()
                finally:
                    manager.close()

    def test_tools_recreates_on_failure(self) -> None:
        """If _connect_and_discover fails, next tools() call retries."""
        manager = MCPManager({"server1": {"transport": "stdio"}})
        call_count = 0

        async def _failing_then_ok() -> list[Any]:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("first attempt fails")
            return [MagicMock(name="recovered_tool")]

        try:
            with patch.object(
                manager, "_connect_and_discover", side_effect=_failing_then_ok
            ):
                with pytest.raises(ConnectionError):
                    manager.tools()

                # Cache cleared — next call retries
                result = manager.tools()
                assert len(result) == 1
                assert call_count == 2
        finally:
            manager.close()

    def test_empty_server_config(self) -> None:
        """Empty config returns empty tools list."""
        client_patch, convert_patch, _, _ = _patch_client_and_convert({})

        with client_patch, convert_patch:
            manager = MCPManager({})
            try:
                result = manager.tools()
                assert result == []
            finally:
                manager.close()


class TestMCPManagerStatus:
    """Tests for MCPManager.status() method."""

    def test_status_before_connect(self) -> None:
        """Returns all servers as connected=False, tool_count=0."""
        manager = MCPManager(
            {
                "server_a": {"transport": "stdio"},
                "server_b": {"transport": "stdio"},
            }
        )
        try:
            statuses = manager.status()
            assert len(statuses) == 2
            for s in statuses:
                assert isinstance(s, MCPServerStatus)
                assert s.connected is False
                assert s.tool_count == 0
            assert statuses[0].name == "server_a"
            assert statuses[1].name == "server_b"
        finally:
            manager.close()

    def test_status_after_connect(self) -> None:
        """Returns servers as connected=True with correct tool counts."""
        tool1 = _make_mock_tool("t1")
        tool2 = _make_mock_tool("t2")
        tool3 = _make_mock_tool("t3")

        client_patch, convert_patch, _, _ = _patch_client_and_convert(
            {
                "alpha": [tool1, tool2],
                "beta": [tool3],
            }
        )

        config: dict[str, dict[str, object]] = {
            "alpha": {"transport": "stdio"},
            "beta": {"transport": "stdio"},
        }

        with client_patch, convert_patch:
            manager = MCPManager(config)
            try:
                manager.tools()  # triggers connection
                statuses = manager.status()

                assert len(statuses) == 2
                alpha_status = next(s for s in statuses if s.name == "alpha")
                beta_status = next(s for s in statuses if s.name == "beta")

                assert alpha_status.connected is True
                assert alpha_status.tool_count == 2
                assert beta_status.connected is True
                assert beta_status.tool_count == 1
            finally:
                manager.close()


class TestMCPManagerClose:
    """Tests for MCPManager.close() method."""

    def test_close_stops_loop(self) -> None:
        """After close(), background thread is no longer alive."""
        manager = MCPManager({"s1": {"transport": "stdio"}})
        assert manager._thread.is_alive()
        manager.close()
        assert not manager._thread.is_alive()

    def test_close_idempotent(self) -> None:
        """Calling close() twice does not raise."""
        manager = MCPManager({"s1": {"transport": "stdio"}})
        manager.close()
        manager.close()  # Should not raise
