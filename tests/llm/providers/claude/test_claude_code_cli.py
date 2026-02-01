#!/usr/bin/env python3
"""Unit tests for claude_code_cli module - core CLI functionality."""

import json
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.llm.providers.claude.claude_code_cli import (
    ask_claude_code_cli,
    build_cli_command,
    create_response_dict,
    format_stream_json_input,
    parse_cli_json_string,
)
from mcp_coder.utils.subprocess_runner import CommandResult

from .conftest import StreamJsonFactory


class TestClaudeCodeCliBackwardCompatibility:
    """Test cases for backward compatibility of CLI functions."""

    @patch("mcp_coder.llm.providers.claude.claude_code_cli._find_claude_executable")
    @patch("mcp_coder.llm.providers.claude.claude_code_cli.execute_subprocess")
    @patch("mcp_coder.llm.providers.claude.claude_code_cli.get_stream_log_path")
    def test_ask_claude_code_cli_success(
        self,
        mock_get_path: MagicMock,
        mock_execute: MagicMock,
        mock_find: MagicMock,
        make_stream_json_output: StreamJsonFactory,
    ) -> None:
        """Test successful Claude question returns dict with text."""
        mock_find.return_value = "claude"
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_get_path.return_value = Path(tmpdir) / "test.ndjson"
            mock_result = CommandResult(
                return_code=0,
                stdout=make_stream_json_output("The answer is 42", "test-sess"),
                stderr="",
                timed_out=False,
            )
            mock_execute.return_value = mock_result

            response = ask_claude_code_cli("What is the meaning of life?")

            assert response["text"] == "The answer is 42"
            call_args = mock_execute.call_args
            command = call_args[0][0]
            assert "--output-format" in command
            assert "stream-json" in command
            assert "--input-format" in command
            assert "--replay-user-messages" in command
            # Verify stdin was used with JSON-formatted input
            options = call_args[0][1]
            input_data = json.loads(options.input_data)
            assert input_data["type"] == "user"
            assert input_data["message"]["content"] == "What is the meaning of life?"

    @patch("mcp_coder.llm.providers.claude.claude_code_cli._find_claude_executable")
    @patch("mcp_coder.llm.providers.claude.claude_code_cli.execute_subprocess")
    @patch("mcp_coder.llm.providers.claude.claude_code_cli.get_stream_log_path")
    def test_ask_claude_code_cli_with_custom_timeout(
        self,
        mock_get_path: MagicMock,
        mock_execute: MagicMock,
        mock_find: MagicMock,
        make_stream_json_output: StreamJsonFactory,
    ) -> None:
        """Test Claude question with custom timeout."""
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

            ask_claude_code_cli("Test question", timeout=60)

            call_args = mock_execute.call_args
            options = call_args[0][1]
            assert options.timeout_seconds == 60

    @patch("mcp_coder.llm.providers.claude.claude_code_cli._find_claude_executable")
    def test_ask_claude_code_cli_file_not_found(self, mock_find: MagicMock) -> None:
        """Test Claude CLI not found error."""
        mock_find.side_effect = FileNotFoundError(
            "Claude Code CLI not found. Please ensure it's installed and accessible."
        )

        with pytest.raises(FileNotFoundError, match="Claude Code CLI not found"):
            ask_claude_code_cli("Test question")

    @patch("mcp_coder.llm.providers.claude.claude_code_cli._find_claude_executable")
    @patch("mcp_coder.llm.providers.claude.claude_code_cli.execute_subprocess")
    @patch("mcp_coder.llm.providers.claude.claude_code_cli.get_stream_log_path")
    def test_ask_claude_code_cli_timeout(
        self,
        mock_get_path: MagicMock,
        mock_execute: MagicMock,
        mock_find: MagicMock,
    ) -> None:
        """Test Claude command timeout."""
        mock_find.return_value = "claude"
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_get_path.return_value = Path(tmpdir) / "test.ndjson"
            mock_result = CommandResult(
                return_code=1,
                stdout="",
                stderr="",
                timed_out=True,
                execution_error="Process timed out after 30 seconds",
            )
            mock_execute.return_value = mock_result

            with pytest.raises(subprocess.TimeoutExpired):
                ask_claude_code_cli("Test question")

    @patch("mcp_coder.llm.providers.claude.claude_code_cli._find_claude_executable")
    @patch("mcp_coder.llm.providers.claude.claude_code_cli.execute_subprocess")
    @patch("mcp_coder.llm.providers.claude.claude_code_cli.get_stream_log_path")
    def test_ask_claude_code_cli_command_error(
        self,
        mock_get_path: MagicMock,
        mock_execute: MagicMock,
        mock_find: MagicMock,
    ) -> None:
        """Test Claude command failure."""
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

    @patch("mcp_coder.llm.providers.claude.claude_code_cli._find_claude_executable")
    @patch("mcp_coder.llm.providers.claude.claude_code_cli.execute_subprocess")
    @patch("mcp_coder.llm.providers.claude.claude_code_cli.get_stream_log_path")
    def test_ask_claude_code_cli_error_includes_stream_file(
        self,
        mock_get_path: MagicMock,
        mock_execute: MagicMock,
        mock_find: MagicMock,
        make_stream_json_output: StreamJsonFactory,
    ) -> None:
        """Test that CLI errors include stream file path for diagnosis."""
        mock_find.return_value = "claude"
        with tempfile.TemporaryDirectory() as tmpdir:
            stream_path = Path(tmpdir) / "test.ndjson"
            mock_get_path.return_value = stream_path
            mock_result = CommandResult(
                return_code=1,
                stdout=make_stream_json_output(is_error=True),
                stderr="Auth error",
                timed_out=False,
            )
            mock_execute.return_value = mock_result

            with pytest.raises(subprocess.CalledProcessError) as exc_info:
                ask_claude_code_cli("Test question")

            # Verify stream file path is in stderr
            assert str(stream_path) in str(exc_info.value.stderr)


class TestPureFunctions:
    """Tests for pure functions (fast, no I/O)."""

    def test_parse_cli_json_string_validates_session_id_type(self) -> None:
        """Test that parse_cli_json_string validates session_id is a string."""
        # session_id as int should raise error
        json_str = json.dumps({"result": "Test", "session_id": 123})

        with pytest.raises(ValueError, match="session_id must be string, got int"):
            parse_cli_json_string(json_str)

    def test_build_cli_command_validates_empty_claude_cmd(self) -> None:
        """Test that build_cli_command validates claude_cmd is not empty."""
        with pytest.raises(ValueError, match="claude_cmd cannot be empty"):
            build_cli_command(None, "")

        with pytest.raises(ValueError, match="claude_cmd cannot be empty"):
            build_cli_command(None, "   ")

    def test_build_cli_command_validates_empty_session_id(self) -> None:
        """Test that build_cli_command validates session_id is not empty string."""
        with pytest.raises(ValueError, match="session_id cannot be empty string"):
            build_cli_command("", "claude")

        with pytest.raises(ValueError, match="session_id cannot be empty string"):
            build_cli_command("   ", "claude")

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
        """Test command building without session ID uses stream-json with full logging."""
        cmd = build_cli_command(None, "claude")

        assert cmd == [
            "claude",
            "-p",
            "",
            "--output-format",
            "stream-json",
            "--verbose",
            "--input-format",
            "stream-json",
            "--replay-user-messages",
        ]
        assert "--resume" not in cmd

    def test_build_cli_command_with_stream_json_disabled(self) -> None:
        """Test command building with stream-json disabled."""
        cmd = build_cli_command(None, "claude", use_stream_json=False)

        assert cmd == ["claude", "-p", "", "--output-format", "json"]
        assert "--verbose" not in cmd  # verbose only needed for stream-json

    def test_build_cli_command_with_session(self) -> None:
        """Test command building with session ID (uses stdin)."""
        cmd = build_cli_command("session-123", "claude")

        assert "--resume" in cmd
        assert "session-123" in cmd
        # With stdin, question is not in command
        assert "-p" in cmd
        assert "" in cmd

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


class TestFormatStreamJsonInput:
    """Tests for format_stream_json_input function."""

    def test_format_stream_json_input_basic(self) -> None:
        """Test basic prompt formatting."""
        result = format_stream_json_input("What is 2+2?")
        parsed = json.loads(result)

        assert parsed["type"] == "user"
        assert parsed["message"]["role"] == "user"
        assert parsed["message"]["content"] == "What is 2+2?"

    def test_format_stream_json_input_with_special_characters(self) -> None:
        """Test prompt with special characters is properly escaped."""
        prompt = 'Say "hello" and use a backslash: \\'
        result = format_stream_json_input(prompt)
        parsed = json.loads(result)

        assert parsed["message"]["content"] == prompt

    def test_format_stream_json_input_with_newlines(self) -> None:
        """Test multi-line prompt."""
        prompt = "Line 1\nLine 2\nLine 3"
        result = format_stream_json_input(prompt)
        parsed = json.loads(result)

        assert parsed["message"]["content"] == prompt

    def test_format_stream_json_input_with_unicode(self) -> None:
        """Test prompt with unicode characters."""
        prompt = "Hello 世界 🌍"
        result = format_stream_json_input(prompt)
        parsed = json.loads(result)

        assert parsed["message"]["content"] == prompt


class TestEnvVarsParameter:
    """Tests for env_vars parameter support."""

    @patch("mcp_coder.llm.providers.claude.claude_code_cli._find_claude_executable")
    @patch("mcp_coder.llm.providers.claude.claude_code_cli.execute_subprocess")
    @patch("mcp_coder.llm.providers.claude.claude_code_cli.get_stream_log_path")
    def test_ask_claude_code_cli_with_env_vars(
        self,
        mock_get_path: MagicMock,
        mock_execute: MagicMock,
        mock_find: MagicMock,
        make_stream_json_output: StreamJsonFactory,
    ) -> None:
        """Test that env_vars are passed to subprocess."""
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

            env_vars = {"MCP_CODER_PROJECT_DIR": "/test/path"}
            result = ask_claude_code_cli("Test question", env_vars=env_vars)

            # Verify env_vars were passed to CommandOptions
            call_args = mock_execute.call_args
            options = call_args[0][1]
            assert options.env == env_vars
            assert result["text"] == "Test response"

    @patch("mcp_coder.llm.providers.claude.claude_code_cli._find_claude_executable")
    @patch("mcp_coder.llm.providers.claude.claude_code_cli.execute_subprocess")
    @patch("mcp_coder.llm.providers.claude.claude_code_cli.get_stream_log_path")
    def test_ask_claude_code_cli_without_env_vars(
        self,
        mock_get_path: MagicMock,
        mock_execute: MagicMock,
        mock_find: MagicMock,
        make_stream_json_output: StreamJsonFactory,
    ) -> None:
        """Test backward compatibility when env_vars is not provided."""
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

            result = ask_claude_code_cli("Test question")

            # Verify env is None when not provided
            call_args = mock_execute.call_args
            options = call_args[0][1]
            assert options.env is None
            assert result["text"] == "Test response"
