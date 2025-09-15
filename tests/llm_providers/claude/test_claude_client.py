#!/usr/bin/env python3
"""Unit tests for claude_client module - simple wrapper tests."""

from unittest.mock import MagicMock, patch

from mcp_coder.llm_providers.claude.claude_client import ask_claude


class TestClaudeClient:
    """Test cases for Claude client wrapper function."""

    @patch("mcp_coder.llm_providers.claude.claude_client.ask_claude_code_cli")
    def test_ask_claude_delegates_to_cli(self, mock_cli: MagicMock) -> None:
        """Test that ask_claude delegates to ask_claude_code_cli."""
        mock_cli.return_value = "test response"

        result = ask_claude("test question")

        assert result == "test response"
        mock_cli.assert_called_once_with("test question", 30)

    @patch("mcp_coder.llm_providers.claude.claude_client.ask_claude_code_cli")
    def test_ask_claude_passes_timeout(self, mock_cli: MagicMock) -> None:
        """Test that ask_claude passes timeout parameter."""
        mock_cli.return_value = "response"

        ask_claude("question", timeout=60)

        mock_cli.assert_called_once_with("question", 60)
