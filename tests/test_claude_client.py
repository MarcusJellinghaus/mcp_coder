#!/usr/bin/env python3
"""Unit tests for claude_client module."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.claude_client import ask_claude


class TestClaudeClient:
    """Test cases for Claude client functions."""

    @patch("mcp_coder.claude_client._find_claude_executable")
    @patch("subprocess.run")
    def test_ask_claude_success(self, mock_run: MagicMock, mock_find: MagicMock) -> None:
        """Test successful Claude question."""
        mock_find.return_value = "claude"
        mock_result = MagicMock()
        mock_result.stdout = "The answer is 42\n"
        mock_run.return_value = mock_result

        response = ask_claude("What is the meaning of life?")

        assert response == "The answer is 42"
        mock_run.assert_called_once_with(
            ["claude", "--print", "What is the meaning of life?"],
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        )

    @patch("mcp_coder.claude_client._find_claude_executable")
    @patch("subprocess.run")
    def test_ask_claude_with_custom_timeout(self, mock_run: MagicMock, mock_find: MagicMock) -> None:
        """Test Claude question with custom timeout."""
        mock_find.return_value = "claude"
        mock_result = MagicMock()
        mock_result.stdout = "Response\n"
        mock_run.return_value = mock_result

        ask_claude("Test question", timeout=60)

        mock_run.assert_called_once_with(
            ["claude", "--print", "Test question"],
            capture_output=True,
            text=True,
            timeout=60,
            check=True,
        )

    @patch("mcp_coder.claude_client._find_claude_executable")
    def test_ask_claude_file_not_found(self, mock_find: MagicMock) -> None:
        """Test Claude CLI not found error."""
        mock_find.side_effect = FileNotFoundError("Claude Code CLI not found. Please ensure it's installed and accessible.")

        with pytest.raises(FileNotFoundError, match="Claude Code CLI not found"):
            ask_claude("Test question")

    @patch("subprocess.run")
    def test_ask_claude_timeout(self, mock_run: MagicMock) -> None:
        """Test Claude command timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired("claude", 30)

        with pytest.raises(
            subprocess.TimeoutExpired, match="timed out after 30 seconds"
        ):
            ask_claude("Test question")

    @patch("subprocess.run")
    def test_ask_claude_command_error(self, mock_run: MagicMock) -> None:
        """Test Claude command failure."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "claude", stderr="Command failed"
        )

        with pytest.raises(subprocess.CalledProcessError):
            ask_claude("Test question")

