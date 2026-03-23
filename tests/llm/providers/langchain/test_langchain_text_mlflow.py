"""Tests for MLflow logging in LangChain text mode (_log_text_mlflow)."""

from unittest.mock import MagicMock, patch

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


class TestLogTextMlflow:
    """Tests for _log_text_mlflow() function."""

    def test_logs_params_and_ends_run(self) -> None:
        """_log_text_mlflow starts run, logs params, ends run."""
        mock_mlflow = MagicMock()
        with patch(
            "mcp_coder.llm.providers.langchain.get_mlflow_logger",
            return_value=mock_mlflow,
        ):
            from mcp_coder.llm.providers.langchain import _log_text_mlflow

            _log_text_mlflow(_make_config(), "session-123")

        mock_mlflow.start_run.assert_called_once_with(session_id="session-123")
        mock_mlflow.log_params.assert_called_once()
        params = mock_mlflow.log_params.call_args[0][0]
        assert params["backend"] == "openai"
        assert params["model"] == "gpt-4o"
        assert params["mode"] == "text"
        mock_mlflow.end_run.assert_called_once_with(session_id="session-123")

    def test_exception_is_swallowed(self) -> None:
        """MLflow errors don't propagate to caller."""
        mock_mlflow = MagicMock()
        mock_mlflow.start_run.side_effect = RuntimeError("MLflow down")
        with patch(
            "mcp_coder.llm.providers.langchain.get_mlflow_logger",
            return_value=mock_mlflow,
        ):
            from mcp_coder.llm.providers.langchain import _log_text_mlflow

            # Should not raise
            _log_text_mlflow(_make_config(), "session-123")

    def test_ask_text_calls_log_text_mlflow(self) -> None:
        """_ask_text() calls _log_text_mlflow() after successful invoke."""
        mock_model = MagicMock()
        mock_ai_msg = MagicMock()
        mock_ai_msg.content = "hello"
        mock_model.invoke.return_value = mock_ai_msg

        mock_log = MagicMock()
        with (
            patch(
                "mcp_coder.llm.providers.langchain._create_chat_model",
                return_value=mock_model,
            ),
            patch(
                "mcp_coder.llm.providers.langchain.load_langchain_history",
                return_value=[],
            ),
            patch("mcp_coder.llm.providers.langchain.store_langchain_history"),
            patch(
                "mcp_coder.llm.providers.langchain._log_text_mlflow",
                mock_log,
            ),
        ):
            from mcp_coder.llm.providers.langchain import _ask_text

            config = _make_config()
            _ask_text("question", config, "openai", "sid-1", timeout=30)

        mock_log.assert_called_once_with(config, "sid-1")

    def test_ask_text_skips_logging_on_invoke_failure(self) -> None:
        """_ask_text() does not call _log_text_mlflow() if chat_model.invoke raises."""
        mock_model = MagicMock()
        mock_model.invoke.side_effect = RuntimeError("Model error")

        mock_log = MagicMock()
        with (
            patch(
                "mcp_coder.llm.providers.langchain._create_chat_model",
                return_value=mock_model,
            ),
            patch(
                "mcp_coder.llm.providers.langchain.load_langchain_history",
                return_value=[],
            ),
            patch("mcp_coder.llm.providers.langchain.store_langchain_history"),
            patch(
                "mcp_coder.llm.providers.langchain._log_text_mlflow",
                mock_log,
            ),
        ):
            from mcp_coder.llm.providers.langchain import _ask_text

            with pytest.raises(RuntimeError, match="Model error"):
                _ask_text("question", _make_config(), "openai", "sid-1", timeout=30)

        mock_log.assert_not_called()
