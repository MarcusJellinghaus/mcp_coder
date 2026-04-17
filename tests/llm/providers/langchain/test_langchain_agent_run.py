"""Tests for run_agent execution and MCP launch error wrapping."""

import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcp_coder.llm.providers.langchain.agent import run_agent

# ---------------------------------------------------------------------------
# Helpers for run_agent tests
# ---------------------------------------------------------------------------

_PATCH_MCP_CLIENT = "langchain_mcp_adapters.client.MultiServerMCPClient"
_PATCH_CONVERT_TOOL = "langchain_mcp_adapters.tools.convert_mcp_tool_to_langchain_tool"
_PATCH_CREATE_AGENT = "langgraph.prebuilt.create_react_agent"
_PATCH_FROM_DICT = "langchain_core.messages.messages_from_dict"


def _make_ai_message(
    content: str, tool_calls: list[dict[str, object]] | None = None
) -> object:
    """Create an AIMessage instance (uses conftest mock class).

    model_dump is assigned via lambda because in the test environment
    real LangChain may not be installed — conftest provides lightweight
    stub classes that don't have Pydantic's model_dump.
    """
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
    """Build a mock MultiServerMCPClient for plain instantiation.

    Since ``langchain-mcp-adapters>=0.1.0``, ``MultiServerMCPClient`` is
    stateless — plain ``client = MultiServerMCPClient(cfg)`` with no async
    context manager.  ``client.session()`` still uses ``async with``.
    """
    mock_session = AsyncMock()
    mock_list_result = MagicMock()
    mock_list_result.tools = []  # no raw MCP tools by default
    mock_session.list_tools.return_value = mock_list_result

    mock_client = MagicMock()
    mock_client.connections = {"test": {"transport": "stdio", "command": "echo"}}
    mock_client.session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_client.session.return_value.__aexit__ = AsyncMock(return_value=False)
    return mock_client


class TestRunAgent:
    """Tests for run_agent() async function."""

    @pytest.mark.asyncio
    async def test_returns_final_text(self, tmp_path: Path) -> None:
        """Agent returns the final AIMessage content as text."""
        cfg_path = _write_mcp_config(tmp_path)

        human_msg = _make_human_message("What is 2+2?")
        ai_msg = _make_ai_message("The answer is 4.")

        mock_client = _make_mock_client()

        mock_agent = AsyncMock()
        mock_agent.ainvoke.return_value = {"messages": [human_msg, ai_msg]}

        with (
            patch(_PATCH_MCP_CLIENT, return_value=mock_client),
            patch(_PATCH_CONVERT_TOOL, return_value=MagicMock()),
            patch(_PATCH_CREATE_AGENT, return_value=mock_agent),
            patch(_PATCH_FROM_DICT, return_value=[]),
        ):
            text, _history, _stats = await run_agent(
                question="What is 2+2?",
                chat_model=MagicMock(),
                messages=[],
                mcp_config_path=cfg_path,
            )

        assert text == "The answer is 4."

    @pytest.mark.asyncio
    async def test_returns_message_history(self, tmp_path: Path) -> None:
        """Full message history is serialized and returned."""
        cfg_path = _write_mcp_config(tmp_path)

        human_msg = _make_human_message("Hello")
        ai_msg = _make_ai_message("Hi there!")

        mock_client = _make_mock_client()

        mock_agent = AsyncMock()
        mock_agent.ainvoke.return_value = {"messages": [human_msg, ai_msg]}

        with (
            patch(_PATCH_MCP_CLIENT, return_value=mock_client),
            patch(_PATCH_CONVERT_TOOL, return_value=MagicMock()),
            patch(_PATCH_CREATE_AGENT, return_value=mock_agent),
            patch(_PATCH_FROM_DICT, return_value=[]),
        ):
            _text, history, _stats = await run_agent(
                question="Hello",
                chat_model=MagicMock(),
                messages=[],
                mcp_config_path=cfg_path,
            )

        assert len(history) == 2
        assert history[0]["type"] == "human"
        assert history[1]["type"] == "ai"

    @pytest.mark.asyncio
    async def test_returns_stats_with_tool_counts(self, tmp_path: Path) -> None:
        """Stats dict contains agent_steps and total_tool_calls."""
        cfg_path = _write_mcp_config(tmp_path)

        human_msg = _make_human_message("Read file")
        ai_with_tool = _make_ai_message(
            "",
            tool_calls=[
                {"name": "read_file", "args": {"path": "src/main.py"}, "id": "1"},
            ],
        )
        tool_result = _make_tool_message(
            "file contents here", name="read_file", tool_call_id="1"
        )
        ai_final = _make_ai_message("Here is the file content.")

        mock_client = _make_mock_client()

        mock_agent = AsyncMock()
        mock_agent.ainvoke.return_value = {
            "messages": [human_msg, ai_with_tool, tool_result, ai_final]
        }

        with (
            patch(_PATCH_MCP_CLIENT, return_value=mock_client),
            patch(_PATCH_CONVERT_TOOL, return_value=MagicMock()),
            patch(_PATCH_CREATE_AGENT, return_value=mock_agent),
            patch(_PATCH_FROM_DICT, return_value=[]),
        ):
            _text, _history, stats = await run_agent(
                question="Read file",
                chat_model=MagicMock(),
                messages=[],
                mcp_config_path=cfg_path,
            )

        assert stats["agent_steps"] == 1
        assert stats["total_tool_calls"] == 1

    @pytest.mark.asyncio
    async def test_hard_fails_on_mcp_server_error(self, tmp_path: Path) -> None:
        """If session.list_tools() fails, exception propagates."""
        cfg_path = _write_mcp_config(tmp_path)

        mock_session = AsyncMock()
        mock_session.list_tools.side_effect = ConnectionError("MCP server failed")

        mock_client = MagicMock()
        mock_client.connections = {"test": {"transport": "stdio", "command": "echo"}}
        mock_client.session.return_value.__aenter__ = AsyncMock(
            return_value=mock_session
        )
        mock_client.session.return_value.__aexit__ = AsyncMock(return_value=False)

        with (
            patch(_PATCH_MCP_CLIENT, return_value=mock_client),
            patch(_PATCH_CONVERT_TOOL, return_value=MagicMock()),
            patch(_PATCH_FROM_DICT, return_value=[]),
            pytest.raises(ConnectionError, match="MCP server failed"),
        ):
            await run_agent(
                question="test",
                chat_model=MagicMock(),
                messages=[],
                mcp_config_path=cfg_path,
            )

    @pytest.mark.asyncio
    async def test_handles_agent_response_gracefully(self, tmp_path: Path) -> None:
        """Agent returns partial output without crashing."""
        cfg_path = _write_mcp_config(tmp_path)

        human_msg = _make_human_message("Do something complex")
        partial_ai = _make_ai_message("Partial response so far...")

        mock_client = _make_mock_client()

        mock_agent = AsyncMock()
        mock_agent.ainvoke.return_value = {"messages": [human_msg, partial_ai]}

        with (
            patch(_PATCH_MCP_CLIENT, return_value=mock_client),
            patch(_PATCH_CONVERT_TOOL, return_value=MagicMock()),
            patch(_PATCH_CREATE_AGENT, return_value=mock_agent),
            patch(_PATCH_FROM_DICT, return_value=[]),
        ):
            text, history, _stats = await run_agent(
                question="Do something complex",
                chat_model=MagicMock(),
                messages=[],
                mcp_config_path=cfg_path,
            )

        assert text == "Partial response so far..."
        assert len(history) == 2

    @pytest.mark.asyncio
    async def test_prepends_session_history(self, tmp_path: Path) -> None:
        """Previous message history is prepended to agent input."""
        cfg_path = _write_mcp_config(tmp_path)

        prior_human = _make_human_message("Earlier question")
        prior_ai = _make_ai_message("Earlier answer")
        new_ai = _make_ai_message("New answer")

        mock_client = _make_mock_client()

        mock_agent = AsyncMock()
        mock_agent.ainvoke.return_value = {
            "messages": [
                prior_human,
                prior_ai,
                _make_human_message("New question"),
                new_ai,
            ]
        }

        mock_messages_from_dict = MagicMock(return_value=[prior_human, prior_ai])

        with (
            patch(_PATCH_MCP_CLIENT, return_value=mock_client),
            patch(_PATCH_CONVERT_TOOL, return_value=MagicMock()),
            patch(_PATCH_CREATE_AGENT, return_value=mock_agent),
            patch(_PATCH_FROM_DICT, mock_messages_from_dict),
        ):
            _text, _history, _stats = await run_agent(
                question="New question",
                chat_model=MagicMock(),
                messages=[{"type": "human", "content": "Earlier question"}],
                mcp_config_path=cfg_path,
            )

        # Verify messages_from_dict was called with the prior messages
        mock_messages_from_dict.assert_called_once_with(
            [{"type": "human", "content": "Earlier question"}]
        )

        # Verify agent received prior history + new question
        call_args = mock_agent.ainvoke.call_args
        input_msgs = call_args[0][0]["messages"]
        assert len(input_msgs) == 3  # 2 prior + 1 new

    @pytest.mark.asyncio
    async def test_tool_trace_in_stats(self, tmp_path: Path) -> None:
        """Stats contain tool_trace with name, args, result for each tool call."""
        cfg_path = _write_mcp_config(tmp_path)

        human_msg = _make_human_message("Read two files")
        ai_with_tools = _make_ai_message(
            "",
            tool_calls=[
                {"name": "read_file", "args": {"path": "a.py"}, "id": "1"},
                {"name": "read_file", "args": {"path": "b.py"}, "id": "2"},
            ],
        )
        tool_result_1 = _make_tool_message(
            "content of a.py", name="read_file", tool_call_id="1"
        )
        tool_result_2 = _make_tool_message(
            "content of b.py", name="read_file", tool_call_id="2"
        )
        ai_final = _make_ai_message("Done reading files.")

        mock_client = _make_mock_client()

        mock_agent = AsyncMock()
        mock_agent.ainvoke.return_value = {
            "messages": [
                human_msg,
                ai_with_tools,
                tool_result_1,
                tool_result_2,
                ai_final,
            ]
        }

        with (
            patch(_PATCH_MCP_CLIENT, return_value=mock_client),
            patch(_PATCH_CONVERT_TOOL, return_value=MagicMock()),
            patch(_PATCH_CREATE_AGENT, return_value=mock_agent),
            patch(_PATCH_FROM_DICT, return_value=[]),
        ):
            _text, _history, stats = await run_agent(
                question="Read two files",
                chat_model=MagicMock(),
                messages=[],
                mcp_config_path=cfg_path,
            )

        trace = stats["tool_trace"]
        assert isinstance(trace, list)
        assert len(trace) == 2
        assert trace[0]["name"] == "read_file"
        assert trace[0]["args"] == {"path": "a.py"}
        assert trace[0]["result"] == "content of a.py"
        assert trace[1]["name"] == "read_file"
        assert trace[1]["args"] == {"path": "b.py"}
        assert trace[1]["result"] == "content of b.py"


# ---------------------------------------------------------------------------
# Tests for LLMMCPLaunchError wrap (issue #830 — Step 2)
# ---------------------------------------------------------------------------


def _make_launch_failing_client(exc: BaseException) -> MagicMock:
    """Build a mock MultiServerMCPClient whose session() raises on enter."""
    mock_client = MagicMock()
    mock_client.connections = {"broken": {"transport": "stdio", "command": "/no/such"}}
    mock_client.session.return_value.__aenter__ = AsyncMock(side_effect=exc)
    mock_client.session.return_value.__aexit__ = AsyncMock(return_value=False)
    return mock_client


class TestRunAgentLaunchErrorWrap:
    """Wrap FileNotFoundError / PermissionError as LLMMCPLaunchError."""

    @pytest.mark.parametrize(
        ("exc_class", "exc_message", "command"),
        [
            (FileNotFoundError, "no such file", "/no/such/binary"),
            (PermissionError, "denied", "/denied/binary"),
        ],
        ids=["FileNotFoundError", "PermissionError"],
    )
    @pytest.mark.asyncio
    async def test_run_agent_wraps_launch_errors(
        self,
        tmp_path: Path,
        exc_class: type[BaseException],
        exc_message: str,
        command: str,
    ) -> None:
        """FileNotFoundError / PermissionError from session.__aenter__ become LLMMCPLaunchError."""
        from mcp_coder.llm.providers.langchain._exceptions import LLMMCPLaunchError

        cfg = {"mcpServers": {"broken": {"command": command}}}
        cfg_file = tmp_path / ".mcp.json"
        cfg_file.write_text(json.dumps(cfg), encoding="utf-8")

        original = exc_class(exc_message)
        mock_client = _make_launch_failing_client(original)

        with (
            patch(_PATCH_MCP_CLIENT, return_value=mock_client),
            patch(_PATCH_CONVERT_TOOL, return_value=MagicMock()),
            patch(_PATCH_FROM_DICT, return_value=[]),
            pytest.raises(LLMMCPLaunchError) as exc_info,
        ):
            await run_agent(
                question="test",
                chat_model=MagicMock(),
                messages=[],
                mcp_config_path=str(cfg_file),
            )

        msg = str(exc_info.value)
        assert "broken" in msg
        assert command in msg
        assert exc_class.__name__ in msg
        assert exc_info.value.__cause__ is original

    @pytest.mark.asyncio
    async def test_run_agent_stream_wraps_filenotfound(self, tmp_path: Path) -> None:
        """run_agent_stream wraps FileNotFoundError on first iteration."""
        from mcp_coder.llm.providers.langchain._exceptions import LLMMCPLaunchError
        from mcp_coder.llm.providers.langchain.agent import run_agent_stream

        cfg = {"mcpServers": {"broken": {"command": "/no/such/binary"}}}
        cfg_file = tmp_path / ".mcp.json"
        cfg_file.write_text(json.dumps(cfg), encoding="utf-8")

        original = FileNotFoundError("no such file")
        mock_client = _make_launch_failing_client(original)

        with (
            patch(_PATCH_MCP_CLIENT, return_value=mock_client),
            patch(_PATCH_CONVERT_TOOL, return_value=MagicMock()),
            patch(_PATCH_CREATE_AGENT, return_value=AsyncMock()),
            patch(_PATCH_FROM_DICT, return_value=[]),
        ):
            gen = run_agent_stream(
                question="test",
                chat_model=MagicMock(),
                messages=[],
                mcp_config_path=str(cfg_file),
                session_id="s1",
            )
            with pytest.raises(LLMMCPLaunchError) as exc_info:
                async for _ in gen:
                    pass

        msg = str(exc_info.value)
        assert "broken" in msg
        assert "/no/such/binary" in msg
        assert "FileNotFoundError" in msg
        assert exc_info.value.__cause__ is original

    @pytest.mark.asyncio
    async def test_run_agent_stream_skips_wrap_when_tools_provided(
        self, tmp_path: Path
    ) -> None:
        """When ``tools`` is passed, MultiServerMCPClient must not be constructed."""
        from mcp_coder.llm.providers.langchain.agent import run_agent_stream

        cfg_file = tmp_path / ".mcp.json"
        cfg_file.write_text(json.dumps({"mcpServers": {}}), encoding="utf-8")

        mock_agent = MagicMock()

        async def _empty_events() -> Any:
            for _ in []:
                yield

        mock_agent.astream_events.return_value = _empty_events()

        pre_built_tool = MagicMock()

        with (
            patch(_PATCH_MCP_CLIENT) as mock_client_cls,
            patch(_PATCH_CREATE_AGENT, return_value=mock_agent),
            patch(_PATCH_FROM_DICT, return_value=[]),
            patch(
                "mcp_coder.llm.storage.session_storage.store_langchain_history",
                MagicMock(),
            ),
        ):
            gen = run_agent_stream(
                question="test",
                chat_model=MagicMock(),
                messages=[],
                mcp_config_path=str(cfg_file),
                session_id="s1",
                tools=[pre_built_tool],
            )
            async for _ in gen:
                pass

        mock_client_cls.assert_not_called()
