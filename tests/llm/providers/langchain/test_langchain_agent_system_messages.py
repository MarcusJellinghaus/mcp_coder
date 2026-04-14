"""Tests for system message handling in run_agent."""

import asyncio
import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcp_coder.llm.providers.langchain.agent import run_agent

_PATCH_MCP_CLIENT = "langchain_mcp_adapters.client.MultiServerMCPClient"
_PATCH_CONVERT_TOOL = "langchain_mcp_adapters.tools.convert_mcp_tool_to_langchain_tool"
_PATCH_CREATE_AGENT = "langgraph.prebuilt.create_react_agent"
_PATCH_FROM_DICT = "langchain_core.messages.messages_from_dict"


def _make_ai_message(
    content: str, tool_calls: list[dict[str, object]] | None = None
) -> object:
    """Create an AIMessage instance (uses conftest mock class)."""
    from langchain_core.messages import AIMessage

    msg = AIMessage(content=content, tool_calls=tool_calls or [])
    msg.model_dump = lambda: {
        "type": "ai",
        "content": content,
        "tool_calls": tool_calls or [],
    }
    return msg


def _make_human_message(content: str) -> object:
    """Create a HumanMessage instance (uses conftest mock class)."""
    from langchain_core.messages import HumanMessage

    msg = HumanMessage(content=content)
    msg.model_dump = lambda: {"type": "human", "content": content}
    return msg


def _write_mcp_config(tmp_path: Path) -> str:
    """Write a minimal .mcp.json and return its path."""
    cfg = {"mcpServers": {"test": {"command": "echo", "args": ["hello"]}}}
    cfg_file = tmp_path / ".mcp.json"
    cfg_file.write_text(json.dumps(cfg), encoding="utf-8")
    return str(cfg_file)


def _make_mock_client() -> MagicMock:
    """Build a mock MultiServerMCPClient for plain instantiation."""
    mock_session = AsyncMock()
    mock_list_result = MagicMock()
    mock_list_result.tools = []
    mock_session.list_tools.return_value = mock_list_result

    mock_client = MagicMock()
    mock_client.connections = {"test": {"transport": "stdio", "command": "echo"}}
    mock_client.session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_client.session.return_value.__aexit__ = AsyncMock(return_value=False)
    return mock_client


class TestRunAgentSystemMessages:
    """Tests for system message handling in run_agent."""

    @pytest.mark.asyncio
    async def test_prepends_system_messages(self, tmp_path: Path) -> None:
        """System messages appear first in input_messages passed to agent."""
        from langchain_core.messages import SystemMessage

        cfg_path = _write_mcp_config(tmp_path)

        human_msg = _make_human_message("Hello")
        ai_msg = _make_ai_message("Hi!")

        mock_client = _make_mock_client()

        mock_agent = AsyncMock()
        mock_agent.ainvoke.return_value = {"messages": [human_msg, ai_msg]}

        sys_msgs = [
            SystemMessage(content="system instructions"),
            SystemMessage(content="project context"),
        ]

        with (
            patch(_PATCH_MCP_CLIENT, return_value=mock_client),
            patch(_PATCH_CONVERT_TOOL, return_value=MagicMock()),
            patch(_PATCH_CREATE_AGENT, return_value=mock_agent),
            patch(_PATCH_FROM_DICT, return_value=[]),
        ):
            await run_agent(
                question="Hello",
                chat_model=MagicMock(),
                messages=[],
                mcp_config_path=cfg_path,
                system_messages=sys_msgs,
            )

        # Verify system messages are first in the input
        call_args = mock_agent.ainvoke.call_args[0][0]["messages"]
        assert len(call_args) == 3  # 2 system + 1 human
        assert isinstance(call_args[0], SystemMessage)
        assert isinstance(call_args[1], SystemMessage)
        assert call_args[0].content == "system instructions"
        assert call_args[1].content == "project context"

    @pytest.mark.asyncio
    async def test_no_system_messages_when_none(self, tmp_path: Path) -> None:
        """No SystemMessages when system_messages is None."""
        from langchain_core.messages import SystemMessage

        cfg_path = _write_mcp_config(tmp_path)

        human_msg = _make_human_message("Hello")
        ai_msg = _make_ai_message("Hi!")

        mock_client = _make_mock_client()

        mock_agent = AsyncMock()
        mock_agent.ainvoke.return_value = {"messages": [human_msg, ai_msg]}

        with (
            patch(_PATCH_MCP_CLIENT, return_value=mock_client),
            patch(_PATCH_CONVERT_TOOL, return_value=MagicMock()),
            patch(_PATCH_CREATE_AGENT, return_value=mock_agent),
            patch(_PATCH_FROM_DICT, return_value=[]),
        ):
            await run_agent(
                question="Hello",
                chat_model=MagicMock(),
                messages=[],
                mcp_config_path=cfg_path,
            )

        call_args = mock_agent.ainvoke.call_args[0][0]["messages"]
        assert len(call_args) == 1  # just the human message
        assert not isinstance(call_args[0], SystemMessage)

    @pytest.mark.asyncio
    async def test_timeout_raises_on_slow_agent(self, tmp_path: Path) -> None:
        """asyncio.TimeoutError is raised when agent exceeds timeout."""
        cfg_path = _write_mcp_config(tmp_path)

        async def _slow_invoke(*args: Any, **kwargs: Any) -> dict[str, Any]:
            await asyncio.sleep(10)
            return {"messages": []}  # pragma: no cover

        mock_client = _make_mock_client()

        mock_agent = MagicMock()
        mock_agent.ainvoke = _slow_invoke

        with (
            patch(_PATCH_MCP_CLIENT, return_value=mock_client),
            patch(_PATCH_CONVERT_TOOL, return_value=MagicMock()),
            patch(_PATCH_CREATE_AGENT, return_value=mock_agent),
            patch(_PATCH_FROM_DICT, return_value=[]),
            pytest.raises(asyncio.TimeoutError),
        ):
            await run_agent(
                question="test",
                chat_model=MagicMock(),
                messages=[],
                mcp_config_path=cfg_path,
                timeout=1,
            )
