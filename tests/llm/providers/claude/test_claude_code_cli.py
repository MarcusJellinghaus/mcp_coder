#!/usr/bin/env python3
"""Unit tests for claude_code_cli module."""

import json
import subprocess
import tempfile
from pathlib import Path
from typing import cast
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.llm.providers.claude.claude_code_cli import (
    CLIError,
    ParsedStreamResponse,
    StreamMessage,
    ask_claude_code_cli,
    build_cli_command,
    create_response_dict,
    create_response_dict_from_stream,
    get_stream_log_path,
    parse_cli_json_string,
    parse_stream_json_file,
    parse_stream_json_line,
    parse_stream_json_string,
    sanitize_branch_identifier,
)
from mcp_coder.llm.types import LLMResponseDict
from mcp_coder.utils.subprocess_runner import CommandResult


def make_stream_json_output(
    result_text: str = "Test response",
    session_id: str = "test-session-123",
    is_error: bool = False,
) -> str:
    """Helper to create valid stream-json output for testing."""
    system_msg = json.dumps(
        {
            "type": "system",
            "subtype": "init",
            "session_id": session_id,
            "model": "claude-opus-4-5-20251101",
            "tools": ["Task", "Bash"],
        }
    )
    assistant_msg = json.dumps(
        {
            "type": "assistant",
            "message": {
                "content": [{"type": "text", "text": result_text}],
            },
            "session_id": session_id,
        }
    )
    result_msg = json.dumps(
        {
            "type": "result",
            "subtype": "success" if not is_error else "error",
            "is_error": is_error,
            "result": result_text,
            "session_id": session_id,
            "duration_ms": 1500,
            "total_cost_usd": 0.05,
            "usage": {"input_tokens": 100, "output_tokens": 50},
        }
    )
    return f"{system_msg}\n{assistant_msg}\n{result_msg}"


class TestStreamJsonParsing:
    """Tests for stream-json parsing functions."""

    def test_parse_stream_json_line_valid(self) -> None:
        """Test parsing a valid stream-json line."""
        line = json.dumps({"type": "system", "session_id": "abc"})
        result = parse_stream_json_line(line)
        assert result is not None
        assert result["type"] == "system"
        assert result["session_id"] == "abc"

    def test_parse_stream_json_line_empty(self) -> None:
        """Test parsing empty line returns None."""
        assert parse_stream_json_line("") is None
        assert parse_stream_json_line("   ") is None

    def test_parse_stream_json_line_invalid(self) -> None:
        """Test parsing invalid JSON returns None."""
        assert parse_stream_json_line("not json {") is None

    def test_parse_stream_json_string_full(self) -> None:
        """Test parsing complete stream-json output."""
        content = make_stream_json_output("Hello world", "sess-123")
        result = parse_stream_json_string(content)

        assert result["text"] == "Hello world"
        assert result["session_id"] == "sess-123"
        assert len(result["messages"]) == 3
        assert result["system_message"] is not None
        assert result["result_message"] is not None

    def test_parse_stream_json_string_extracts_cost(self) -> None:
        """Test that cost and usage are extracted from result message."""
        content = make_stream_json_output()
        result = parse_stream_json_string(content)

        assert result["result_message"] is not None
        assert result["result_message"]["total_cost_usd"] == 0.05
        assert result["result_message"]["duration_ms"] == 1500

    def test_parse_stream_json_file(self) -> None:
        """Test parsing stream-json from file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.ndjson"
            content = make_stream_json_output("File test", "file-sess")
            file_path.write_text(content, encoding="utf-8")

            result = parse_stream_json_file(file_path)

            assert result["text"] == "File test"
            assert result["session_id"] == "file-sess"

    def test_parse_stream_json_file_not_exists(self) -> None:
        """Test parsing non-existent file returns empty response."""
        result = parse_stream_json_file(Path("/nonexistent/file.ndjson"))
        assert result["text"] == ""
        assert result["session_id"] is None
        assert result["messages"] == []


class TestSanitizeBranchIdentifier:
    """Tests for sanitize_branch_identifier() function."""

    def test_extracts_issue_id_from_branch(self) -> None:
        """Test extraction of numeric issue ID from branch name."""
        result = sanitize_branch_identifier("123-feature-name")
        assert result == "123"

    def test_extracts_prefix_from_slash_branch(self) -> None:
        """Test extraction of prefix from branch with slash."""
        result = sanitize_branch_identifier("fix/improve-logging")
        assert result == "fix"

    def test_limits_to_ten_characters(self) -> None:
        """Test that identifier is limited to 10 characters."""
        result = sanitize_branch_identifier("verylongbranchname")
        assert len(result) <= 10
        assert result == "verylongbr"

    def test_sanitizes_special_characters(self) -> None:
        """Test that special characters are removed."""
        result = sanitize_branch_identifier("feat@#$%name")
        assert result == "featname"

    def test_returns_empty_for_none(self) -> None:
        """Test returns empty string when branch_name is None."""
        result = sanitize_branch_identifier(None)
        assert result == ""

    def test_returns_empty_for_detached_head(self) -> None:
        """Test returns empty string for detached HEAD."""
        result = sanitize_branch_identifier("HEAD")
        assert result == ""

    def test_returns_empty_for_empty_string(self) -> None:
        """Test returns empty string for empty input."""
        result = sanitize_branch_identifier("")
        assert result == ""
        result = sanitize_branch_identifier("   ")
        assert result == ""


class TestGetStreamLogPath:
    """Tests for stream log path generation."""

    def test_get_stream_log_path_default(self) -> None:
        """Test default path generation."""
        path = get_stream_log_path()
        assert "logs" in str(path)
        assert "claude-sessions" in str(path)
        assert path.suffix == ".ndjson"
        assert "session_" in path.name

    def test_get_stream_log_path_custom_logs_dir(self) -> None:
        """Test custom logs directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = get_stream_log_path(logs_dir=tmpdir)
            assert tmpdir in str(path)
            assert "claude-sessions" in str(path)

    def test_get_stream_log_path_with_cwd(self) -> None:
        """Test path generation with cwd."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = get_stream_log_path(cwd=tmpdir)
            assert tmpdir in str(path)


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
            # Verify stdin was used
            options = call_args[0][1]
            assert options.input_data == "What is the meaning of life?"

    @patch("mcp_coder.llm.providers.claude.claude_code_cli._find_claude_executable")
    @patch("mcp_coder.llm.providers.claude.claude_code_cli.execute_subprocess")
    @patch("mcp_coder.llm.providers.claude.claude_code_cli.get_stream_log_path")
    def test_ask_claude_code_cli_with_custom_timeout(
        self,
        mock_get_path: MagicMock,
        mock_execute: MagicMock,
        mock_find: MagicMock,
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
        """Test command building without session ID uses stream-json."""
        cmd = build_cli_command(None, "claude")

        assert cmd == [
            "claude",
            "-p",
            "",
            "--output-format",
            "stream-json",
            "--verbose",
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


class TestCreateResponseDictFromStream:
    """Tests for create_response_dict_from_stream."""

    def test_creates_valid_response(self) -> None:
        """Test creating response dict from parsed stream."""
        parsed = ParsedStreamResponse(
            text="Hello",
            session_id="abc-123",
            messages=[],
            result_message=cast(
                StreamMessage,
                {
                    "type": "result",
                    "duration_ms": 1000,
                    "total_cost_usd": 0.05,
                },
            ),
            system_message=cast(StreamMessage, {"type": "system"}),
        )

        result = create_response_dict_from_stream(parsed, "/path/to/file.ndjson")

        assert result["text"] == "Hello"
        assert result["session_id"] == "abc-123"
        assert result["method"] == "cli"
        assert result["provider"] == "claude"
        assert result["raw_response"]["stream_file"] == "/path/to/file.ndjson"
        assert result["raw_response"]["duration_ms"] == 1000
        assert result["raw_response"]["total_cost_usd"] == 0.05


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


class TestStreamFileWriting:
    """Tests for stream file writing functionality."""

    @patch("mcp_coder.llm.providers.claude.claude_code_cli._find_claude_executable")
    @patch("mcp_coder.llm.providers.claude.claude_code_cli.execute_subprocess")
    def test_stream_output_written_to_file(
        self,
        mock_execute: MagicMock,
        mock_find: MagicMock,
    ) -> None:
        """Test that stream output is written to log file."""
        mock_find.return_value = "claude"
        stream_content = make_stream_json_output("Test", "sess-123")
        mock_result = CommandResult(
            return_code=0,
            stdout=stream_content,
            stderr="",
            timed_out=False,
        )
        mock_execute.return_value = mock_result

        with tempfile.TemporaryDirectory() as tmpdir:
            result = ask_claude_code_cli("Test question", logs_dir=tmpdir)

            # Check that stream file was created
            stream_file = result["raw_response"].get("stream_file")
            assert stream_file is not None
            stream_file_path = Path(str(stream_file))
            assert stream_file_path.exists()

            # Verify content was written
            content = stream_file_path.read_text(encoding="utf-8")
            assert "sess-123" in content

    @patch("mcp_coder.llm.providers.claude.claude_code_cli._find_claude_executable")
    @patch("mcp_coder.llm.providers.claude.claude_code_cli.execute_subprocess")
    def test_stream_file_preserved_on_error(
        self,
        mock_execute: MagicMock,
        mock_find: MagicMock,
    ) -> None:
        """Test that stream file is preserved even when CLI fails."""
        mock_find.return_value = "claude"
        # Partial stream output before failure
        partial_content = json.dumps(
            {"type": "system", "session_id": "partial-sess", "model": "claude"}
        )
        mock_result = CommandResult(
            return_code=1,
            stdout=partial_content,
            stderr="Auth failed",
            timed_out=False,
        )
        mock_execute.return_value = mock_result

        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(subprocess.CalledProcessError) as exc_info:
                ask_claude_code_cli("Test question", logs_dir=tmpdir)

            # Stream file path should be in error stderr
            assert "ndjson" in str(exc_info.value.stderr)

            # Find and verify the stream file
            session_dir = Path(tmpdir) / "claude-sessions"
            stream_files = list(session_dir.glob("*.ndjson"))
            assert len(stream_files) == 1

            # Content should be written
            content = stream_files[0].read_text(encoding="utf-8")
            assert "partial-sess" in content
