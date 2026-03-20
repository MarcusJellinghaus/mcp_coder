"""Tests for agent utility functions and run_agent execution."""

import asyncio
import builtins
import json
import logging
from pathlib import Path
from types import ModuleType
from typing import Any, Callable
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcp_coder.llm.providers.langchain.agent import (
    AGENT_MAX_STEPS,
    _check_agent_dependencies,
    _load_mcp_server_config,
    _resolve_env_vars,
    _sanitize_tool_schema,
    run_agent,
)


class TestCheckAgentDependencies:
    """Tests for _check_agent_dependencies."""

    @staticmethod
    def _import_blocker(*blocked_packages: str) -> Callable[..., ModuleType]:
        """Return a side_effect for builtins.__import__ that blocks given packages."""
        _real_import = builtins.__import__

        def _fake_import(name: str, *args: Any, **kwargs: Any) -> ModuleType:
            for pkg in blocked_packages:
                if name == pkg or name.startswith(pkg + "."):
                    raise ImportError(f"No module named {name!r}")
            return _real_import(name, *args, **kwargs)

        return _fake_import

    def test_raises_when_both_missing(self) -> None:
        """Both packages missing -> ImportError listing both."""
        with patch(
            "builtins.__import__",
            side_effect=self._import_blocker("langchain_mcp_adapters", "langgraph"),
        ):
            with pytest.raises(ImportError, match="langchain-mcp-adapters") as exc_info:
                _check_agent_dependencies()
            assert "langgraph" in str(exc_info.value)

    def test_raises_when_one_missing(self) -> None:
        """Single package missing -> ImportError listing that package."""
        with patch(
            "builtins.__import__",
            side_effect=self._import_blocker("langgraph"),
        ):
            with pytest.raises(ImportError, match="langgraph"):
                _check_agent_dependencies()

    def test_passes_when_installed(self) -> None:
        """No error when packages are importable (conftest mocks provide them)."""
        # conftest auto-mocks both packages, so this should just pass
        _check_agent_dependencies()


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

    def test_raises_on_invalid_json(self, tmp_path: Path) -> None:
        """Malformed JSON raises ValueError with user-friendly message."""
        cfg_file = tmp_path / ".mcp.json"
        cfg_file.write_text("{invalid json", encoding="utf-8")
        with pytest.raises(ValueError, match="Failed to parse MCP config file"):
            _load_mcp_server_config(str(cfg_file))

    def test_warns_on_non_stdio_transport(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Non-stdio transport logs a warning and falls back to stdio."""
        path = self._write_config(
            tmp_path,
            {"mcpServers": {"s": {"command": "cmd", "transport": "sse"}}},
        )
        with caplog.at_level(logging.WARNING):
            result = _load_mcp_server_config(path)
        assert "only 'stdio' is supported" in caplog.text
        assert "sse" in caplog.text
        assert result["s"]["transport"] == "stdio"

    def test_accepts_type_field(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Config with 'type': 'stdio' should not warn; output has transport=stdio."""
        path = self._write_config(
            tmp_path,
            {
                "mcpServers": {
                    "s": {
                        "command": "cmd",
                        "type": "stdio",
                    }
                }
            },
        )
        with caplog.at_level(logging.WARNING):
            result = _load_mcp_server_config(path)
        # No warning for "type" field
        assert "type" not in caplog.text
        # Output should have transport=stdio (forced)
        assert result["s"]["transport"] == "stdio"
        # 'type' must NOT appear in output — MultiServerMCPClient rejects it
        assert "type" not in result["s"]

    def test_type_field_excluded_from_output(self, tmp_path: Path) -> None:
        """'type' field from .mcp.json must not leak into server config dict.

        Regression test: MultiServerMCPClient passes all config keys to
        _create_stdio_session(), which raises TypeError on unknown kwargs.
        """
        path = self._write_config(
            tmp_path,
            {
                "mcpServers": {
                    "server-a": {
                        "type": "stdio",
                        "command": "echo",
                        "args": ["hello"],
                        "env": {"FOO": "bar"},
                    },
                    "server-b": {
                        "type": "stdio",
                        "command": "cat",
                    },
                }
            },
        )
        result = _load_mcp_server_config(path)
        for name in ("server-a", "server-b"):
            assert "type" not in result[name], f"'type' leaked into config for {name}"
            assert result[name]["transport"] == "stdio"


class TestSanitizeToolSchema:
    """Tests for _sanitize_tool_schema."""

    def test_adds_type_to_untyped_property(self) -> None:
        """Property with only 'title' gets 'type': 'string' added."""
        schema: dict[str, Any] = {
            "properties": {"content": {"title": "Content"}},
            "type": "object",
        }
        result = _sanitize_tool_schema(schema)
        assert result["properties"]["content"]["type"] == "string"

    def test_preserves_existing_type(self) -> None:
        """Property with an existing 'type' is not modified."""
        schema: dict[str, Any] = {
            "properties": {"name": {"title": "Name", "type": "string"}},
            "type": "object",
        }
        result = _sanitize_tool_schema(schema)
        assert result["properties"]["name"]["type"] == "string"

    def test_preserves_anyof(self) -> None:
        """Property using 'anyOf' is not modified."""
        schema: dict[str, Any] = {
            "properties": {
                "opts": {
                    "anyOf": [{"type": "string"}, {"type": "null"}],
                    "default": None,
                }
            },
            "type": "object",
        }
        result = _sanitize_tool_schema(schema)
        assert "type" not in result["properties"]["opts"]
        assert "anyOf" in result["properties"]["opts"]

    def test_preserves_ref(self) -> None:
        """Property using '$ref' is not modified."""
        schema: dict[str, Any] = {
            "properties": {"item": {"$ref": "#/definitions/Item"}},
            "type": "object",
        }
        result = _sanitize_tool_schema(schema)
        assert "type" not in result["properties"]["item"]

    def test_no_properties_returns_unchanged(self) -> None:
        """Schema without 'properties' is returned unchanged."""
        schema: dict[str, Any] = {"type": "object"}
        result = _sanitize_tool_schema(schema)
        assert result == {"type": "object"}

    def test_multiple_untyped_properties(self) -> None:
        """All untyped properties get default type."""
        schema: dict[str, Any] = {
            "properties": {
                "content": {"title": "Content"},
                "data": {"title": "Data"},
                "name": {"title": "Name", "type": "string"},
            },
            "type": "object",
        }
        result = _sanitize_tool_schema(schema)
        assert result["properties"]["content"]["type"] == "string"
        assert result["properties"]["data"]["type"] == "string"
        assert result["properties"]["name"]["type"] == "string"

    def test_does_not_mutate_original(self) -> None:
        """Original schema is not modified; a new copy is returned."""
        schema: dict[str, Any] = {
            "properties": {"x": {"title": "X"}},
            "type": "object",
        }
        result = _sanitize_tool_schema(schema)
        assert result is not schema
        assert result["properties"]["x"]["type"] == "string"
        # Original must be untouched
        assert "type" not in schema["properties"]["x"]


class TestAgentConstants:
    """Verify module-level constants."""

    def test_max_steps_value(self) -> None:
        assert AGENT_MAX_STEPS == 50


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
    """Build a mock MultiServerMCPClient that works as an async context manager.

    The mock supports ``async with MultiServerMCPClient(cfg) as client:``
    by implementing ``__aenter__`` to return itself, so ``client.connections``
    and ``client.session()`` work inside the ``async with`` block.
    """
    mock_session = AsyncMock()
    mock_list_result = MagicMock()
    mock_list_result.tools = []  # no raw MCP tools by default
    mock_session.list_tools.return_value = mock_list_result

    mock_client = MagicMock()
    mock_client.connections = {"test": {"transport": "stdio", "command": "echo"}}
    mock_client.session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_client.session.return_value.__aexit__ = AsyncMock(return_value=False)
    # Support ``async with MultiServerMCPClient(...) as client:``
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
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
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

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
