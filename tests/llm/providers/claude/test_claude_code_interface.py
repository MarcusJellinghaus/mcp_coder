#!/usr/bin/env python3
"""Tests for claude_code_interface module."""

from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.llm.providers.claude.claude_code_interface import ask_claude_code


class TestAskClaudeCodeSessionSupport:
    """Test ask_claude_code session ID support."""

    @patch("mcp_coder.llm.providers.claude.claude_code_interface.ask_claude_code_cli")
    def test_cli_with_session_id(self, mock_cli: MagicMock) -> None:
        """Test that session_id is passed through to CLI method."""
        mock_cli.return_value = {
            "text": "CLI response",
            "session_id": "cli-session-123",
            "version": "1.0",
            "timestamp": "2025-01-01T00:00:00Z",
            "method": "cli",
            "provider": "claude",
            "raw_response": {},
        }

        response = ask_claude_code("Test", method="cli", session_id="cli-session-123")

        assert response == "CLI response"
        mock_cli.assert_called_once_with(
            "Test", session_id="cli-session-123", timeout=30, env_vars=None, cwd=None, mcp_config=None
        )

    @patch("mcp_coder.llm.providers.claude.claude_code_interface.ask_claude_code_api")
    def test_api_with_session_id(self, mock_api: MagicMock) -> None:
        """Test that session_id is passed through to API method."""
        mock_api.return_value = {
            "text": "API response",
            "session_id": "api-session-456",
            "version": "1.0",
            "timestamp": "2025-01-01T00:00:00Z",
            "method": "api",
            "provider": "claude",
            "raw_response": {},
        }

        response = ask_claude_code("Test", method="api", session_id="api-session-456")

        assert response == "API response"
        mock_api.assert_called_once_with(
            "Test", session_id="api-session-456", timeout=30, env_vars=None, cwd=None, mcp_config=None
        )

    @patch("mcp_coder.llm.providers.claude.claude_code_interface.ask_claude_code_cli")
    def test_returns_text_only(self, mock_cli: MagicMock) -> None:
        """Test that function returns only text, not full dict."""
        mock_cli.return_value = {
            "text": "Just the text",
            "session_id": "test-123",
            "version": "1.0",
            "timestamp": "2025-01-01T00:00:00Z",
            "method": "cli",
            "provider": "claude",
            "raw_response": {"metadata": {"cost": 0.05}},
        }

        response = ask_claude_code("Test", method="cli")

        # Should return string, not dict
        assert isinstance(response, str)
        assert response == "Just the text"

    @patch("mcp_coder.llm.providers.claude.claude_code_interface.ask_claude_code_cli")
    def test_without_session_id(self, mock_cli: MagicMock) -> None:
        """Test that session_id is optional."""
        mock_cli.return_value = {
            "text": "Response without session",
            "session_id": "auto-generated",
            "version": "1.0",
            "timestamp": "2025-01-01T00:00:00Z",
            "method": "cli",
            "provider": "claude",
            "raw_response": {},
        }

        # Should not raise - session_id is optional
        response = ask_claude_code("Test", method="cli")
        assert response == "Response without session"

    @patch("mcp_coder.llm.providers.claude.claude_code_interface.ask_claude_code_cli")
    def test_session_id_none_by_default(self, mock_cli: MagicMock) -> None:
        """Test that session_id defaults to None."""
        mock_cli.return_value = {
            "text": "Default behavior",
            "session_id": "new-session",
            "version": "1.0",
            "timestamp": "2025-01-01T00:00:00Z",
            "method": "cli",
            "provider": "claude",
            "raw_response": {},
        }

        response = ask_claude_code("Test", method="cli")

        # Should pass None as session_id to underlying function
        mock_cli.assert_called_once_with(
            "Test", session_id=None, timeout=30, env_vars=None, cwd=None, mcp_config=None
        )
        assert response == "Default behavior"

    @patch("mcp_coder.llm.providers.claude.claude_code_interface.ask_claude_code_api")
    def test_api_session_id_default_none(self, mock_api: MagicMock) -> None:
        """Test that API method also gets None by default."""
        mock_api.return_value = {
            "text": "API default",
            "session_id": None,
            "version": "1.0",
            "timestamp": "2025-01-01T00:00:00Z",
            "method": "api",
            "provider": "claude",
            "raw_response": {},
        }

        response = ask_claude_code("Test", method="api")

        mock_api.assert_called_once_with(
            "Test", session_id=None, timeout=30, env_vars=None, cwd=None
        )
        assert response == "API default"

    @patch("mcp_coder.llm.providers.claude.claude_code_interface.ask_claude_code_cli")
    def test_timeout_parameter_passthrough(self, mock_cli: MagicMock) -> None:
        """Test that timeout parameter is passed through."""
        mock_cli.return_value = {
            "text": "Response",
            "session_id": None,
            "version": "1.0",
            "timestamp": "2025-01-01T00:00:00Z",
            "method": "cli",
            "provider": "claude",
            "raw_response": {},
        }

        ask_claude_code("Test", method="cli", timeout=60)

        mock_cli.assert_called_once_with(
            "Test", session_id=None, timeout=60, env_vars=None, cwd=None
        )

    @patch("mcp_coder.llm.providers.claude.claude_code_interface.ask_claude_code_cli")
    def test_cli_with_env_vars(self, mock_cli: MagicMock) -> None:
        """Test that env_vars is passed through to CLI method."""
        test_env_vars = {"VAR1": "value1", "VAR2": "value2"}
        mock_cli.return_value = {
            "text": "CLI response with env vars",
            "session_id": "env-test",
            "version": "1.0",
            "timestamp": "2025-01-01T00:00:00Z",
            "method": "cli",
            "provider": "claude",
            "raw_response": {},
        }

        response = ask_claude_code("Test", method="cli", env_vars=test_env_vars)

        assert response == "CLI response with env vars"
        mock_cli.assert_called_once_with(
            "Test", session_id=None, timeout=30, env_vars=test_env_vars, cwd=None
        )


class TestAskClaudeCodeValidation:
    """Test input validation for ask_claude_code."""

    @patch("mcp_coder.llm.providers.claude.claude_code_interface.ask_claude_code_cli")
    def test_empty_question_raises_error(self, mock_cli: MagicMock) -> None:
        """Test that empty question raises ValueError."""
        with pytest.raises(ValueError, match="Question cannot be empty"):
            ask_claude_code("")

        mock_cli.assert_not_called()

    @patch("mcp_coder.llm.providers.claude.claude_code_interface.ask_claude_code_cli")
    def test_whitespace_only_question_raises_error(self, mock_cli: MagicMock) -> None:
        """Test that whitespace-only question raises ValueError."""
        with pytest.raises(ValueError, match="Question cannot be empty"):
            ask_claude_code("   \n  ")

        mock_cli.assert_not_called()

    @patch("mcp_coder.llm.providers.claude.claude_code_interface.ask_claude_code_cli")
    def test_invalid_timeout_raises_error(self, mock_cli: MagicMock) -> None:
        """Test that invalid timeout raises ValueError."""
        with pytest.raises(ValueError, match="Timeout must be a positive number"):
            ask_claude_code("Test", timeout=0)

        with pytest.raises(ValueError, match="Timeout must be a positive number"):
            ask_claude_code("Test", timeout=-1)

        mock_cli.assert_not_called()

    def test_invalid_method_raises_error(self) -> None:
        """Test that invalid method raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported method"):
            ask_claude_code("Test", method="invalid")


class TestAskClaudeCodeBackwardCompatibility:
    """Test backward compatibility of ask_claude_code."""

    @patch("mcp_coder.llm.providers.claude.claude_code_interface.ask_claude_code_cli")
    def test_existing_code_still_works(self, mock_cli: MagicMock) -> None:
        """Test that existing code without session_id still works."""
        mock_cli.return_value = {
            "text": "Legacy response",
            "session_id": "new-123",
            "version": "1.0",
            "timestamp": "2025-01-01T00:00:00Z",
            "method": "cli",
            "provider": "claude",
            "raw_response": {},
        }

        # Old-style call without session_id parameter
        response = ask_claude_code("Test question")

        assert response == "Legacy response"
        assert isinstance(response, str)

    @patch("mcp_coder.llm.providers.claude.claude_code_interface.ask_claude_code_api")
    def test_api_method_still_works(self, mock_api: MagicMock) -> None:
        """Test that API method works without session_id."""
        mock_api.return_value = {
            "text": "API legacy",
            "session_id": None,
            "version": "1.0",
            "timestamp": "2025-01-01T00:00:00Z",
            "method": "api",
            "provider": "claude",
            "raw_response": {},
        }

        response = ask_claude_code("Test", method="api")

        assert response == "API legacy"
        assert isinstance(response, str)
