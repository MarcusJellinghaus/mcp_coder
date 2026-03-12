"""Tests for mcp_coder.llm.providers.langchain.__init__."""

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestLoadLangchainConfig:
    def test_returns_expected_keys(self) -> None:
        """_load_langchain_config returns a dict with all expected keys."""
        with patch(
            "mcp_coder.llm.providers.langchain.get_config_values",
            return_value={
                ("llm", "provider"): "langchain",
                ("llm.langchain", "backend"): "openai",
                ("llm.langchain", "model"): "gpt-4o",
                ("llm.langchain", "api_key"): None,
                ("llm.langchain", "endpoint"): None,
                ("llm.langchain", "api_version"): None,
            },
        ):
            from mcp_coder.llm.providers.langchain import _load_langchain_config

            cfg = _load_langchain_config()
        assert set(cfg.keys()) == {
            "provider",
            "backend",
            "model",
            "api_key",
            "endpoint",
            "api_version",
        }

    def test_env_var_overrides_config_values(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """MCP_CODER_LLM_LANGCHAIN_* env vars override config.toml values."""
        monkeypatch.setenv("MCP_CODER_LLM_LANGCHAIN_BACKEND", "gemini")
        monkeypatch.setenv("MCP_CODER_LLM_LANGCHAIN_MODEL", "gemini-2.0-flash")
        with patch(
            "mcp_coder.llm.providers.langchain.get_config_values",
            return_value={
                ("llm", "provider"): "langchain",
                ("llm.langchain", "backend"): "openai",
                ("llm.langchain", "model"): "gpt-4o",
                ("llm.langchain", "api_key"): None,
                ("llm.langchain", "endpoint"): None,
                ("llm.langchain", "api_version"): None,
            },
        ):
            from mcp_coder.llm.providers.langchain import _load_langchain_config

            cfg = _load_langchain_config()
        assert cfg["backend"] == "gemini"
        assert cfg["model"] == "gemini-2.0-flash"

    def test_env_var_does_not_override_when_empty(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Empty env vars do not override config.toml values."""
        monkeypatch.delenv("MCP_CODER_LLM_LANGCHAIN_BACKEND", raising=False)
        monkeypatch.delenv("MCP_CODER_LLM_LANGCHAIN_MODEL", raising=False)
        with patch(
            "mcp_coder.llm.providers.langchain.get_config_values",
            return_value={
                ("llm", "provider"): "langchain",
                ("llm.langchain", "backend"): "openai",
                ("llm.langchain", "model"): "gpt-4o",
                ("llm.langchain", "api_key"): None,
                ("llm.langchain", "endpoint"): None,
                ("llm.langchain", "api_version"): None,
            },
        ):
            from mcp_coder.llm.providers.langchain import _load_langchain_config

            cfg = _load_langchain_config()
        assert cfg["backend"] == "openai"
        assert cfg["model"] == "gpt-4o"


class TestAskLangchain:
    def _make_config(self, backend: str = "openai") -> dict[str, str | None]:
        return {
            "provider": "langchain",
            "backend": backend,
            "model": "gpt-4o",
            "api_key": None,
            "endpoint": None,
            "api_version": None,
        }

    def test_returns_llm_response_dict(self) -> None:
        """ask_langchain returns a complete LLMResponseDict."""
        with (
            patch(
                "mcp_coder.llm.providers.langchain._load_langchain_config",
                return_value=self._make_config(),
            ),
            patch(
                "mcp_coder.llm.providers.langchain.load_langchain_history",
                return_value=[],
            ),
            patch("mcp_coder.llm.providers.langchain.store_langchain_history"),
            patch(
                "mcp_coder.llm.providers.langchain.openai_backend.ask_openai",
                return_value=("Hello!", {"content": "Hello!"}),
            ),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain

            result = ask_langchain("Hi")
        assert result["text"] == "Hello!"
        assert result["provider"] == "langchain"
        assert result["session_id"] is not None

    def test_generates_session_id_when_none_given(self) -> None:
        """A UUID session_id is generated when none is provided."""
        with (
            patch(
                "mcp_coder.llm.providers.langchain._load_langchain_config",
                return_value=self._make_config(),
            ),
            patch(
                "mcp_coder.llm.providers.langchain.load_langchain_history",
                return_value=[],
            ),
            patch("mcp_coder.llm.providers.langchain.store_langchain_history"),
            patch(
                "mcp_coder.llm.providers.langchain.openai_backend.ask_openai",
                return_value=("ok", {}),
            ),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain

            result = ask_langchain("question")
        # Must be a valid UUID
        uuid.UUID(str(result["session_id"]))

    def test_preserves_provided_session_id(self) -> None:
        """When session_id is passed, it is preserved in the response."""
        sid = "my-session-123"
        with (
            patch(
                "mcp_coder.llm.providers.langchain._load_langchain_config",
                return_value=self._make_config(),
            ),
            patch(
                "mcp_coder.llm.providers.langchain.load_langchain_history",
                return_value=[],
            ),
            patch("mcp_coder.llm.providers.langchain.store_langchain_history"),
            patch(
                "mcp_coder.llm.providers.langchain.openai_backend.ask_openai",
                return_value=("ok", {}),
            ),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain

            result = ask_langchain("question", session_id=sid)
        assert result["session_id"] == sid

    def test_raises_value_error_for_unknown_backend(self) -> None:
        """Unsupported backend raises ValueError with a clear message."""
        with (
            patch(
                "mcp_coder.llm.providers.langchain._load_langchain_config",
                return_value={**self._make_config(), "backend": "unknown_llm"},
            ),
            patch(
                "mcp_coder.llm.providers.langchain.load_langchain_history",
                return_value=[],
            ),
            patch("mcp_coder.llm.providers.langchain.store_langchain_history"),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain

            with pytest.raises(ValueError, match="unknown_llm"):
                ask_langchain("question")

    def test_raises_value_error_when_backend_not_configured(self) -> None:
        """Missing backend config raises ValueError."""
        with (
            patch(
                "mcp_coder.llm.providers.langchain._load_langchain_config",
                return_value={**self._make_config(), "backend": None},
            ),
            patch(
                "mcp_coder.llm.providers.langchain.load_langchain_history",
                return_value=[],
            ),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain

            with pytest.raises(ValueError, match="backend"):
                ask_langchain("question")

    def test_history_is_updated_and_stored(self) -> None:
        """After a call, both human and AI messages are appended to history."""
        store_mock = MagicMock()
        with (
            patch(
                "mcp_coder.llm.providers.langchain._load_langchain_config",
                return_value=self._make_config(),
            ),
            patch(
                "mcp_coder.llm.providers.langchain.load_langchain_history",
                return_value=[{"role": "human", "content": "prev"}],
            ),
            patch(
                "mcp_coder.llm.providers.langchain.store_langchain_history",
                store_mock,
            ),
            patch(
                "mcp_coder.llm.providers.langchain.openai_backend.ask_openai",
                return_value=("answer", {}),
            ),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain

            ask_langchain("new question", session_id="sid")
        stored_messages = store_mock.call_args[0][1]  # second positional arg
        assert {"role": "human", "content": "prev"} in stored_messages
        assert {"role": "human", "content": "new question"} in stored_messages
        assert {"role": "ai", "content": "answer"} in stored_messages


class TestCreateChatModel:
    """Tests for _create_chat_model() dispatcher."""

    def test_dispatches_to_openai_backend(self) -> None:
        """Config with backend=openai calls create_openai_model."""
        mock_model = MagicMock()
        with patch(
            "mcp_coder.llm.providers.langchain.openai_backend.create_openai_model",
            return_value=mock_model,
        ) as mock_create:
            from mcp_coder.llm.providers.langchain import _create_chat_model

            result = _create_chat_model(
                {"backend": "openai", "model": "gpt-4o", "api_key": "k"}
            )
        assert result is mock_model
        mock_create.assert_called_once_with(
            model="gpt-4o", api_key="k", endpoint=None, api_version=None
        )

    def test_dispatches_to_gemini_backend(self) -> None:
        """Config with backend=gemini calls create_gemini_model."""
        mock_model = MagicMock()
        with patch(
            "mcp_coder.llm.providers.langchain.gemini_backend.create_gemini_model",
            return_value=mock_model,
        ) as mock_create:
            from mcp_coder.llm.providers.langchain import _create_chat_model

            result = _create_chat_model(
                {"backend": "gemini", "model": "gemini-2.0-flash", "api_key": "k"}
            )
        assert result is mock_model
        mock_create.assert_called_once_with(model="gemini-2.0-flash", api_key="k")

    def test_dispatches_to_anthropic_backend(self) -> None:
        """Config with backend=anthropic calls create_anthropic_model."""
        mock_model = MagicMock()
        with patch(
            "mcp_coder.llm.providers.langchain.anthropic_backend.create_anthropic_model",
            return_value=mock_model,
        ) as mock_create:
            from mcp_coder.llm.providers.langchain import _create_chat_model

            result = _create_chat_model(
                {
                    "backend": "anthropic",
                    "model": "claude-sonnet-4-20250514",
                    "api_key": "k",
                }
            )
        assert result is mock_model
        mock_create.assert_called_once_with(
            model="claude-sonnet-4-20250514", api_key="k"
        )

    def test_raises_on_unknown_backend(self) -> None:
        """Unknown backend raises ValueError."""
        from mcp_coder.llm.providers.langchain import _create_chat_model

        with pytest.raises(ValueError, match="unknown_llm"):
            _create_chat_model({"backend": "unknown_llm", "model": "x"})


class TestCheckAgentDependencies:
    """Tests for _check_agent_dependencies()."""

    def test_passes_when_both_installed(self) -> None:
        """No error when both packages importable."""
        from mcp_coder.llm.providers.langchain.agent import (
            _check_agent_dependencies,
        )

        # Both are mocked in conftest, so this should not raise
        _check_agent_dependencies()

    def test_raises_clear_error_when_mcp_adapters_missing(self) -> None:
        """ImportError with install instructions for langchain-mcp-adapters."""
        import importlib
        import sys

        from mcp_coder.llm.providers.langchain import agent as agent_module

        saved = sys.modules.get("langchain_mcp_adapters")
        sys.modules["langchain_mcp_adapters"] = None  # type: ignore[assignment]
        try:
            importlib.reload(agent_module)
            with pytest.raises(ImportError, match="langchain-mcp-adapters"):
                agent_module._check_agent_dependencies()
        finally:
            if saved is not None:
                sys.modules["langchain_mcp_adapters"] = saved
            else:
                sys.modules.pop("langchain_mcp_adapters", None)
            importlib.reload(agent_module)

    def test_raises_clear_error_when_langgraph_missing(self) -> None:
        """ImportError with install instructions for langgraph."""
        import importlib
        import sys

        from mcp_coder.llm.providers.langchain import agent as agent_module

        saved = sys.modules.get("langgraph")
        sys.modules["langgraph"] = None  # type: ignore[assignment]
        try:
            importlib.reload(agent_module)
            with pytest.raises(ImportError, match="langgraph"):
                agent_module._check_agent_dependencies()
        finally:
            if saved is not None:
                sys.modules["langgraph"] = saved
            else:
                sys.modules.pop("langgraph", None)
            importlib.reload(agent_module)


class TestAskLangchainAgentMode:
    """Tests for agent mode routing in ask_langchain()."""

    def _make_config(self, backend: str = "openai") -> dict[str, str | None]:
        return {
            "provider": "langchain",
            "backend": backend,
            "model": "gpt-4o",
            "api_key": None,
            "endpoint": None,
            "api_version": None,
        }

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
                return_value=self._make_config(),
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
        """When mcp_config is None, existing backend dispatch used."""
        with (
            patch(
                "mcp_coder.llm.providers.langchain._load_langchain_config",
                return_value=self._make_config(),
            ),
            patch(
                "mcp_coder.llm.providers.langchain.load_langchain_history",
                return_value=[],
            ),
            patch("mcp_coder.llm.providers.langchain.store_langchain_history"),
            patch(
                "mcp_coder.llm.providers.langchain.openai_backend.ask_openai",
                return_value=("text answer", {}),
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
                return_value=self._make_config(),
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
        serialized_messages = [
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
                return_value=self._make_config(),
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
        stored = store_mock.call_args[0][1]
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
                return_value=self._make_config(),
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
        assert len(raw["tool_trace"]) == 1
        assert "messages" in raw

    def test_backward_compatible_text_only(self) -> None:
        """Existing text-only call still works (regression check)."""
        with (
            patch(
                "mcp_coder.llm.providers.langchain._load_langchain_config",
                return_value=self._make_config("gemini"),
            ),
            patch(
                "mcp_coder.llm.providers.langchain.load_langchain_history",
                return_value=[],
            ),
            patch("mcp_coder.llm.providers.langchain.store_langchain_history"),
            patch(
                "mcp_coder.llm.providers.langchain.gemini_backend.ask_gemini",
                return_value=("gemini reply", {"content": "gemini reply"}),
            ),
        ):
            from mcp_coder.llm.providers.langchain import ask_langchain

            result = ask_langchain("Hi", timeout=10)
        assert result["text"] == "gemini reply"
        assert result["provider"] == "langchain"


class TestAgentModeMLflowLogging:
    """Tests for MLflow logging in agent mode."""

    def _make_config(self, backend: str = "openai") -> dict[str, str | None]:
        return {
            "provider": "langchain",
            "backend": backend,
            "model": "gpt-4o",
            "api_key": None,
            "endpoint": None,
            "api_version": None,
        }

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
                return_value=self._make_config(),
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
                return_value=self._make_config(),
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
                return_value=self._make_config(),
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
