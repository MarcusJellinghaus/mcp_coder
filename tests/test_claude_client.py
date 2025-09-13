#!/usr/bin/env python3
"""Unit tests for claude_client module."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.claude_client import ask_claude
from mcp_coder.subprocess_runner import CommandResult


class TestClaudeClient:
    """Test cases for Claude client functions."""

    @patch("mcp_coder.claude_client._find_claude_executable")
    @patch("mcp_coder.claude_client.execute_command")
    def test_ask_claude_success(self, mock_execute: MagicMock, mock_find: MagicMock) -> None:
        """Test successful Claude question."""
        mock_find.return_value = "claude"
        mock_result = CommandResult(
            return_code=0,
            stdout="The answer is 42\n",
            stderr="",
            timed_out=False,
        )
        mock_execute.return_value = mock_result

        response = ask_claude("What is the meaning of life?")

        assert response == "The answer is 42"
        mock_execute.assert_called_once_with(
            ["claude", "--print", "What is the meaning of life?"],
            timeout_seconds=30,
        )

    @patch("mcp_coder.claude_client._find_claude_executable")
    @patch("mcp_coder.claude_client.execute_command")
    def test_ask_claude_with_custom_timeout(self, mock_execute: MagicMock, mock_find: MagicMock) -> None:
        """Test Claude question with custom timeout."""
        mock_find.return_value = "claude"
        mock_result = CommandResult(
            return_code=0,
            stdout="Response\n",
            stderr="",
            timed_out=False,
        )
        mock_execute.return_value = mock_result

        ask_claude("Test question", timeout=60)

        mock_execute.assert_called_once_with(
            ["claude", "--print", "Test question"],
            timeout_seconds=60,
        )

    @patch("mcp_coder.claude_client._find_claude_executable")
    def test_ask_claude_file_not_found(self, mock_find: MagicMock) -> None:
        """Test Claude CLI not found error."""
        mock_find.side_effect = FileNotFoundError("Claude Code CLI not found. Please ensure it's installed and accessible.")

        with pytest.raises(FileNotFoundError, match="Claude Code CLI not found"):
            ask_claude("Test question")

    @patch("mcp_coder.claude_client._find_claude_executable")
    @patch("mcp_coder.claude_client.execute_command")
    def test_ask_claude_timeout(self, mock_execute: MagicMock, mock_find: MagicMock) -> None:
        """Test Claude command timeout."""
        mock_find.return_value = "claude"
        mock_result = CommandResult(
            return_code=1,
            stdout="",
            stderr="",
            timed_out=True,
            execution_error="Process timed out after 30 seconds",
        )
        mock_execute.return_value = mock_result

        with pytest.raises(
            subprocess.TimeoutExpired, match="timed out after 30 seconds"
        ):
            ask_claude("Test question")

    @patch("mcp_coder.claude_client._find_claude_executable")
    @patch("mcp_coder.claude_client.execute_command")
    def test_ask_claude_command_error(self, mock_execute: MagicMock, mock_find: MagicMock) -> None:
        """Test Claude command failure."""
        mock_find.return_value = "claude"
        mock_result = CommandResult(
            return_code=1,
            stdout="",
            stderr="Command failed",
            timed_out=False,
        )
        mock_execute.return_value = mock_result

        with pytest.raises(subprocess.CalledProcessError):
            ask_claude("Test question")

