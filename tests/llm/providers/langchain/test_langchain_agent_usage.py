"""Tests for token usage accumulation in run_agent() stats.

``run_agent`` drains ``run_agent_stream``, so usage no longer comes from the
final message list — it comes from the stream's ``on_chat_model_end``
accumulator. These tests therefore feed usage through hand-built
``on_chat_model_end`` events.

**They prove the accumulator arithmetic only.** Because the ``usage_metadata``
is injected by hand they pass by construction and cannot show whether a real
backend streams usage at all; that is gated by
``test_langchain_integration.py::TestAgentModeIntegration::test_agent_simple_prompt``.
"""

import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcp_coder.llm.providers.langchain.agent import run_agent
from tests.llm.providers.langchain.conftest import async_events, graph_events

_PATCH_MCP_CLIENT = "langchain_mcp_adapters.client.MultiServerMCPClient"
_PATCH_CONVERT_TOOL = "langchain_mcp_adapters.tools.convert_mcp_tool_to_langchain_tool"
_PATCH_CREATE_AGENT = "langgraph.prebuilt.create_react_agent"
_PATCH_FROM_DICT = "langchain_core.messages.messages_from_dict"
_PATCH_STORE = "mcp_coder.llm.storage.session_storage.store_langchain_history"


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


def _chat_model_end(ai_msg: object) -> dict[str, object]:
    """Build the ``on_chat_model_end`` event that carries *ai_msg*'s usage.

    Under ``astream_events`` the aggregated chunk arrives here; this is the only
    place ``run_agent_stream`` reads usage from.
    """
    return {
        "event": "on_chat_model_end",
        "data": {"output": ai_msg},
        "run_id": "model-run",
        "name": "model",
    }


async def _run_with(
    tmp_path: Path,
    final_messages: list[object],
    inner: list[dict[str, object]],
) -> dict[str, Any]:
    """Drive ``run_agent`` over a stubbed graph and return its stats."""
    cfg_path = _write_mcp_config(tmp_path)

    # MagicMock (not AsyncMock): run_agent_stream does
    # `async for event in agent.astream_events(...)`, and an AsyncMock child
    # call returns a coroutine, which `async for` rejects.
    mock_agent = MagicMock()
    mock_agent.astream_events.return_value = async_events(
        graph_events(list(final_messages), inner=inner)
    )

    with (
        patch(_PATCH_MCP_CLIENT, return_value=_make_mock_client()),
        patch(_PATCH_CONVERT_TOOL, return_value=MagicMock()),
        patch(_PATCH_CREATE_AGENT, return_value=mock_agent),
        patch(_PATCH_FROM_DICT, return_value=[]),
        patch(_PATCH_STORE, MagicMock()),
    ):
        _text, _history, stats = await run_agent(
            question="Hi",
            chat_model=MagicMock(),
            messages=[],
            mcp_config_path=cfg_path,
            session_id="s1",
        )
    return stats


class TestRunAgentUsage:
    """Tests for token usage accumulation in run_agent() stats."""

    @pytest.mark.asyncio
    async def test_run_agent_stats_include_usage(self, tmp_path: Path) -> None:
        """Stats contain summed usage from AIMessages with usage_metadata."""
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

        stats = await _run_with(
            tmp_path,
            [human_msg, ai_msg],
            inner=[_chat_model_end(ai_msg)],
        )

        assert stats["usage"]["input_tokens"] == 500
        assert stats["usage"]["output_tokens"] == 200
        assert stats["usage"]["cache_read_input_tokens"] == 100

    @pytest.mark.asyncio
    async def test_run_agent_stats_usage_empty_when_no_metadata(
        self, tmp_path: Path
    ) -> None:
        """Stats contain empty usage dict when AIMessages lack usage_metadata."""
        human_msg = _make_human_message("Hi")
        ai_msg = _make_ai_message("Answer")  # no usage_metadata

        stats = await _run_with(
            tmp_path,
            [human_msg, ai_msg],
            inner=[_chat_model_end(ai_msg)],
        )

        assert stats["usage"] == {}

    @pytest.mark.asyncio
    async def test_run_agent_stats_usage_sums_multiple_steps(
        self, tmp_path: Path
    ) -> None:
        """Stats usage is the per-field sum across multiple AIMessages."""
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

        stats = await _run_with(
            tmp_path,
            [human_msg, ai_msg_1, tool_result, ai_msg_2],
            inner=[_chat_model_end(ai_msg_1), _chat_model_end(ai_msg_2)],
        )

        assert stats["usage"]["input_tokens"] == 1300
        assert stats["usage"]["output_tokens"] == 500
        assert stats["usage"]["cache_read_input_tokens"] == 300
