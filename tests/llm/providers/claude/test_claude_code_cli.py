#!/usr/bin/env python3
"""Unit tests for claude_code_cli module - core CLI functionality."""

import json
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
from mcp_coder.utils.subprocess_runner import CalledProcessError, TimeoutExpired

from .conftest import StreamJsonFactory, _make_stream_gen


class TestClaudeCodeCliBackwardCompatibility:
    """Test cases for the drain-wrapper over the streaming core.

    ``ask_claude_code_cli`` now iterates ``ask_claude_code_cli_stream`` to
    completion, so these tests drive the real streaming function with its
    subprocess internals mocked.
    """

    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming._find_claude_executable"
    )
    @patch("mcp_coder.llm.providers.claude.claude_code_cli_streaming.stream_subprocess")
    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming.get_stream_log_path"
    )
    def test_ask_claude_code_cli_success(
        self,
        mock_get_path: MagicMock,
        mock_stream: MagicMock,
        mock_find: MagicMock,
        make_stream_json_output: StreamJsonFactory,
    ) -> None:
        """Test successful Claude question returns dict with text."""
        mock_find.return_value = "claude"
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_get_path.return_value = Path(tmpdir) / "test.ndjson"
            mock_stream.return_value = _make_stream_gen(
                make_stream_json_output("The answer is 42", "test-sess").split("\n")
            )

            response = ask_claude_code_cli("What is the meaning of life?")

            assert response["text"] == "The answer is 42"
            assert response["session_id"] == "test-sess"
            # raw_response is the events shape (not messages)
            assert "events" in response["raw_response"]
            assert "messages" not in response["raw_response"]
            assert "stream_file" in response["raw_response"]
            call_args = mock_stream.call_args
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

    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming._find_claude_executable"
    )
    @patch("mcp_coder.llm.providers.claude.claude_code_cli_streaming.stream_subprocess")
    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming.get_stream_log_path"
    )
    def test_ask_claude_code_cli_with_custom_timeout(
        self,
        mock_get_path: MagicMock,
        mock_stream: MagicMock,
        mock_find: MagicMock,
        make_stream_json_output: StreamJsonFactory,
    ) -> None:
        """Test Claude question with custom timeout (now an inactivity budget)."""
        mock_find.return_value = "claude"
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_get_path.return_value = Path(tmpdir) / "test.ndjson"
            mock_stream.return_value = _make_stream_gen(
                make_stream_json_output().split("\n")
            )

            ask_claude_code_cli("Test question", timeout=60)

            # timeout is forwarded to the streaming core as an inactivity budget
            call_args = mock_stream.call_args
            assert call_args.kwargs["inactivity_timeout_seconds"] == 60

    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming._find_claude_executable"
    )
    @patch("mcp_coder.llm.providers.claude.claude_code_cli_streaming.stream_subprocess")
    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming.get_stream_log_path"
    )
    def test_ask_claude_code_cli_passes_settings_file(
        self,
        mock_get_path: MagicMock,
        mock_stream: MagicMock,
        mock_find: MagicMock,
        make_stream_json_output: StreamJsonFactory,
    ) -> None:
        """Verify ask_claude_code_cli forwards settings_file to build_cli_command."""
        mock_find.return_value = "claude"
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_get_path.return_value = Path(tmpdir) / "test.ndjson"
            mock_stream.return_value = _make_stream_gen(
                make_stream_json_output("ok", "sess-1").split("\n")
            )

            settings_path = "C:/path/.claude/settings.local.json"
            ask_claude_code_cli("Test question", settings_file=settings_path)

            call_args = mock_stream.call_args
            command = call_args[0][0]
            assert "--settings" in command
            assert settings_path in command
            idx = command.index("--settings")
            assert command[idx + 1] == settings_path

    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming._find_claude_executable"
    )
    def test_ask_claude_code_cli_file_not_found(self, mock_find: MagicMock) -> None:
        """Test Claude CLI not found error propagates from the streaming core."""
        mock_find.side_effect = FileNotFoundError(
            "Claude Code CLI not found. Please ensure it's installed and accessible."
        )

        with pytest.raises(FileNotFoundError, match="Claude Code CLI not found"):
            ask_claude_code_cli("Test question")

    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming._find_claude_executable"
    )
    @patch("mcp_coder.llm.providers.claude.claude_code_cli_streaming.stream_subprocess")
    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming.get_stream_log_path"
    )
    def test_ask_claude_code_cli_timeout(
        self,
        mock_get_path: MagicMock,
        mock_stream: MagicMock,
        mock_find: MagicMock,
    ) -> None:
        """Test inactivity timeout is raised as TimeoutExpired."""
        mock_find.return_value = "claude"
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_get_path.return_value = Path(tmpdir) / "test.ndjson"
            mock_stream.return_value = _make_stream_gen(
                [], return_code=1, timed_out=True
            )

            with pytest.raises(TimeoutExpired):
                ask_claude_code_cli("Test question")

    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming._find_claude_executable"
    )
    @patch("mcp_coder.llm.providers.claude.claude_code_cli_streaming.stream_subprocess")
    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming.get_stream_log_path"
    )
    def test_ask_claude_code_cli_command_error(
        self,
        mock_get_path: MagicMock,
        mock_stream: MagicMock,
        mock_find: MagicMock,
    ) -> None:
        """Test non-zero exit is raised as CalledProcessError."""
        mock_find.return_value = "claude"
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_get_path.return_value = Path(tmpdir) / "test.ndjson"
            mock_stream.return_value = _make_stream_gen([], return_code=1)

            with pytest.raises(CalledProcessError):
                ask_claude_code_cli("Test question")

    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming._find_claude_executable"
    )
    @patch("mcp_coder.llm.providers.claude.claude_code_cli_streaming.stream_subprocess")
    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming.get_stream_log_path"
    )
    def test_ask_claude_code_cli_error_includes_stream_file(
        self,
        mock_get_path: MagicMock,
        mock_stream: MagicMock,
        mock_find: MagicMock,
    ) -> None:
        """Test that CLI errors carry the stream file path for diagnosis."""
        mock_find.return_value = "claude"
        with tempfile.TemporaryDirectory() as tmpdir:
            stream_path = Path(tmpdir) / "test.ndjson"
            mock_get_path.return_value = stream_path
            mock_stream.return_value = _make_stream_gen([], return_code=1)

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
            "ToolSearch",
            "--verbose",
            "--input-format",
            "stream-json",
            "--replay-user-messages",
        ]
        assert "--resume" not in cmd

    def test_build_cli_command_with_stream_json_disabled(self) -> None:
        """Test command building with stream-json disabled."""
        cmd = build_cli_command(None, "claude", use_stream_json=False)

        assert cmd == [
            "claude",
            "-p",
            "",
            "--output-format",
            "json",
            "--tools",
            "ToolSearch",
        ]
        assert "--verbose" not in cmd  # verbose only needed for stream-json

    def test_build_cli_command_always_includes_tools_flag(self) -> None:
        """Test that --tools "ToolSearch" is always present regardless of options."""
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
            assert cmd[tools_idx + 1] == "ToolSearch"

    def test_build_cli_command_tools_is_toolsearch(self) -> None:
        """Test the value after --tools is exactly "ToolSearch" (MCP wait-bridge)."""
        cmd = build_cli_command(None, "claude")
        tools_idx = cmd.index("--tools")
        assert cmd[tools_idx + 1] == "ToolSearch"

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

    def test_build_cli_command_append_system_prompt(self) -> None:
        """Test --append-system-prompt flag is present with correct value."""
        cmd = build_cli_command(
            None, "claude", append_system_prompt="You are a helpful assistant."
        )

        assert "--append-system-prompt" in cmd
        idx = cmd.index("--append-system-prompt")
        assert cmd[idx + 1] == "You are a helpful assistant."
        assert "--system-prompt" not in cmd

    def test_build_cli_command_system_prompt_replace(self) -> None:
        """Test --system-prompt flag is present with correct value."""
        cmd = build_cli_command(None, "claude", system_prompt_replace="Replace prompt.")

        assert "--system-prompt" in cmd
        idx = cmd.index("--system-prompt")
        assert cmd[idx + 1] == "Replace prompt."
        assert "--append-system-prompt" not in cmd

    def test_build_cli_command_no_system_prompt(self) -> None:
        """Test neither flag is present when no system prompt given."""
        cmd = build_cli_command(None, "claude")

        assert "--append-system-prompt" not in cmd
        assert "--system-prompt" not in cmd

    def test_build_cli_command_both_prompts_raises(self) -> None:
        """Test ValueError if both append and replace provided."""
        with pytest.raises(ValueError, match="Cannot specify both"):
            build_cli_command(
                None,
                "claude",
                append_system_prompt="append",
                system_prompt_replace="replace",
            )

    def test_build_cli_command_with_settings_file(self) -> None:
        """Test --settings flag is present with the provided settings path."""
        settings_path = "C:/path/.claude/settings.local.json"
        cmd = build_cli_command(None, "claude", settings_file=settings_path)

        assert "--settings" in cmd
        assert settings_path in cmd
        idx = cmd.index("--settings")
        assert cmd[idx + 1] == settings_path

    def test_build_cli_command_without_settings_file(self) -> None:
        """Test --settings flag is NOT present when settings_file is omitted."""
        cmd = build_cli_command(None, "claude")

        assert "--settings" not in cmd


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
    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming._find_claude_executable"
    )
    @patch("mcp_coder.llm.providers.claude.claude_code_cli_streaming.stream_subprocess")
    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming.get_stream_log_path"
    )
    def test_session_id_passed_to_log_llm_response(
        self,
        mock_get_path: MagicMock,
        mock_stream: MagicMock,
        mock_find: MagicMock,
        mock_log_response: MagicMock,
        make_stream_json_output: StreamJsonFactory,
    ) -> None:
        """Test that session_id from stream response is passed to log_llm_response."""
        mock_find.return_value = "claude"
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_get_path.return_value = Path(tmpdir) / "test.ndjson"
            mock_stream.return_value = _make_stream_gen(
                make_stream_json_output("Test response", "cli-session-abc").split("\n")
            )

            ask_claude_code_cli("test question")

            mock_log_response.assert_called_once()
            _, kwargs = mock_log_response.call_args
            assert kwargs.get("session_id") == "cli-session-abc"
