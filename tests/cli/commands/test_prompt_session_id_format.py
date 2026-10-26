import argparse
import logging
from typing import Any
from unittest.mock import Mock, patch

import pytest

from mcp_coder.cli.commands.prompt import execute_prompt


class TestSessionIdOutputFormat:
    """Tests for --output-format session-id functionality."""

    @patch("mcp_coder.cli.commands.prompt.resolve_llm_method")
    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    @patch("mcp_coder.cli.commands.prompt.prompt_llm")
    def test_session_id_format_returns_only_session_id(
        self,
        mock_prompt_llm: Mock,
        mock_prepare_env: Mock,
        mock_resolve_llm: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """With --output-format session-id, prints only the session_id."""
        mock_resolve_llm.return_value = ("claude", "cli argument")
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test"}
        mock_response: dict[str, Any] = {
            "text": "Response text here",
            "session_id": "abc123-session-id",
            "version": "1.0",
            "timestamp": "2024-01-01T00:00:00",
            "provider": "claude",
            "raw_response": {},
        }
        mock_prompt_llm.return_value = mock_response

        args = argparse.Namespace(
            prompt="test prompt",
            output_format="session-id",
            timeout=30,
            llm_method="claude",
            session_id=None,
            continue_session_from=None,
            continue_session=False,
            project_dir=None,
            mcp_config=None,
            settings=None,
        )

        result = execute_prompt(args)

        assert result == 0
        captured = capsys.readouterr()
        assert captured.out.strip() == "abc123-session-id"

    @patch("mcp_coder.cli.commands.prompt.resolve_llm_method")
    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    @patch("mcp_coder.cli.commands.prompt.prompt_llm")
    def test_session_id_format_error_when_no_session_id(
        self,
        mock_prompt_llm: Mock,
        mock_prepare_env: Mock,
        mock_resolve_llm: Mock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Returns error when response has no session_id."""
        mock_resolve_llm.return_value = ("claude", "cli argument")
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test"}
        mock_response: dict[str, Any] = {
            "text": "Response text",
            "session_id": None,  # No session_id
            "version": "1.0",
            "timestamp": "2024-01-01T00:00:00",
            "provider": "claude",
            "raw_response": {},
        }
        mock_prompt_llm.return_value = mock_response

        args = argparse.Namespace(
            prompt="test prompt",
            output_format="session-id",
            timeout=30,
            llm_method="claude",
            session_id=None,
            continue_session_from=None,
            continue_session=False,
            project_dir=None,
            mcp_config=None,
            settings=None,
        )

        with caplog.at_level(logging.DEBUG):
            result = execute_prompt(args)

        assert result == 1  # Error exit code
        assert "No session_id in response" in caplog.text

    @patch("mcp_coder.cli.commands.prompt.resolve_llm_method")
    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    @patch("mcp_coder.cli.commands.prompt.prompt_llm")
    def test_session_id_format_error_when_empty_session_id(
        self,
        mock_prompt_llm: Mock,
        mock_prepare_env: Mock,
        mock_resolve_llm: Mock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Returns error when response has empty session_id string."""
        mock_resolve_llm.return_value = ("claude", "cli argument")
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test"}
        mock_response: dict[str, Any] = {
            "text": "Response text",
            "session_id": "",  # Empty session_id
            "version": "1.0",
            "timestamp": "2024-01-01T00:00:00",
            "provider": "claude",
            "raw_response": {},
        }
        mock_prompt_llm.return_value = mock_response

        args = argparse.Namespace(
            prompt="test prompt",
            output_format="session-id",
            timeout=30,
            llm_method="claude",
            session_id=None,
            continue_session_from=None,
            continue_session=False,
            project_dir=None,
            mcp_config=None,
            settings=None,
        )

        with caplog.at_level(logging.DEBUG):
            result = execute_prompt(args)

        assert result == 1  # Error exit code
        assert "No session_id in response" in caplog.text

    @patch("mcp_coder.cli.commands.prompt.resolve_llm_method")
    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    @patch("mcp_coder.cli.commands.prompt.prompt_llm")
    def test_session_id_format_with_resume(
        self,
        mock_prompt_llm: Mock,
        mock_prepare_env: Mock,
        mock_resolve_llm: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Session ID format works when resuming existing session."""
        mock_resolve_llm.return_value = ("claude", "cli argument")
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test"}
        mock_response: dict[str, Any] = {
            "text": "Continued response",
            "session_id": "existing-session-456",
            "version": "1.0",
            "timestamp": "2024-01-01T00:00:00",
            "provider": "claude",
            "raw_response": {},
        }
        mock_prompt_llm.return_value = mock_response

        args = argparse.Namespace(
            prompt="/discuss",
            output_format="session-id",
            timeout=30,
            llm_method="claude",
            session_id="existing-session-456",
            continue_session_from=None,
            continue_session=False,
            project_dir=None,
            mcp_config=None,
            settings=None,
        )

        result = execute_prompt(args)

        assert result == 0
        captured = capsys.readouterr()
        assert captured.out.strip() == "existing-session-456"
        # Verify session_id was passed to prompt_llm
        call_kwargs = mock_prompt_llm.call_args[1]
        assert call_kwargs["session_id"] == "existing-session-456"
