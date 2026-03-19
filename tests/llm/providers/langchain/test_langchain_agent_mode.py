"""Tests for agent mode routing and MLflow logging in langchain provider."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _make_config(backend: str = "openai") -> dict[str, str | None]:
    """Build a minimal langchain config dict for testing."""
    return {
        "provider": "langchain",
        "backend": backend,
        "model": "gpt-4o",
        "api_key": None,
        "endpoint": None,
        "api_version": None,
    }


class TestAskLangchainAgentMode:
    """Tests for agent mode routing in ask_langchain()."""

    def test_routes_to_agent_when_mcp_config_provided(self) -> None:
        """When mcp_config is set, run_agent is called."""
        mock_run_agent = AsyncMock(
            return_value=(
                "agent answer",
                [{"type": "human", "content": "q"}],
                {"agent_steps": 1, "total_tool_calls": 0, "tool_trace": []},
            )
        )
        with (
            patch(
                "mcp_coder.llm.providers.langchain._load_langchain_config",
                return_value=_make_config(),
            ),
            patch(
                "mcp_coder.llm.providers.langchain.agent._check_agent_dependencies",
            ),
            patch(
                "mcp_coder.llm.providers.langchain.agent.run_agent",
                mock_run_agent,
            ),
            patch(
                "mcp_coder.llm.providers.langchain._create_chat_model",
                return_value=MagicMock(),
            ),
            patch(
                "mcp_coder.llm.providers.langchain.load_langchain_history",
                return_value=[],
            ),
            patch("mcp_coder.llm.providers.langchain.store_langchain_history"),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain

            result = ask_langchain("question", mcp_config="/path/to/.mcp.json")
        assert result["text"] == "agent answer"
        mock_run_agent.assert_called_once()

    def test_routes_to_text_mode_when_mcp_config_none(self) -> None:
        """When mcp_config is None, _create_chat_model dispatch used."""
        mock_model = MagicMock()
        mock_ai_msg = MagicMock()
        mock_ai_msg.content = "text answer"
        mock_model.invoke.return_value = mock_ai_msg
        with (
            patch(
                "mcp_coder.llm.providers.langchain._load_langchain_config",
                return_value=_make_config(),
            ),
            patch(
                "mcp_coder.llm.providers.langchain.load_langchain_history",
                return_value=[],
            ),
            patch("mcp_coder.llm.providers.langchain.store_langchain_history"),
            patch(
                "mcp_coder.llm.providers.langchain._create_chat_model",
                return_value=mock_model,
            ),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain

            result = ask_langchain("question", mcp_config=None)
        assert result["text"] == "text answer"

    def test_raises_import_error_when_deps_missing(self) -> None:
        """Agent mode raises ImportError if langchain-mcp-adapters not installed."""
        with (
            patch(
                "mcp_coder.llm.providers.langchain._load_langchain_config",
                return_value=_make_config(),
            ),
            patch(
                "mcp_coder.llm.providers.langchain.agent._check_agent_dependencies",
                side_effect=ImportError("langchain-mcp-adapters"),
            ),
            patch(
                "mcp_coder.llm.providers.langchain.load_langchain_history",
                return_value=[],
            ),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain

            with pytest.raises(ImportError, match="langchain-mcp-adapters"):
                ask_langchain("question", mcp_config="/path/to/.mcp.json")

    def test_agent_mode_stores_full_history(self) -> None:
        """Agent mode stores serialized message history including tool calls."""
        serialized_messages: list[dict[str, Any]] = [
            {"type": "human", "content": "question"},
            {"type": "ai", "content": "", "tool_calls": [{"name": "read_file"}]},
            {"type": "tool", "name": "read_file", "content": "file data"},
            {"type": "ai", "content": "Here is the answer"},
        ]
        mock_run_agent = AsyncMock(
            return_value=(
                "Here is the answer",
                serialized_messages,
                {"agent_steps": 1, "total_tool_calls": 1, "tool_trace": []},
            )
        )
        store_mock = MagicMock()
        with (
            patch(
                "mcp_coder.llm.providers.langchain._load_langchain_config",
                return_value=_make_config(),
            ),
            patch(
                "mcp_coder.llm.providers.langchain.agent._check_agent_dependencies",
            ),
            patch(
                "mcp_coder.llm.providers.langchain.agent.run_agent",
                mock_run_agent,
            ),
            patch(
                "mcp_coder.llm.providers.langchain._create_chat_model",
                return_value=MagicMock(),
            ),
            patch(
                "mcp_coder.llm.providers.langchain.load_langchain_history",
                return_value=[],
            ),
            patch(
                "mcp_coder.llm.providers.langchain.store_langchain_history",
                store_mock,
            ),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain

            ask_langchain("question", session_id="sid", mcp_config="/path/.mcp.json")
        stored: list[dict[str, object]] = store_mock.call_args[0][1]
        assert len(stored) == 4
        assert stored[1].get("tool_calls") is not None

    def test_agent_mode_populates_raw_response(self) -> None:
        """raw_response contains messages, backend, model, agent stats."""
        stats = {
            "agent_steps": 2,
            "total_tool_calls": 3,
            "tool_trace": [{"name": "t", "args": {}, "result": "r"}],
        }
        mock_run_agent = AsyncMock(
            return_value=("answer", [{"type": "ai", "content": "answer"}], stats)
        )
        with (
            patch(
                "mcp_coder.llm.providers.langchain._load_langchain_config",
                return_value=_make_config(),
            ),
            patch(
                "mcp_coder.llm.providers.langchain.agent._check_agent_dependencies",
            ),
            patch(
                "mcp_coder.llm.providers.langchain.agent.run_agent",
                mock_run_agent,
            ),
            patch(
                "mcp_coder.llm.providers.langchain._create_chat_model",
                return_value=MagicMock(),
            ),
            patch(
                "mcp_coder.llm.providers.langchain.load_langchain_history",
                return_value=[],
            ),
            patch("mcp_coder.llm.providers.langchain.store_langchain_history"),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain

            result = ask_langchain("question", mcp_config="/path/.mcp.json")
        raw = result["raw_response"]
        assert raw["backend"] == "openai"
        assert raw["model"] == "gpt-4o"
        assert raw["agent_steps"] == 2
        assert raw["total_tool_calls"] == 3
        tool_trace = raw["tool_trace"]
        assert isinstance(tool_trace, list)
        assert len(tool_trace) == 1
        assert "messages" in raw

    def test_backward_compatible_text_only(self) -> None:
        """Existing text-only call still works (regression check)."""
        mock_model = MagicMock()
        mock_ai_msg = MagicMock()
        mock_ai_msg.content = "gemini reply"
        mock_model.invoke.return_value = mock_ai_msg
        with (
            patch(
                "mcp_coder.llm.providers.langchain._load_langchain_config",
                return_value=_make_config("gemini"),
            ),
            patch(
                "mcp_coder.llm.providers.langchain.load_langchain_history",
                return_value=[],
            ),
            patch("mcp_coder.llm.providers.langchain.store_langchain_history"),
            patch(
                "mcp_coder.llm.providers.langchain._create_chat_model",
                return_value=mock_model,
            ),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain

            result = ask_langchain("Hi", timeout=10)
        assert result["text"] == "gemini reply"
        assert result["provider"] == "langchain"


class TestAgentModeMLflowLogging:
    """Tests for MLflow logging in agent mode."""

    def test_agent_mode_logs_to_mlflow(self) -> None:
        """MLflow logger receives params, metrics, and tool_trace artifact."""
        stats = {
            "agent_steps": 2,
            "total_tool_calls": 3,
            "tool_trace": [
                {"name": "read_file", "args": {"path": "x"}, "result": "data"},
            ],
        }
        mock_run_agent = AsyncMock(
            return_value=("answer", [{"type": "ai", "content": "answer"}], stats)
        )
        mock_mlflow = MagicMock()
        with (
            patch(
                "mcp_coder.llm.providers.langchain._load_langchain_config",
                return_value=_make_config(),
            ),
            patch(
                "mcp_coder.llm.providers.langchain.agent._check_agent_dependencies",
            ),
            patch(
                "mcp_coder.llm.providers.langchain.agent.run_agent",
                mock_run_agent,
            ),
            patch(
                "mcp_coder.llm.providers.langchain._create_chat_model",
                return_value=MagicMock(),
            ),
            patch(
                "mcp_coder.llm.providers.langchain.load_langchain_history",
                return_value=[],
            ),
            patch("mcp_coder.llm.providers.langchain.store_langchain_history"),
            patch(
                "mcp_coder.llm.providers.langchain.get_mlflow_logger",
                return_value=mock_mlflow,
            ),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain

            ask_langchain("question", mcp_config="/path/.mcp.json")

        mock_mlflow.start_run.assert_called_once()
        mock_mlflow.log_params.assert_called_once()
        params = mock_mlflow.log_params.call_args[0][0]
        assert params["backend"] == "openai"
        assert params["model"] == "gpt-4o"

        mock_mlflow.log_metrics.assert_called_once()
        metrics = mock_mlflow.log_metrics.call_args[0][0]
        assert metrics["agent_steps"] == 2.0
        assert metrics["total_tool_calls"] == 3.0

        mock_mlflow.log_artifact.assert_called_once()
        artifact_call = mock_mlflow.log_artifact.call_args
        assert artifact_call[0][1] == "tool_trace.json"

        mock_mlflow.end_run.assert_called_once()

    def test_mlflow_failure_does_not_break_agent_mode(self) -> None:
        """MLflow errors are caught and do not prevent agent response."""
        mock_run_agent = AsyncMock(
            return_value=(
                "answer",
                [{"type": "ai", "content": "answer"}],
                {"agent_steps": 1, "total_tool_calls": 0, "tool_trace": []},
            )
        )
        mock_mlflow = MagicMock()
        mock_mlflow.start_run.side_effect = RuntimeError("MLflow down")
        with (
            patch(
                "mcp_coder.llm.providers.langchain._load_langchain_config",
                return_value=_make_config(),
            ),
            patch(
                "mcp_coder.llm.providers.langchain.agent._check_agent_dependencies",
            ),
            patch(
                "mcp_coder.llm.providers.langchain.agent.run_agent",
                mock_run_agent,
            ),
            patch(
                "mcp_coder.llm.providers.langchain._create_chat_model",
                return_value=MagicMock(),
            ),
            patch(
                "mcp_coder.llm.providers.langchain.load_langchain_history",
                return_value=[],
            ),
            patch("mcp_coder.llm.providers.langchain.store_langchain_history"),
            patch(
                "mcp_coder.llm.providers.langchain.get_mlflow_logger",
                return_value=mock_mlflow,
            ),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain

            result = ask_langchain("question", mcp_config="/path/.mcp.json")
        # Should still return a valid response despite MLflow failure
        assert result["text"] == "answer"

    def test_no_tool_trace_artifact_when_empty(self) -> None:
        """No tool_trace.json artifact logged when tool_trace is empty."""
        stats = {
            "agent_steps": 1,
            "total_tool_calls": 0,
            "tool_trace": [],
        }
        mock_run_agent = AsyncMock(
            return_value=("answer", [{"type": "ai", "content": "answer"}], stats)
        )
        mock_mlflow = MagicMock()
        with (
            patch(
                "mcp_coder.llm.providers.langchain._load_langchain_config",
                return_value=_make_config(),
            ),
            patch(
                "mcp_coder.llm.providers.langchain.agent._check_agent_dependencies",
            ),
            patch(
                "mcp_coder.llm.providers.langchain.agent.run_agent",
                mock_run_agent,
            ),
            patch(
                "mcp_coder.llm.providers.langchain._create_chat_model",
                return_value=MagicMock(),
            ),
            patch(
                "mcp_coder.llm.providers.langchain.load_langchain_history",
                return_value=[],
            ),
            patch("mcp_coder.llm.providers.langchain.store_langchain_history"),
            patch(
                "mcp_coder.llm.providers.langchain.get_mlflow_logger",
                return_value=mock_mlflow,
            ),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain

            ask_langchain("question", mcp_config="/path/.mcp.json")

        mock_mlflow.log_artifact.assert_not_called()
