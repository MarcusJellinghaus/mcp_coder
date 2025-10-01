#!/usr/bin/env python3
"""Unit tests for claude_code_cli module."""

import json
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.llm_providers.claude.claude_code_cli import (
    ask_claude_code_cli,
    build_cli_command,
    create_response_dict,
    parse_cli_json_string,
)
from mcp_coder.llm_types import LLMResponseDict
from mcp_coder.utils.subprocess_runner import CommandResult


class TestClaudeCodeCliBackwardCompatibility:
    """Test cases for backward compatibility of CLI functions."""

    @patch("mcp_coder.llm_providers.claude.claude_code_cli._find_claude_executable")
    @patch("mcp_coder.llm_providers.claude.claude_code_cli.execute_command")
    def test_ask_claude_code_cli_success(
        self, mock_execute: MagicMock, mock_find: MagicMock
    ) -> None:
        """Test successful Claude question returns dict with text."""
        mock_find.return_value = "claude"
        mock_result = CommandResult(
            return_code=0,
            stdout=json.dumps({"result": "The answer is 42", "session_id": "test"}),
            stderr="",
            timed_out=False,
        )
        mock_execute.return_value = mock_result

        response = ask_claude_code_cli("What is the meaning of life?")

        assert response["text"] == "The answer is 42"
        call_args = mock_execute.call_args
        command = call_args[0][0]
        assert "--output-format" in command
        assert "json" in command

    @patch("mcp_coder.llm_providers.claude.claude_code_cli._find_claude_executable")
    @patch("mcp_coder.llm_providers.claude.claude_code_cli.execute_command")
    def test_ask_claude_code_cli_with_custom_timeout(
        self, mock_execute: MagicMock, mock_find: MagicMock
    ) -> None:
        """Test Claude question with custom timeout."""
        mock_find.return_value = "claude"
        mock_result = CommandResult(
            return_code=0,
            stdout=json.dumps({"result": "Response"}),
            stderr="",
            timed_out=False,
        )
        mock_execute.return_value = mock_result

        ask_claude_code_cli("Test question", timeout=60)

        call_args = mock_execute.call_args
        assert call_args[1]["timeout_seconds"] == 60

    @patch("mcp_coder.llm_providers.claude.claude_code_cli._find_claude_executable")
    def test_ask_claude_code_cli_file_not_found(self, mock_find: MagicMock) -> None:
        """Test Claude CLI not found error."""
        mock_find.side_effect = FileNotFoundError(
            "Claude Code CLI not found. Please ensure it's installed and accessible."
        )

        with pytest.raises(FileNotFoundError, match="Claude Code CLI not found"):
            ask_claude_code_cli("Test question")

    @patch("mcp_coder.llm_providers.claude.claude_code_cli._find_claude_executable")
    @patch("mcp_coder.llm_providers.claude.claude_code_cli.execute_command")
    def test_ask_claude_code_cli_timeout(
        self, mock_execute: MagicMock, mock_find: MagicMock
    ) -> None:
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
            ask_claude_code_cli("Test question")

    @patch("mcp_coder.llm_providers.claude.claude_code_cli._find_claude_executable")
    @patch("mcp_coder.llm_providers.claude.claude_code_cli.execute_command")
    def test_ask_claude_code_cli_command_error(
        self, mock_execute: MagicMock, mock_find: MagicMock
    ) -> None:
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
            ask_claude_code_cli("Test question")


class TestPureFunctions:
    """Tests for pure functions (fast, no I/O)."""

    def test_parse_cli_json_string_basic(self) -> None:
        """Test parsing basic CLI JSON with real structure."""
        json_str = json.dumps({"result": "Test response", "session_id": "abc-123"})

        result = parse_cli_json_string(json_str)

        assert result["text"] == "Test response"
        assert result["session_id"] == "abc-123"
        assert result["raw_response"]["result"] == "Test response"

    def test_parse_cli_json_string_missing_session_id(self) -> None:
        """Test parsing when session_id is missing."""
        json_str = json.dumps({"result": "Response without session"})

        result = parse_cli_json_string(json_str)

        assert result["text"] == "Response without session"
        assert result["session_id"] is None

    def test_parse_cli_json_string_invalid_json(self) -> None:
        """Test error handling for invalid JSON."""
        invalid_json = "not valid json {{"

        with pytest.raises(ValueError, match="Failed to parse CLI JSON"):
            parse_cli_json_string(invalid_json)

    def test_build_cli_command_without_session(self) -> None:
        """Test command building without session ID."""
        cmd = build_cli_command("test question", None, "claude")

        assert cmd == ["claude", "--print", "--output-format", "json", "test question"]
        assert "--resume" not in cmd

    def test_build_cli_command_with_session(self) -> None:
        """Test command building with session ID."""
        cmd = build_cli_command("follow up", "session-123", "claude")

        assert "--resume" in cmd
        assert "session-123" in cmd
        assert cmd[-1] == "follow up"

    def test_create_response_dict_structure(self) -> None:
        """Test response dict creation."""
        result = create_response_dict(
            "Hello", "abc-123", {"result": "Hello", "session_id": "abc-123"}
        )

        assert result["text"] == "Hello"
        assert result["session_id"] == "abc-123"
        assert result["method"] == "cli"
        assert result["provider"] == "claude"
        assert "version" in result
        assert "timestamp" in result


class TestIOWrappers:
    """Tests for I/O wrapper integration."""

    @patch("mcp_coder.llm_providers.claude.claude_code_cli._find_claude_executable")
    @patch("mcp_coder.llm_providers.claude.claude_code_cli.execute_command")
    def test_ask_claude_code_cli_returns_typed_dict(
        self, mock_execute: MagicMock, mock_find: MagicMock
    ) -> None:
        """Test that CLI method returns complete LLMResponseDict."""
        mock_find.return_value = "claude"
        mock_result = CommandResult(
            return_code=0,
            stdout=json.dumps({"result": "Test response", "session_id": "test-123"}),
            stderr="",
            timed_out=False,
        )
        mock_execute.return_value = mock_result

        result = ask_claude_code_cli("Test question")

        # Check all required fields present
        assert isinstance(result, dict)
        for field in [
            "version",
            "timestamp",
            "text",
            "session_id",
            "method",
            "provider",
            "raw_response",
        ]:
            assert field in result
        assert result["text"] == "Test response"
        assert result["session_id"] == "test-123"

    @patch("mcp_coder.llm_providers.claude.claude_code_cli._find_claude_executable")
    @patch("mcp_coder.llm_providers.claude.claude_code_cli.execute_command")
    def test_ask_claude_code_cli_with_session_integration(
        self, mock_execute: MagicMock, mock_find: MagicMock
    ) -> None:
        """Test session ID passthrough in full workflow."""
        mock_find.return_value = "claude"
        mock_result = CommandResult(
            return_code=0,
            stdout=json.dumps({"result": "Continued", "session_id": "existing"}),
            stderr="",
            timed_out=False,
        )
        mock_execute.return_value = mock_result

        result = ask_claude_code_cli("Follow up", session_id="existing")

        # Verify --resume flag was used
        call_args = mock_execute.call_args
        command = call_args[0][0]
        assert "--resume" in command
        assert "existing" in command
        assert result["session_id"] == "existing"
