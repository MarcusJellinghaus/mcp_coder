"""Tests for the unified ``_convert_server_tools`` helper and interceptor pass-through.

Covers Step 2 of the I2.3 plan (Decision D1): the three near-duplicate
``convert_mcp_tool_to_langchain_tool`` build loops are collapsed into one shared
helper that accepts ``tool_interceptors``, and ``MCPManager`` gains a pass-through
``tool_interceptors`` constructor parameter. Every production site still passes
``None`` by default at this step.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcp_coder.llm.providers.langchain.agent import (
    _convert_server_tools,
    run_agent_stream,
)
from mcp_coder.llm.providers.langchain.mcp_manager import MCPManager

_PATCH_MCP_CLIENT = "langchain_mcp_adapters.client.MultiServerMCPClient"
_PATCH_CONVERT_TOOL = "langchain_mcp_adapters.tools.convert_mcp_tool_to_langchain_tool"
_PATCH_CREATE_AGENT = "langgraph.prebuilt.create_react_agent"
_PATCH_FROM_DICT = "langchain_core.messages.messages_from_dict"
_PATCH_STORE_HISTORY = "mcp_coder.llm.storage.session_storage.store_langchain_history"
_HELPER_IN_AGENT = "mcp_coder.llm.providers.langchain.agent._convert_server_tools"
_HELPER_IN_MANAGER = (
    "mcp_coder.llm.providers.langchain.mcp_manager._convert_server_tools"
)


def _make_raw_tool(
    name: str = "foo", input_schema: dict[str, Any] | None = None
) -> MagicMock:
    """Create a mock raw MCP tool whose ``model_copy`` applies the update."""
    tool = MagicMock()
    tool.name = name
    tool.inputSchema = (
        input_schema
        if input_schema is not None
        else {"type": "object", "properties": {}}
    )

    def _model_copy(update: dict[str, Any]) -> MagicMock:
        new = MagicMock()
        new.name = tool.name
        new.inputSchema = update["inputSchema"]
        return new

    tool.model_copy = MagicMock(side_effect=_model_copy)
    return tool


def _build_mock_client(server_tools: dict[str, list[MagicMock]]) -> MagicMock:
    """Build a mock MultiServerMCPClient with the given servers and raw tools."""
    client = MagicMock()
    connections: dict[str, MagicMock] = {}
    sessions: dict[str, AsyncMock] = {}

    for server_name, tools in server_tools.items():
        connections[server_name] = MagicMock()
        session = AsyncMock()
        session.list_tools = AsyncMock(return_value=SimpleNamespace(tools=tools))
        sessions[server_name] = session

    client.connections = connections

    def _session_factory(name: str) -> AsyncMock:
        ctx = AsyncMock()
        ctx.__aenter__ = AsyncMock(return_value=sessions[name])
        ctx.__aexit__ = AsyncMock(return_value=False)
        return ctx

    client.session = MagicMock(side_effect=_session_factory)
    client.__aexit__ = AsyncMock(return_value=None)
    return client


class TestConvertServerTools:
    """Unit tests for the standalone ``_convert_server_tools`` helper."""

    def test_convert_server_tools_forwards_interceptors(self) -> None:
        """A sentinel ``tool_interceptors`` is forwarded to convert per tool."""
        sentinel = [object()]
        raw_tools = [_make_raw_tool("foo"), _make_raw_tool("bar")]
        connection = MagicMock()

        with patch(_PATCH_CONVERT_TOOL, return_value=MagicMock()) as mock_convert:
            _convert_server_tools(
                raw_tools, connection, "srv", tool_interceptors=sentinel
            )

        assert mock_convert.call_count == 2
        for call in mock_convert.call_args_list:
            assert call.kwargs["tool_interceptors"] is sentinel

    def test_convert_server_tools_defaults_interceptors_to_none(self) -> None:
        """Omitting ``tool_interceptors`` forwards ``None`` to convert."""
        raw_tools = [_make_raw_tool("foo")]

        with patch(_PATCH_CONVERT_TOOL, return_value=MagicMock()) as mock_convert:
            _convert_server_tools(raw_tools, MagicMock(), "srv")

        assert mock_convert.call_args.kwargs["tool_interceptors"] is None

    def test_convert_server_tools_sanitizes_schema(self) -> None:
        """A typeless property gains ``\"type\": \"string\"`` before convert."""
        raw_tool = _make_raw_tool(
            "foo",
            input_schema={
                "type": "object",
                "properties": {"content": {"title": "Content"}},
            },
        )

        with patch(_PATCH_CONVERT_TOOL, return_value=MagicMock()) as mock_convert:
            _convert_server_tools([raw_tool], MagicMock(), "srv")

        passed_tool = mock_convert.call_args.args[1]
        assert passed_tool.inputSchema["properties"]["content"]["type"] == "string"

    def test_convert_server_tools_preserves_order(self) -> None:
        """The returned list mirrors the input order 1:1."""
        raw_tools = [_make_raw_tool("a"), _make_raw_tool("b"), _make_raw_tool("c")]
        returned = [
            SimpleNamespace(name="a"),
            SimpleNamespace(name="b"),
            SimpleNamespace(name="c"),
        ]

        with patch(_PATCH_CONVERT_TOOL, side_effect=returned):
            result = _convert_server_tools(raw_tools, MagicMock(), "srv")

        assert result == returned


class TestMCPManagerInterceptors:
    """Tests for the ``tool_interceptors`` pass-through on ``MCPManager``."""

    def test_mcp_manager_stores_and_forwards_interceptors(self) -> None:
        """Interceptors are stored and forwarded to the shared helper."""
        sentinel = object()
        raw_tool = _make_raw_tool("read_file")
        mock_client = _build_mock_client({"workspace": [raw_tool]})

        with (
            patch(_PATCH_MCP_CLIENT, return_value=mock_client),
            patch(
                _HELPER_IN_MANAGER,
                return_value=[SimpleNamespace(name="read_file", metadata=None)],
            ) as mock_helper,
        ):
            manager = MCPManager(
                {"workspace": {"transport": "stdio"}},
                tool_interceptors=[sentinel],
            )
            try:
                assert manager._tool_interceptors == [sentinel]
                manager.tools()
            finally:
                manager.close()

        mock_helper.assert_called_once()
        assert mock_helper.call_args.args[3] == [sentinel]

    def test_mcp_manager_defaults_interceptors_to_none(self) -> None:
        """Without the argument, the manager stores and forwards ``None``."""
        raw_tool = _make_raw_tool("read_file")
        mock_client = _build_mock_client({"workspace": [raw_tool]})

        with (
            patch(_PATCH_MCP_CLIENT, return_value=mock_client),
            patch(
                _HELPER_IN_MANAGER,
                return_value=[SimpleNamespace(name="read_file", metadata=None)],
            ) as mock_helper,
        ):
            manager = MCPManager({"workspace": {"transport": "stdio"}})
            try:
                assert manager._tool_interceptors is None
                manager.tools()
            finally:
                manager.close()

        assert mock_helper.call_args.args[3] is None

    def test_connect_and_discover_stamps_canonical_name_from_raw_mcp_name(self) -> None:
        """The canonical stamp is derived from the raw MCP name, not ``lc_tool.name``.

        Regression guard for the turn-vs-call canonical-identity invariant: the
        mocked ``convert_...`` returns an lc_tool whose ``.name`` deliberately
        DIFFERS from the raw MCP tool name (``foo`` -> ``renamed_foo``). The stamp
        must equal ``mcp__workspace__foo`` (the raw-name literal), never
        ``mcp__workspace__renamed_foo``. Pinning the expected value to the raw
        name (a different source than ``lc_tool.name``) makes this non-tautological.
        """
        raw_tool = _make_raw_tool("foo")
        mock_client = _build_mock_client({"workspace": [raw_tool]})

        def _convert(*_args: Any, **_kwargs: Any) -> SimpleNamespace:
            return SimpleNamespace(name="renamed_foo", metadata=None)

        with (
            patch(_PATCH_MCP_CLIENT, return_value=mock_client),
            patch(_PATCH_CONVERT_TOOL, side_effect=_convert),
        ):
            manager = MCPManager({"workspace": {"transport": "stdio"}})
            try:
                tools = manager.tools()
                # Sanity: the rename actually happened, so the assertion below
                # is meaningful (not tautological).
                assert tools[0].name == "renamed_foo"
                assert manager.canonical_name(tools[0]) == "mcp__workspace__foo"
            finally:
                manager.close()


class TestRunAgentStreamInlineLoader:
    """The ``run_agent_stream`` else-branch loader uses the helper with no interceptors."""

    @pytest.mark.asyncio
    async def test_run_agent_stream_inline_loader_passes_no_interceptors(
        self, tmp_path: Path
    ) -> None:
        """The inline (no-``tools``) path forwards ``None`` interceptors via the helper."""
        cfg = {"mcpServers": {"srv": {"command": "echo", "args": ["hi"]}}}
        cfg_file = tmp_path / ".mcp.json"
        cfg_file.write_text(json.dumps(cfg), encoding="utf-8")

        raw_tool = _make_raw_tool("foo")
        mock_client = _build_mock_client({"srv": [raw_tool]})

        mock_agent = MagicMock()

        async def _empty_events() -> Any:
            for _ in []:
                yield

        mock_agent.astream_events.return_value = _empty_events()

        with (
            patch(_PATCH_MCP_CLIENT, return_value=mock_client),
            patch(_HELPER_IN_AGENT, return_value=[MagicMock()]) as mock_helper,
            patch(_PATCH_CREATE_AGENT, return_value=mock_agent),
            patch(_PATCH_FROM_DICT, return_value=[]),
            patch(_PATCH_STORE_HISTORY, MagicMock()),
        ):
            gen = run_agent_stream(
                question="test",
                chat_model=MagicMock(),
                messages=[],
                mcp_config_path=str(cfg_file),
                session_id="s1",
            )
            async for _ in gen:
                pass

        mock_helper.assert_called_once()
        # No interceptors forwarded: neither a 4th positional nor a kwarg.
        assert "tool_interceptors" not in mock_helper.call_args.kwargs
        assert len(mock_helper.call_args.args) == 3

    @pytest.mark.asyncio
    async def test_run_agent_stream_skips_inline_loader_when_tools_provided(
        self,
    ) -> None:
        """Providing ``tools`` skips the site-3 inline loader entirely (D1 guard).

        This is the iCoder path: ``MCPManager`` supplies pre-built, interceptor-
        instrumented tools, so ``run_agent_stream`` must never construct a
        ``MultiServerMCPClient`` (the un-instrumented site-3 convert loop). A
        client patched to blow up on construction proves the branch is not taken.
        """
        boom_client = MagicMock(
            side_effect=AssertionError("site-3 inline loader must not run")
        )
        mock_agent = MagicMock()

        async def _empty_events() -> Any:
            for _ in []:
                yield

        mock_agent.astream_events.return_value = _empty_events()

        with (
            patch(_PATCH_MCP_CLIENT, boom_client),
            patch(_PATCH_CREATE_AGENT, return_value=mock_agent),
            patch(_PATCH_FROM_DICT, return_value=[]),
            patch(_PATCH_STORE_HISTORY, MagicMock()),
        ):
            gen = run_agent_stream(
                question="test",
                chat_model=MagicMock(),
                messages=[],
                mcp_config_path="/does/not/matter.json",
                session_id="s1",
                tools=[MagicMock()],
            )
            async for _ in gen:
                pass

        boom_client.assert_not_called()
