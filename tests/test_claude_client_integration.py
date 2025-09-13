#!/usr/bin/env python3
"""Integration tests for claude_client module with mocked CLI calls."""

import subprocess
from unittest.mock import Mock, patch

import pytest

from mcp_coder.claude_client import ask_claude, _find_claude_executable


class TestClaudeClientIntegration:
    """Integration test cases with mocked Claude Code CLI."""

    @patch("mcp_coder.claude_client._find_claude_executable")
    @patch("subprocess.run")
    def test_ask_claude_simple_math_exact(self, mock_run: Mock, mock_find: Mock) -> None:
        """Test asking Claude a simple math question with mocked response."""
        # Mock finding the executable
        mock_find.return_value = "claude"

        # Mock successful subprocess call
        mock_result = Mock()
        mock_result.stdout = "4"
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        response = ask_claude("What is 2 + 2? Please provide the shortest possible answer.")

        # Verify the response
        assert response == "4"
        # Verify subprocess was called correctly
        mock_run.assert_called_once_with(
            ["claude", "--print", "What is 2 + 2? Please provide the shortest possible answer."],
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        )

    @patch("mcp_coder.claude_client._find_claude_executable")
    @patch("subprocess.run")
    def test_ask_claude_timeout_handling(self, mock_run: Mock, mock_find: Mock) -> None:
        """Test that timeout parameter works with mocked response."""
        # Mock finding the executable
        mock_find.return_value = "claude"

        # Mock successful subprocess call
        mock_result = Mock()
        mock_result.stdout = "Hello! How can I help you?"
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        response = ask_claude("Hello", timeout=20)

        assert len(response) > 0
        assert isinstance(response, str)
        # Verify timeout was passed correctly
        mock_run.assert_called_once_with(
            ["claude", "--print", "Hello"],
            capture_output=True,
            text=True,
            timeout=20,
            check=True,
        )

    @patch("mcp_coder.claude_client._find_claude_executable")
    @patch("subprocess.run")
    def test_ask_claude_timeout_expired(self, mock_run: Mock, mock_find: Mock) -> None:
        """Test timeout exception handling."""
        # Mock finding the executable
        mock_find.return_value = "claude"

        # Mock timeout exception
        mock_run.side_effect = subprocess.TimeoutExpired(
            ["claude", "--print", "Hello"], 30
        )

        with pytest.raises(subprocess.TimeoutExpired, match="Command.*timed out after 30 seconds"):
            ask_claude("Hello", timeout=30)

    def test_ask_claude_cli_not_found(self) -> None:
        """Test error handling when Claude CLI is not found."""
        with patch("mcp_coder.claude_client._find_claude_executable") as mock_find:
            mock_find.side_effect = FileNotFoundError("Claude Code CLI not found. Please ensure it's installed and accessible.")

            with pytest.raises(FileNotFoundError, match="Claude Code CLI not found"):
                ask_claude("Test question")