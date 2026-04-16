"""Tests for token usage accumulation in run_agent() stats."""

import json
from pathlib import Path
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


def _make_tool_message(
    content: str, name: str = "tool", tool_call_id: str = "test-tool-call-id"
) -> object:
    """Create a ToolMessage instance (uses conftest mock class)."""
    from langchain_core.messages import ToolMessage

    msg = ToolMessage(content=content, name=name, tool_call_id=tool_call_id)
    msg.model_dump = lambda: {
        "type": "tool",
        "name": name,
        "content": content,
    }
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


def _make_ai_message_with_usage(
    content: str,
    usage_metadata: dict[str, object] | None = None,
    tool_calls: list[dict[str, object]] | None = None,
) -> object:
    """Create an AIMessage with optional usage_metadata."""
    from langchain_core.messages import AIMessage

    kwargs: dict[str, object] = {"content": content, "tool_calls": tool_calls or []}
    if usage_metadata is not None:
        kwargs["usage_metadata"] = usage_metadata
    msg = AIMessage(**kwargs)
    msg.model_dump = lambda: {
        "type": "ai",
        "content": content,
        "tool_calls": tool_calls or [],
    }
    return msg


class TestRunAgentUsage:
    """Tests for token usage accumulation in run_agent() stats."""

    @pytest.mark.asyncio
    async def test_run_agent_stats_include_usage(self, tmp_path: Path) -> None:
        """Stats contain summed usage from AIMessages with usage_metadata."""
        cfg_path = _write_mcp_config(tmp_path)

        human_msg = _make_human_message("Hi")
        ai_msg = _make_ai_message_with_usage(
            "Answer",
            usage_metadata={
                "input_tokens": 500,
                "output_tokens": 200,
                "total_tokens": 700,
                "input_token_details": {"cache_read": 100},
            },
        )

        mock_client = _make_mock_client()

        mock_agent = AsyncMock()
        mock_agent.ainvoke.return_value = {"messages": [human_msg, ai_msg]}

        with (
            patch(_PATCH_MCP_CLIENT, return_value=mock_client),
            patch(_PATCH_CONVERT_TOOL, return_value=MagicMock()),
            patch(_PATCH_CREATE_AGENT, return_value=mock_agent),
            patch(_PATCH_FROM_DICT, return_value=[]),
        ):
            _text, _history, stats = await run_agent(
                question="Hi",
                chat_model=MagicMock(),
                messages=[],
                mcp_config_path=cfg_path,
            )

        assert stats["usage"]["input_tokens"] == 500
        assert stats["usage"]["output_tokens"] == 200
        assert stats["usage"]["cache_read_input_tokens"] == 100

    @pytest.mark.asyncio
    async def test_run_agent_stats_usage_empty_when_no_metadata(
        self, tmp_path: Path
    ) -> None:
        """Stats contain empty usage dict when AIMessages lack usage_metadata."""
        cfg_path = _write_mcp_config(tmp_path)

        human_msg = _make_human_message("Hi")
        ai_msg = _make_ai_message("Answer")  # no usage_metadata

        mock_client = _make_mock_client()

        mock_agent = AsyncMock()
        mock_agent.ainvoke.return_value = {"messages": [human_msg, ai_msg]}

        with (
            patch(_PATCH_MCP_CLIENT, return_value=mock_client),
            patch(_PATCH_CONVERT_TOOL, return_value=MagicMock()),
            patch(_PATCH_CREATE_AGENT, return_value=mock_agent),
            patch(_PATCH_FROM_DICT, return_value=[]),
        ):
            _text, _history, stats = await run_agent(
                question="Hi",
                chat_model=MagicMock(),
                messages=[],
                mcp_config_path=cfg_path,
            )

        assert stats["usage"] == {}

    @pytest.mark.asyncio
    async def test_run_agent_stats_usage_sums_multiple_steps(
        self, tmp_path: Path
    ) -> None:
        """Stats usage is the per-field sum across multiple AIMessages."""
        cfg_path = _write_mcp_config(tmp_path)

        human_msg = _make_human_message("Hi")
        ai_msg_1 = _make_ai_message_with_usage(
            "",
            usage_metadata={
                "input_tokens": 500,
                "output_tokens": 200,
                "total_tokens": 700,
                "input_token_details": {"cache_read": 100},
            },
            tool_calls=[{"name": "tool", "args": {}, "id": "1"}],
        )
        tool_result = _make_tool_message("ok", name="tool", tool_call_id="1")
        ai_msg_2 = _make_ai_message_with_usage(
            "Answer",
            usage_metadata={
                "input_tokens": 800,
                "output_tokens": 300,
                "total_tokens": 1100,
                "input_token_details": {"cache_read": 200},
            },
        )

        mock_client = _make_mock_client()

        mock_agent = AsyncMock()
        mock_agent.ainvoke.return_value = {
            "messages": [human_msg, ai_msg_1, tool_result, ai_msg_2]
        }

        with (
            patch(_PATCH_MCP_CLIENT, return_value=mock_client),
            patch(_PATCH_CONVERT_TOOL, return_value=MagicMock()),
            patch(_PATCH_CREATE_AGENT, return_value=mock_agent),
            patch(_PATCH_FROM_DICT, return_value=[]),
        ):
            _text, _history, stats = await run_agent(
                question="Hi",
                chat_model=MagicMock(),
                messages=[],
                mcp_config_path=cfg_path,
            )

        assert stats["usage"]["input_tokens"] == 1300
        assert stats["usage"]["output_tokens"] == 500
        assert stats["usage"]["cache_read_input_tokens"] == 300
