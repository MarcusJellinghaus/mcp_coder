#!/usr/bin/env python3
"""Unit tests for claude_code_cli module - core CLI functionality."""

import json
import tempfile
from collections.abc import Generator
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
from mcp_coder.llm.providers.claude.claude_code_cli_streaming import (
    ask_claude_code_cli_stream,
)
from mcp_coder.utils.subprocess_runner import (
    CalledProcessError,
    CommandResult,
    TimeoutExpired,
)

from .conftest import StreamJsonFactory


def _make_stream_gen(
    lines: list[str],
    return_code: int = 0,
    timed_out: bool = False,
) -> Generator[str, None, CommandResult]:
    """Create a generator mimicking stream_subprocess output."""
    for line in lines:
        yield line
    return CommandResult(
        return_code=return_code,
        stdout="",
        stderr="",
        timed_out=timed_out,
    )


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

            with pytest.raises(TimeoutExpired):
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

            with pytest.raises(CalledProcessError):
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

            with pytest.raises(CalledProcessError) as exc_info:
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
            "--tools",
            "",
            "--verbose",
            "--input-format",
            "stream-json",
            "--replay-user-messages",
        ]
        assert "--resume" not in cmd

    def test_build_cli_command_with_stream_json_disabled(self) -> None:
        """Test command building with stream-json disabled."""
        cmd = build_cli_command(None, "claude", use_stream_json=False)

        assert cmd == ["claude", "-p", "", "--output-format", "json", "--tools", ""]
        assert "--verbose" not in cmd  # verbose only needed for stream-json

    def test_build_cli_command_always_includes_tools_flag(self) -> None:
        """Test that --tools "" is always present regardless of options."""
        variants = [
            build_cli_command(None, "claude"),
            build_cli_command("session-1", "claude"),
            build_cli_command(None, "claude", use_stream_json=False),
            build_cli_command(None, "claude", mcp_config=".mcp.json"),
            build_cli_command(
                "session-1", "claude", mcp_config=".mcp.json", use_stream_json=False
            ),
        ]
        for cmd in variants:
            tools_idx = cmd.index("--tools")
            assert cmd[tools_idx + 1] == ""

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


class TestSessionIdPropagation:
    """Tests that session_id is threaded through to log_llm_response."""

    @patch("mcp_coder.llm.providers.claude.claude_code_cli.log_llm_response")
    @patch("mcp_coder.llm.providers.claude.claude_code_cli._find_claude_executable")
    @patch("mcp_coder.llm.providers.claude.claude_code_cli.execute_subprocess")
    @patch("mcp_coder.llm.providers.claude.claude_code_cli.get_stream_log_path")
    def test_session_id_passed_to_log_llm_response(
        self,
        mock_get_path: MagicMock,
        mock_execute: MagicMock,
        mock_find: MagicMock,
        mock_log_response: MagicMock,
        make_stream_json_output: StreamJsonFactory,
    ) -> None:
        """Test that session_id from stream response is passed to log_llm_response."""
        mock_find.return_value = "claude"
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_get_path.return_value = Path(tmpdir) / "test.ndjson"
            mock_result = CommandResult(
                return_code=0,
                stdout=make_stream_json_output("Test response", "cli-session-abc"),
                stderr="",
                timed_out=False,
            )
            mock_execute.return_value = mock_result

            ask_claude_code_cli("test question")

            mock_log_response.assert_called_once()
            _, kwargs = mock_log_response.call_args
            assert kwargs.get("session_id") == "cli-session-abc"


class TestAskClaudeCodeCliStream:
    """Tests for ask_claude_code_cli_stream function."""

    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming._find_claude_executable"
    )
    @patch("mcp_coder.llm.providers.claude.claude_code_cli_streaming.stream_subprocess")
    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming.get_stream_log_path"
    )
    def test_ask_claude_stream_yields_text_delta(
        self,
        mock_get_path: MagicMock,
        mock_stream: MagicMock,
        mock_find: MagicMock,
    ) -> None:
        """Test that assistant text content blocks produce text_delta events."""
        mock_find.return_value = "claude"
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_get_path.return_value = Path(tmpdir) / "test.ndjson"
            lines = [
                json.dumps(
                    {
                        "type": "assistant",
                        "message": {"content": [{"type": "text", "text": "Hello "}]},
                    }
                ),
                json.dumps(
                    {
                        "type": "assistant",
                        "message": {"content": [{"type": "text", "text": "world"}]},
                    }
                ),
                json.dumps(
                    {
                        "type": "result",
                        "session_id": "s1",
                        "usage": {"input_tokens": 10},
                        "total_cost_usd": 0.01,
                    }
                ),
            ]
            mock_stream.return_value = _make_stream_gen(lines)

            events = list(ask_claude_code_cli_stream("Hello"))
            text_deltas = [e for e in events if e["type"] == "text_delta"]

            assert len(text_deltas) == 2
            assert text_deltas[0]["text"] == "Hello "
            assert text_deltas[1]["text"] == "world"

    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming._find_claude_executable"
    )
    @patch("mcp_coder.llm.providers.claude.claude_code_cli_streaming.stream_subprocess")
    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming.get_stream_log_path"
    )
    def test_ask_claude_stream_yields_tool_events(
        self,
        mock_get_path: MagicMock,
        mock_stream: MagicMock,
        mock_find: MagicMock,
    ) -> None:
        """Test that tool_use and tool_result content blocks produce events."""
        mock_find.return_value = "claude"
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_get_path.return_value = Path(tmpdir) / "test.ndjson"
            lines = [
                json.dumps(
                    {
                        "type": "assistant",
                        "message": {
                            "content": [
                                {
                                    "type": "tool_use",
                                    "name": "Bash",
                                    "input": {"command": "ls"},
                                }
                            ]
                        },
                    }
                ),
                json.dumps(
                    {
                        "type": "assistant",
                        "message": {
                            "content": [
                                {
                                    "type": "tool_result",
                                    "name": "Bash",
                                    "content": "file.txt",
                                }
                            ]
                        },
                    }
                ),
                json.dumps({"type": "result", "session_id": "s1"}),
            ]
            mock_stream.return_value = _make_stream_gen(lines)

            events = list(ask_claude_code_cli_stream("list files"))
            tool_starts = [e for e in events if e["type"] == "tool_use_start"]
            tool_results = [e for e in events if e["type"] == "tool_result"]

            assert len(tool_starts) == 1
            assert tool_starts[0]["name"] == "Bash"
            assert tool_starts[0]["args"] == {"command": "ls"}
            assert len(tool_results) == 1
            assert tool_results[0]["name"] == "Bash"
            assert tool_results[0]["output"] == "file.txt"

    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming._find_claude_executable"
    )
    @patch("mcp_coder.llm.providers.claude.claude_code_cli_streaming.stream_subprocess")
    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming.get_stream_log_path"
    )
    def test_ask_claude_stream_yields_done(
        self,
        mock_get_path: MagicMock,
        mock_stream: MagicMock,
        mock_find: MagicMock,
    ) -> None:
        """Test that result message produces done event with metadata."""
        mock_find.return_value = "claude"
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_get_path.return_value = Path(tmpdir) / "test.ndjson"
            lines = [
                json.dumps(
                    {
                        "type": "result",
                        "session_id": "abc123",
                        "usage": {"input_tokens": 100, "output_tokens": 50},
                        "total_cost_usd": 0.05,
                    }
                ),
            ]
            mock_stream.return_value = _make_stream_gen(lines)

            events = list(ask_claude_code_cli_stream("Hello"))
            done_events = [e for e in events if e["type"] == "done"]

            assert len(done_events) == 1
            assert done_events[0]["session_id"] == "abc123"
            assert done_events[0]["usage"] == {
                "input_tokens": 100,
                "output_tokens": 50,
            }
            assert done_events[0]["cost_usd"] == 0.05

    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming._find_claude_executable"
    )
    @patch("mcp_coder.llm.providers.claude.claude_code_cli_streaming.stream_subprocess")
    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming.get_stream_log_path"
    )
    def test_ask_claude_stream_yields_raw_lines(
        self,
        mock_get_path: MagicMock,
        mock_stream: MagicMock,
        mock_find: MagicMock,
    ) -> None:
        """Test that every NDJSON line produces a raw_line event."""
        mock_find.return_value = "claude"
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_get_path.return_value = Path(tmpdir) / "test.ndjson"
            lines = [
                json.dumps({"type": "system", "session_id": "s1"}),
                json.dumps(
                    {
                        "type": "assistant",
                        "message": {"content": [{"type": "text", "text": "Hi"}]},
                    }
                ),
                json.dumps({"type": "result", "session_id": "s1"}),
            ]
            mock_stream.return_value = _make_stream_gen(lines)

            events = list(ask_claude_code_cli_stream("Hello"))
            raw_lines = [e for e in events if e["type"] == "raw_line"]

            assert len(raw_lines) == 3
            for raw_event, original_line in zip(raw_lines, lines):
                assert raw_event["line"] == original_line

    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming._find_claude_executable"
    )
    @patch("mcp_coder.llm.providers.claude.claude_code_cli_streaming.stream_subprocess")
    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming.get_stream_log_path"
    )
    def test_ask_claude_stream_writes_log_file(
        self,
        mock_get_path: MagicMock,
        mock_stream: MagicMock,
        mock_find: MagicMock,
    ) -> None:
        """Test that NDJSON lines are written to the log file."""
        mock_find.return_value = "claude"
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test.ndjson"
            mock_get_path.return_value = log_path
            lines = [
                json.dumps({"type": "system", "session_id": "s1"}),
                json.dumps({"type": "result", "session_id": "s1"}),
            ]
            mock_stream.return_value = _make_stream_gen(lines)

            # Consume all events
            list(ask_claude_code_cli_stream("Hello"))

            # Verify log file was written
            assert log_path.exists()
            content = log_path.read_text(encoding="utf-8")
            written_lines = content.strip().split("\n")
            assert written_lines == lines

    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming._find_claude_executable"
    )
    @patch("mcp_coder.llm.providers.claude.claude_code_cli_streaming.stream_subprocess")
    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming.get_stream_log_path"
    )
    def test_ask_claude_stream_timeout_yields_error(
        self,
        mock_get_path: MagicMock,
        mock_stream: MagicMock,
        mock_find: MagicMock,
    ) -> None:
        """Test that a timed-out stream yields an error event."""
        mock_find.return_value = "claude"
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_get_path.return_value = Path(tmpdir) / "test.ndjson"
            mock_stream.return_value = _make_stream_gen(
                [], return_code=1, timed_out=True
            )

            events = list(ask_claude_code_cli_stream("Hello", timeout=30))
            error_events = [e for e in events if e["type"] == "error"]

            assert any("Timed out" in str(e["message"]) for e in error_events)

    def test_ask_claude_stream_empty_question_raises(self) -> None:
        """Test that empty/whitespace question raises ValueError."""
        with pytest.raises(ValueError, match="empty"):
            list(ask_claude_code_cli_stream(""))
        with pytest.raises(ValueError, match="empty"):
            list(ask_claude_code_cli_stream("   "))

    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming._find_claude_executable"
    )
    @patch("mcp_coder.llm.providers.claude.claude_code_cli_streaming.stream_subprocess")
    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming.get_stream_log_path"
    )
    def test_ask_claude_stream_nonzero_exit_yields_error(
        self,
        mock_get_path: MagicMock,
        mock_stream: MagicMock,
        mock_find: MagicMock,
    ) -> None:
        """Test that a non-zero exit code yields an error event."""
        mock_find.return_value = "claude"
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_get_path.return_value = Path(tmpdir) / "test.ndjson"
            mock_stream.return_value = _make_stream_gen([], return_code=1)

            events = list(ask_claude_code_cli_stream("Hello"))
            error_events = [e for e in events if e["type"] == "error"]

            assert len(error_events) == 1
            assert "failed with code 1" in str(error_events[0]["message"])
