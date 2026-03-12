"""Tests for agent utility functions and run_agent execution."""

import json
import logging
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcp_coder.llm.providers.langchain.agent import (
    AGENT_MAX_STEPS,
    _load_mcp_server_config,
    _resolve_env_vars,
    run_agent,
)


class TestResolveEnvVars:
    """Tests for _resolve_env_vars."""

    def test_replaces_single_var(self) -> None:
        result = _resolve_env_vars("${HOME}/bin", {"HOME": "/usr/local"})
        assert result == "/usr/local/bin"

    def test_replaces_multiple_vars(self) -> None:
        result = _resolve_env_vars(
            "${USER}@${HOST}", {"USER": "alice", "HOST": "server1"}
        )
        assert result == "alice@server1"

    def test_preserves_unknown_vars(self) -> None:
        result = _resolve_env_vars("${KNOWN}/${UNKNOWN}", {"KNOWN": "ok"})
        assert result == "ok/${UNKNOWN}"

    def test_empty_string_unchanged(self) -> None:
        assert _resolve_env_vars("", {"A": "B"}) == ""

    def test_no_placeholders_unchanged(self) -> None:
        assert _resolve_env_vars("plain text", {"A": "B"}) == "plain text"


class TestLoadMcpServerConfig:
    """Tests for _load_mcp_server_config."""

    @staticmethod
    def _write_config(tmp_path: Path, config: dict[str, object]) -> str:
        cfg_file = tmp_path / ".mcp.json"
        cfg_file.write_text(json.dumps(config), encoding="utf-8")
        return str(cfg_file)

    def test_loads_and_resolves_config(self, tmp_path: Path) -> None:
        path = self._write_config(
            tmp_path,
            {
                "mcpServers": {
                    "myserver": {
                        "command": "${BIN}/server",
                        "args": ["--dir", "${PROJECT}"],
                        "env": {"PYTHONPATH": "${LIB}"},
                    }
                }
            },
        )
        result = _load_mcp_server_config(
            path, env_vars={"BIN": "/opt/bin", "PROJECT": "/code", "LIB": "/lib"}
        )
        assert result == {
            "myserver": {
                "command": "/opt/bin/server",
                "args": ["--dir", "/code"],
                "env": {"PYTHONPATH": "/lib"},
                "transport": "stdio",
            }
        }

    def test_env_vars_override_os_environ(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("MY_VAR", "from_os")
        path = self._write_config(
            tmp_path,
            {"mcpServers": {"s": {"command": "${MY_VAR}"}}},
        )
        # env_vars should win over os.environ
        result = _load_mcp_server_config(path, env_vars={"MY_VAR": "override"})
        assert result["s"]["command"] == "override"

    def test_raises_on_missing_file(self) -> None:
        with pytest.raises(FileNotFoundError):
            _load_mcp_server_config("/nonexistent/path/.mcp.json")

    def test_sets_stdio_transport(self, tmp_path: Path) -> None:
        path = self._write_config(
            tmp_path,
            {"mcpServers": {"s": {"command": "cmd", "transport": "sse"}}},
        )
        result = _load_mcp_server_config(path)
        # Always overridden to stdio
        assert result["s"]["transport"] == "stdio"

    def test_warns_on_unknown_fields(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        path = self._write_config(
            tmp_path,
            {
                "mcpServers": {
                    "s": {
                        "command": "cmd",
                        "unknownField": "value123",
                    }
                }
            },
        )
        with caplog.at_level(logging.WARNING):
            result = _load_mcp_server_config(path)
        assert "unknownField" in caplog.text
        # Unknown field should not appear in output
        assert "unknownField" not in result["s"]


class TestAgentConstants:
    """Verify module-level constants."""

    def test_max_steps_value(self) -> None:
        assert AGENT_MAX_STEPS == 50


# ---------------------------------------------------------------------------
# Helpers for run_agent tests
# ---------------------------------------------------------------------------

_PATCH_MCP_CLIENT = "langchain_mcp_adapters.client.MultiServerMCPClient"
_PATCH_CREATE_AGENT = "langgraph.prebuilt.create_react_agent"
_PATCH_FROM_DICT = "langchain_core.messages.messages_from_dict"


def _make_ai_message(
    content: str, tool_calls: list[dict[str, object]] | None = None
) -> object:
    """Create an AIMessage instance (uses conftest mock class)."""
    from langchain_core.messages import AIMessage

    msg = AIMessage(content=content, tool_calls=tool_calls or [])
    msg.model_dump = lambda: {  # type: ignore[attr-defined]
        "type": "ai",
        "content": content,
        "tool_calls": tool_calls or [],
    }
    return msg


def _make_human_message(content: str) -> object:
    """Create a HumanMessage instance (uses conftest mock class)."""
    from langchain_core.messages import HumanMessage

    msg = HumanMessage(content=content)
    msg.model_dump = lambda: {"type": "human", "content": content}  # type: ignore[attr-defined]
    return msg


def _make_tool_message(content: str, name: str = "tool") -> object:
    """Create a ToolMessage instance (uses conftest mock class)."""
    from langchain_core.messages import ToolMessage

    msg = ToolMessage(content=content, name=name)
    msg.model_dump = lambda: {  # type: ignore[attr-defined]
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


class TestRunAgent:
    """Tests for run_agent() async function."""

    @pytest.mark.asyncio
    async def test_returns_final_text(self, tmp_path: Path) -> None:
        """Agent returns the final AIMessage content as text."""
        cfg_path = _write_mcp_config(tmp_path)

        human_msg = _make_human_message("What is 2+2?")
        ai_msg = _make_ai_message("The answer is 4.")

        mock_client = AsyncMock()
        mock_client.get_tools.return_value = [MagicMock()]

        mock_agent = AsyncMock()
        mock_agent.ainvoke.return_value = {"messages": [human_msg, ai_msg]}

        with (
            patch(_PATCH_MCP_CLIENT, return_value=mock_client),
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

        mock_client = AsyncMock()
        mock_client.get_tools.return_value = []

        mock_agent = AsyncMock()
        mock_agent.ainvoke.return_value = {"messages": [human_msg, ai_msg]}

        with (
            patch(_PATCH_MCP_CLIENT, return_value=mock_client),
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
        tool_result = _make_tool_message("file contents here", name="read_file")
        ai_final = _make_ai_message("Here is the file content.")

        mock_client = AsyncMock()
        mock_client.get_tools.return_value = [MagicMock()]

        mock_agent = AsyncMock()
        mock_agent.ainvoke.return_value = {
            "messages": [human_msg, ai_with_tool, tool_result, ai_final]
        }

        with (
            patch(_PATCH_MCP_CLIENT, return_value=mock_client),
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
        """If MultiServerMCPClient fails to start, exception propagates."""
        cfg_path = _write_mcp_config(tmp_path)

        mock_client = AsyncMock()
        mock_client.__aenter__.side_effect = ConnectionError("MCP server failed")

        with (
            patch(_PATCH_MCP_CLIENT, return_value=mock_client),
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
    async def test_max_iterations_returns_partial_output(self, tmp_path: Path) -> None:
        """When recursion limit reached, returns partial output (no crash)."""
        cfg_path = _write_mcp_config(tmp_path)

        human_msg = _make_human_message("Do something complex")
        partial_ai = _make_ai_message("Partial response so far...")

        mock_client = AsyncMock()
        mock_client.get_tools.return_value = []

        mock_agent = AsyncMock()
        mock_agent.ainvoke.return_value = {"messages": [human_msg, partial_ai]}

        with (
            patch(_PATCH_MCP_CLIENT, return_value=mock_client),
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

        mock_client = AsyncMock()
        mock_client.get_tools.return_value = []

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
        tool_result_1 = _make_tool_message("content of a.py", name="read_file")
        tool_result_2 = _make_tool_message("content of b.py", name="read_file")
        ai_final = _make_ai_message("Done reading files.")

        mock_client = AsyncMock()
        mock_client.get_tools.return_value = [MagicMock()]

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
