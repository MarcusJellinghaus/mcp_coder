from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.llm.interface import LLMTimeoutError, prompt_llm
from mcp_coder.utils.subprocess_runner import TimeoutExpired
from tests.llm.test_interface import PROJECT_DIR


class TestMlflowConversationIntegration:
    """Tests for mlflow_conversation context manager wiring in prompt_llm."""

    @patch("mcp_coder.llm.interface.mlflow_conversation")
    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_mlflow_conversation_called_for_claude(
        self, mock_cli: MagicMock, mock_mlflow_cm: MagicMock
    ) -> None:
        """prompt_llm wraps claude provider call with mlflow_conversation."""
        mock_ctx: dict[str, Any] = {"response_data": None, "error": None}
        mock_mlflow_cm.return_value.__enter__ = MagicMock(return_value=mock_ctx)
        mock_mlflow_cm.return_value.__exit__ = MagicMock(return_value=False)
        mock_cli.return_value = {
            "text": "reply",
            "session_id": "s1",
            "version": "1.0",
            "timestamp": "2025-01-01",
            "provider": "claude",
            "raw_response": {},
        }

        result = prompt_llm(
            "hello",
            provider="claude",
            session_id="s1",
            project_dir="/work",
            branch_name="main",
        )

        mock_mlflow_cm.assert_called_once_with(
            "hello",
            "claude",
            "s1",
            {"branch_name": "main", "working_directory": str(Path("/work"))},
        )
        assert result["text"] == "reply"
        assert mock_ctx["response_data"] == mock_cli.return_value

    @patch("mcp_coder.llm.interface.mlflow_conversation")
    @patch("mcp_coder.llm.providers.langchain.ask_langchain")
    def test_mlflow_conversation_called_for_langchain(
        self, mock_langchain: MagicMock, mock_mlflow_cm: MagicMock
    ) -> None:
        """prompt_llm wraps langchain provider call with mlflow_conversation."""
        mock_ctx: dict[str, Any] = {"response_data": None, "error": None}
        mock_mlflow_cm.return_value.__enter__ = MagicMock(return_value=mock_ctx)
        mock_mlflow_cm.return_value.__exit__ = MagicMock(return_value=False)
        mock_langchain.return_value = {
            "text": "lc reply",
            "session_id": "lc-s1",
            "version": "1.0",
            "timestamp": "2025-01-01",
            "provider": "langchain",
            "raw_response": {},
        }

        result = prompt_llm(
            "hello", provider="langchain", session_id="lc-s1", project_dir=PROJECT_DIR
        )

        mock_mlflow_cm.assert_called_once_with(
            "hello",
            "langchain",
            "lc-s1",
            {"branch_name": None, "working_directory": PROJECT_DIR},
        )
        assert result["text"] == "lc reply"
        assert mock_ctx["response_data"] == mock_langchain.return_value

    @patch("mcp_coder.llm.interface.mlflow_conversation")
    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_mlflow_conversation_sees_timeout_exception(
        self, mock_cli: MagicMock, mock_mlflow_cm: MagicMock
    ) -> None:
        """TimeoutExpired propagates through context manager so Phase 2 logs error."""
        mock_ctx: dict[str, Any] = {"response_data": None, "error": None}
        mock_mlflow_cm.return_value.__enter__ = MagicMock(return_value=mock_ctx)
        mock_mlflow_cm.return_value.__exit__ = MagicMock(return_value=False)
        mock_cli.side_effect = TimeoutExpired(cmd="claude", timeout=30)

        with pytest.raises(LLMTimeoutError):
            prompt_llm("hello", provider="claude", timeout=30, project_dir=PROJECT_DIR)

        # Context manager __exit__ was called (exception propagated through it)
        mock_mlflow_cm.return_value.__exit__.assert_called_once()
        exit_args = mock_mlflow_cm.return_value.__exit__.call_args[0]
        assert exit_args[0] is LLMTimeoutError

    @patch("mcp_coder.llm.interface.mlflow_conversation")
    def test_mlflow_conversation_not_called_for_unsupported_provider(
        self, mock_mlflow_cm: MagicMock
    ) -> None:
        """ValueError for unsupported provider is raised before context manager."""
        with pytest.raises(ValueError, match="Unsupported provider"):
            prompt_llm("hello", provider="gpt", project_dir=PROJECT_DIR)

        mock_mlflow_cm.assert_not_called()

    @patch("mcp_coder.llm.interface.mlflow_conversation")
    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_metadata_includes_branch_and_working_dir(
        self, mock_cli: MagicMock, mock_mlflow_cm: MagicMock
    ) -> None:
        """Metadata dict passed to mlflow_conversation contains branch_name and working_directory."""
        mock_ctx: dict[str, Any] = {"response_data": None, "error": None}
        mock_mlflow_cm.return_value.__enter__ = MagicMock(return_value=mock_ctx)
        mock_mlflow_cm.return_value.__exit__ = MagicMock(return_value=False)
        mock_cli.return_value = {
            "text": "r",
            "session_id": "s",
            "version": "1.0",
            "timestamp": "2025-01-01",
            "provider": "claude",
            "raw_response": {},
        }

        prompt_llm(
            "q",
            provider="claude",
            project_dir="/my/dir",
            branch_name="feat-x",
        )

        _, args, _ = mock_mlflow_cm.mock_calls[0]
        metadata = args[3]
        assert metadata == {
            "branch_name": "feat-x",
            "working_directory": str(Path("/my/dir")),
        }

    @patch("mcp_coder.llm.interface.mlflow_conversation")
    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_metadata_branch_name_defaults_to_none(
        self, mock_cli: MagicMock, mock_mlflow_cm: MagicMock
    ) -> None:
        """When branch_name is not provided it is None; working_directory is project_dir."""
        mock_ctx: dict[str, Any] = {"response_data": None, "error": None}
        mock_mlflow_cm.return_value.__enter__ = MagicMock(return_value=mock_ctx)
        mock_mlflow_cm.return_value.__exit__ = MagicMock(return_value=False)
        mock_cli.return_value = {
            "text": "r",
            "session_id": "s",
            "version": "1.0",
            "timestamp": "2025-01-01",
            "provider": "claude",
            "raw_response": {},
        }

        prompt_llm("q", project_dir=PROJECT_DIR)

        _, args, _ = mock_mlflow_cm.mock_calls[0]
        metadata = args[3]
        assert metadata["branch_name"] is None
        assert metadata["working_directory"] == PROJECT_DIR
