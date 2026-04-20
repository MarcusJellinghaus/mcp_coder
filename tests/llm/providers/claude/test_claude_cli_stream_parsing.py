#!/usr/bin/env python3
"""Tests for Claude CLI stream-json parsing functions."""

import json
import tempfile
from pathlib import Path
from typing import cast
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.llm.providers.claude.claude_code_cli import (
    ParsedStreamResponse,
    StreamMessage,
    ask_claude_code_cli,
    create_response_dict_from_stream,
    parse_stream_json_file,
    parse_stream_json_line,
    parse_stream_json_string,
)
from mcp_coder.llm.providers.claude.claude_code_cli_log_paths import (
    get_stream_log_path,
    sanitize_branch_identifier,
)
from mcp_coder.llm.providers.claude.claude_code_cli_streaming import (
    ask_claude_code_cli_stream,
)
from mcp_coder.utils.subprocess_runner import CalledProcessError, CommandResult

from .conftest import StreamJsonFactory


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

    def test_parse_stream_json_string_full(
        self, make_stream_json_output: StreamJsonFactory
    ) -> None:
        """Test parsing complete stream-json output."""
        content = make_stream_json_output("Hello world", "sess-123")
        result = parse_stream_json_string(content)

        assert result["text"] == "Hello world"
        assert result["session_id"] == "sess-123"
        assert len(result["messages"]) == 3
        assert result["system_message"] is not None
        assert result["result_message"] is not None

    def test_parse_stream_json_string_extracts_cost(
        self, make_stream_json_output: StreamJsonFactory
    ) -> None:
        """Test that cost and usage are extracted from result message."""
        content = make_stream_json_output()
        result = parse_stream_json_string(content)

        assert result["result_message"] is not None
        assert result["result_message"]["total_cost_usd"] == 0.05
        assert result["result_message"]["duration_ms"] == 1500

    def test_parse_stream_json_file(
        self, make_stream_json_output: StreamJsonFactory
    ) -> None:
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
        assert result["provider"] == "claude"
        assert result["raw_response"]["stream_file"] == "/path/to/file.ndjson"
        assert result["raw_response"]["duration_ms"] == 1000
        assert result["raw_response"]["total_cost_usd"] == 0.05


# ──────────────────────────────────────────────────────────────────────
# Streaming error event tests (mocked subprocess)
# ──────────────────────────────────────────────────────────────────────


def _make_mock_stream(
    lines: list[str],
    *,
    timed_out: bool = False,
    return_code: int = 0,
    stderr: str = "",
) -> MagicMock:
    """Create a mock stream_subprocess return value."""
    mock_stream = MagicMock()
    mock_stream.__iter__ = lambda self: iter(lines)
    mock_stream.result = CommandResult(
        return_code=return_code,
        stdout="",
        stderr=stderr,
        timed_out=timed_out,
    )
    return mock_stream


class TestStreamErrorEventIncludesStderr:
    """Tests for stderr inclusion in streaming error events."""

    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming._find_claude_executable",
        return_value="claude",
    )
    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming.get_stream_log_path",
    )
    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming.stream_subprocess",
    )
    def test_stream_error_event_includes_stderr(
        self,
        mock_stream_sub: MagicMock,
        mock_log_path: MagicMock,
        _mock_find: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Error event message contains stderr when CLI fails."""
        mock_log_path.return_value = tmp_path / "stream.ndjson"
        mock_stream_sub.return_value = _make_mock_stream(
            [], return_code=1, stderr="auth failed"
        )

        events = list(ask_claude_code_cli_stream("test question"))
        error_events = [e for e in events if e.get("type") == "error"]
        assert len(error_events) == 1
        msg = str(error_events[0]["message"])
        assert "CLI failed with code 1" in msg
        assert "auth failed" in msg

    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming._find_claude_executable",
        return_value="claude",
    )
    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming.get_stream_log_path",
    )
    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming.stream_subprocess",
    )
    def test_stream_error_event_without_stderr(
        self,
        mock_stream_sub: MagicMock,
        mock_log_path: MagicMock,
        _mock_find: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Error event message has no trailing colon when stderr is empty."""
        mock_log_path.return_value = tmp_path / "stream.ndjson"
        mock_stream_sub.return_value = _make_mock_stream([], return_code=1, stderr="")

        events = list(ask_claude_code_cli_stream("test question"))
        error_events = [e for e in events if e.get("type") == "error"]
        assert len(error_events) == 1
        assert str(error_events[0]["message"]) == "CLI failed with code 1"

    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming._find_claude_executable",
        return_value="claude",
    )
    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming.get_stream_log_path",
    )
    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming.stream_subprocess",
    )
    def test_stream_error_event_truncates_long_stderr(
        self,
        mock_stream_sub: MagicMock,
        mock_log_path: MagicMock,
        _mock_find: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Error event message truncates stderr to 500 chars."""
        mock_log_path.return_value = tmp_path / "stream.ndjson"
        long_stderr = "x" * 1000
        mock_stream_sub.return_value = _make_mock_stream(
            [], return_code=1, stderr=long_stderr
        )

        events = list(ask_claude_code_cli_stream("test question"))
        error_events = [e for e in events if e.get("type") == "error"]
        assert len(error_events) == 1
        msg = str(error_events[0]["message"])
        assert "CLI failed with code 1" in msg
        # The stderr portion should be at most 500 chars
        stderr_part = msg.split(": ", 1)[1]
        assert len(stderr_part) == 500


class TestStreamFileWriting:
    """Tests for stream file writing functionality."""

    @patch("mcp_coder.llm.providers.claude.claude_code_cli._find_claude_executable")
    @patch("mcp_coder.llm.providers.claude.claude_code_cli.execute_subprocess")
    def test_stream_output_written_to_file(
        self,
        mock_execute: MagicMock,
        mock_find: MagicMock,
        make_stream_json_output: StreamJsonFactory,
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
            with pytest.raises(CalledProcessError) as exc_info:
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
