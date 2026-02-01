#!/usr/bin/env python3
"""Tests for Claude CLI IO wrappers and logging functionality."""

import json
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.llm.providers.claude.claude_code_cli import ask_claude_code_cli
from mcp_coder.utils.subprocess_runner import CommandResult


class TestIOWrappers:
    """Tests for I/O wrapper integration."""

    @patch("mcp_coder.llm.providers.claude.claude_code_cli._find_claude_executable")
    @patch("mcp_coder.llm.providers.claude.claude_code_cli.execute_subprocess")
    @patch("mcp_coder.llm.providers.claude.claude_code_cli.get_stream_log_path")
    def test_ask_claude_code_cli_returns_typed_dict(
        self,
        mock_get_path: MagicMock,
        mock_execute: MagicMock,
        mock_find: MagicMock,
        make_stream_json_output,
    ) -> None:
        """Test that CLI method returns complete LLMResponseDict."""
        mock_find.return_value = "claude"
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_get_path.return_value = Path(tmpdir) / "test.ndjson"
            mock_result = CommandResult(
                return_code=0,
                stdout=make_stream_json_output("Test response", "test-123"),
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

    @patch("mcp_coder.llm.providers.claude.claude_code_cli._find_claude_executable")
    @patch("mcp_coder.llm.providers.claude.claude_code_cli.execute_subprocess")
    @patch("mcp_coder.llm.providers.claude.claude_code_cli.get_stream_log_path")
    def test_ask_claude_code_cli_with_session_integration(
        self,
        mock_get_path: MagicMock,
        mock_execute: MagicMock,
        mock_find: MagicMock,
        make_stream_json_output,
    ) -> None:
        """Test session ID passthrough in full workflow."""
        mock_find.return_value = "claude"
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_get_path.return_value = Path(tmpdir) / "test.ndjson"
            mock_result = CommandResult(
                return_code=0,
                stdout=make_stream_json_output("Continued", "existing"),
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
            # Verify stdin was used
            options = call_args[0][1]
            assert options.input_data == "Follow up"


class TestCliLogging:
    """Tests for logging functionality in CLI method."""

    @patch("mcp_coder.llm.providers.claude.claude_code_cli._find_claude_executable")
    @patch("mcp_coder.llm.providers.claude.claude_code_cli.execute_subprocess")
    @patch("mcp_coder.llm.providers.claude.claude_code_cli.get_stream_log_path")
    @patch("mcp_coder.llm.providers.claude.claude_code_cli.log_llm_request")
    def test_cli_logs_request(
        self,
        mock_log_request: MagicMock,
        mock_get_path: MagicMock,
        mock_execute: MagicMock,
        mock_find: MagicMock,
        make_stream_json_output,
    ) -> None:
        """Test that request is logged before subprocess execution."""
        mock_find.return_value = "claude"
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_get_path.return_value = Path(tmpdir) / "test.ndjson"
            mock_result = CommandResult(
                return_code=0,
                stdout=make_stream_json_output(),
                stderr="",
                timed_out=False,
            )
            mock_execute.return_value = mock_result

            ask_claude_code_cli("Test question", session_id="abc-123", timeout=60)

            # Verify log_llm_request was called with correct parameters
            mock_log_request.assert_called_once()
            call_kwargs = mock_log_request.call_args[1]
            assert call_kwargs["method"] == "cli"
            assert call_kwargs["provider"] == "claude"
            assert call_kwargs["session_id"] == "abc-123"
            assert call_kwargs["prompt"] == "Test question"
            assert call_kwargs["timeout"] == 60
            assert "command" in call_kwargs

    @patch("mcp_coder.llm.providers.claude.claude_code_cli._find_claude_executable")
    @patch("mcp_coder.llm.providers.claude.claude_code_cli.execute_subprocess")
    @patch("mcp_coder.llm.providers.claude.claude_code_cli.get_stream_log_path")
    @patch("mcp_coder.llm.providers.claude.claude_code_cli.log_llm_response")
    def test_cli_logs_response(
        self,
        mock_log_response: MagicMock,
        mock_get_path: MagicMock,
        mock_execute: MagicMock,
        mock_find: MagicMock,
        make_stream_json_output,
    ) -> None:
        """Test that response with duration is logged after success."""
        mock_find.return_value = "claude"
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_get_path.return_value = Path(tmpdir) / "test.ndjson"
            mock_result = CommandResult(
                return_code=0,
                stdout=make_stream_json_output(),
                stderr="",
                timed_out=False,
            )
            mock_execute.return_value = mock_result

            ask_claude_code_cli("Test question")

            # Verify log_llm_response was called with duration and cost
            mock_log_response.assert_called_once()
            call_kwargs = mock_log_response.call_args[1]
            assert call_kwargs["method"] == "cli"
            assert "duration_ms" in call_kwargs
            assert isinstance(call_kwargs["duration_ms"], int)
            assert call_kwargs["duration_ms"] >= 0
            # Should also include cost from stream
            assert call_kwargs["cost_usd"] == 0.05

    @patch("mcp_coder.llm.providers.claude.claude_code_cli._find_claude_executable")
    @patch("mcp_coder.llm.providers.claude.claude_code_cli.execute_subprocess")
    @patch("mcp_coder.llm.providers.claude.claude_code_cli.get_stream_log_path")
    @patch("mcp_coder.llm.providers.claude.claude_code_cli.log_llm_error")
    def test_cli_logs_error_on_timeout(
        self,
        mock_log_error: MagicMock,
        mock_get_path: MagicMock,
        mock_execute: MagicMock,
        mock_find: MagicMock,
    ) -> None:
        """Test that timeout errors are logged with duration."""
        mock_find.return_value = "claude"
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_get_path.return_value = Path(tmpdir) / "test.ndjson"
            mock_result = CommandResult(
                return_code=1,
                stdout="",
                stderr="",
                timed_out=True,
                execution_error="Timed out",
            )
            mock_execute.return_value = mock_result

            with pytest.raises(subprocess.TimeoutExpired):
                ask_claude_code_cli("Test question", timeout=30)

            # Verify log_llm_error was called with error and duration
            mock_log_error.assert_called_once()
            call_kwargs = mock_log_error.call_args[1]
            assert call_kwargs["method"] == "cli"
            assert isinstance(call_kwargs["error"], subprocess.TimeoutExpired)
            assert "duration_ms" in call_kwargs
            assert isinstance(call_kwargs["duration_ms"], int)

    @patch("mcp_coder.llm.providers.claude.claude_code_cli._find_claude_executable")
    @patch("mcp_coder.llm.providers.claude.claude_code_cli.execute_subprocess")
    @patch("mcp_coder.llm.providers.claude.claude_code_cli.get_stream_log_path")
    @patch("mcp_coder.llm.providers.claude.claude_code_cli.log_llm_error")
    def test_cli_logs_error_on_failure(
        self,
        mock_log_error: MagicMock,
        mock_get_path: MagicMock,
        mock_execute: MagicMock,
        mock_find: MagicMock,
    ) -> None:
        """Test that command failures are logged."""
        mock_find.return_value = "claude"
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_get_path.return_value = Path(tmpdir) / "test.ndjson"
            mock_result = CommandResult(
                return_code=1,
                stdout="",
                stderr="Command failed",
                timed_out=False,
            )
            mock_execute.return_value = mock_result

            with pytest.raises(subprocess.CalledProcessError):
                ask_claude_code_cli("Test question")

            # Verify log_llm_error was called with CalledProcessError
            mock_log_error.assert_called_once()
            call_kwargs = mock_log_error.call_args[1]
            assert call_kwargs["method"] == "cli"
            assert isinstance(call_kwargs["error"], subprocess.CalledProcessError)
            assert "duration_ms" in call_kwargs
