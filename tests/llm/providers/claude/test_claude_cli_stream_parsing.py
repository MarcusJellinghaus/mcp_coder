#!/usr/bin/env python3
"""Tests for Claude CLI stream-json parsing functions."""

import json
import tempfile
from pathlib import Path
from typing import cast
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.llm.providers.claude.claude_code_cli import (
    MCP_UNAVAILABLE_MAX_RETRIES,
    McpServersUnavailableError,
    ParsedStreamResponse,
    StreamMessage,
    ask_claude_code_cli,
    create_response_dict_from_stream,
    find_unavailable_mcp_servers,
    mcp_failure_is_retryable,
    parse_stream_json_file,
    parse_stream_json_line,
    parse_stream_json_string,
)
from mcp_coder.llm.providers.claude.claude_code_cli_log_paths import (
    get_stream_log_path,
    sanitize_branch_identifier,
)
from mcp_coder.llm.providers.claude.claude_code_cli_streaming import (
    _map_stream_message_to_event,
    ask_claude_code_cli_stream,
)
from mcp_coder.llm.types import StreamEvent
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


class TestMapStreamMessageIsError:
    """Tests for is_error propagation in _map_stream_message_to_event()."""

    def test_tool_use_result_is_error_propagates(self) -> None:
        """tool_result block with is_error: True surfaces on the event."""
        msg = cast(
            StreamMessage,
            {
                "type": "assistant",
                "message": {
                    "content": [
                        {
                            "type": "tool_result",
                            "name": "Bash",
                            "content": "boom",
                            "is_error": True,
                        }
                    ]
                },
            },
        )
        events = list(_map_stream_message_to_event(msg))
        tool_results = [e for e in events if e["type"] == "tool_result"]
        assert len(tool_results) == 1
        assert tool_results[0]["is_error"] is True

    def test_tool_use_result_is_error_defaults_false(self) -> None:
        """tool_result block without is_error defaults to False."""
        msg = cast(
            StreamMessage,
            {
                "type": "assistant",
                "message": {
                    "content": [
                        {
                            "type": "tool_result",
                            "name": "Bash",
                            "content": "ok",
                        }
                    ]
                },
            },
        )
        events = list(_map_stream_message_to_event(msg))
        tool_results = [e for e in events if e["type"] == "tool_result"]
        assert len(tool_results) == 1
        assert tool_results[0]["is_error"] is False


class TestFindUnavailableMcpServers:
    """Tests for the MCP server availability guard (find_unavailable_mcp_servers)."""

    def test_none_system_message_returns_empty(self) -> None:
        assert find_unavailable_mcp_servers(None) == []

    def test_no_servers_configured_returns_empty(self) -> None:
        msg = cast(StreamMessage, {"type": "system", "subtype": "init", "tools": []})
        assert find_unavailable_mcp_servers(msg) == []

    def test_all_connected_returns_empty(self) -> None:
        msg = cast(
            StreamMessage,
            {
                "type": "system",
                "subtype": "init",
                "mcp_servers": [
                    {"name": "mcp-tools-py", "status": "connected"},
                    {"name": "mcp-workspace", "status": "connected"},
                ],
            },
        )
        assert find_unavailable_mcp_servers(msg) == []

    def test_failed_and_pending_are_reported(self) -> None:
        """Reproduces the #995 init: mcp-tools-py failed, mcp-workspace pending."""
        msg = cast(
            StreamMessage,
            {
                "type": "system",
                "subtype": "init",
                "mcp_servers": [
                    {"name": "mcp-tools-py", "status": "failed"},
                    {"name": "mcp-workspace", "status": "pending"},
                ],
            },
        )
        assert find_unavailable_mcp_servers(msg) == [
            ("mcp-tools-py", "failed"),
            ("mcp-workspace", "pending"),
        ]

    def test_only_unavailable_servers_reported(self) -> None:
        msg = cast(
            StreamMessage,
            {
                "type": "system",
                "subtype": "init",
                "mcp_servers": [
                    {"name": "mcp-tools-py", "status": "connected"},
                    {"name": "mcp-workspace", "status": "failed"},
                ],
            },
        )
        assert find_unavailable_mcp_servers(msg) == [("mcp-workspace", "failed")]

    def test_missing_status_treated_as_unavailable(self) -> None:
        msg = cast(
            StreamMessage,
            {"type": "system", "subtype": "init", "mcp_servers": [{"name": "x"}]},
        )
        assert find_unavailable_mcp_servers(msg) == [("x", "unknown")]

    def test_status_is_case_insensitive(self) -> None:
        msg = cast(
            StreamMessage,
            {
                "type": "system",
                "subtype": "init",
                "mcp_servers": [{"name": "mcp-workspace", "status": "Connected"}],
            },
        )
        assert find_unavailable_mcp_servers(msg) == []


class TestMcpServerGuardInAskClaude:
    """ask_claude_code_cli aborts when configured MCP servers aren't connected."""

    @staticmethod
    def _stream_with_servers(servers: list[dict[str, str]]) -> str:
        system_msg = json.dumps(
            {
                "type": "system",
                "subtype": "init",
                "session_id": "sess-mcp",
                "tools": [],
                "mcp_servers": servers,
            }
        )
        result_msg = json.dumps(
            {
                "type": "result",
                "subtype": "success",
                "is_error": False,
                "result": "done",
                "session_id": "sess-mcp",
            }
        )
        return f"{system_msg}\n{result_msg}"

    @patch("mcp_coder.llm.providers.claude.claude_code_cli._find_claude_executable")
    @patch("mcp_coder.llm.providers.claude.claude_code_cli.execute_subprocess")
    def test_raises_when_server_failed(
        self, mock_execute: MagicMock, mock_find: MagicMock
    ) -> None:
        mock_find.return_value = "claude"
        stream = self._stream_with_servers(
            [
                {"name": "mcp-tools-py", "status": "failed"},
                {"name": "mcp-workspace", "status": "pending"},
            ]
        )
        mock_execute.return_value = CommandResult(
            return_code=0, stdout=stream, stderr="", timed_out=False
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(McpServersUnavailableError) as exc_info:
                ask_claude_code_cli("Test question", logs_dir=tmpdir)

        assert "mcp-tools-py=failed" in str(exc_info.value)
        assert "mcp-workspace=pending" in str(exc_info.value)

    @patch("mcp_coder.llm.providers.claude.claude_code_cli._find_claude_executable")
    @patch("mcp_coder.llm.providers.claude.claude_code_cli.execute_subprocess")
    def test_succeeds_when_all_connected(
        self, mock_execute: MagicMock, mock_find: MagicMock
    ) -> None:
        mock_find.return_value = "claude"
        stream = self._stream_with_servers(
            [{"name": "mcp-workspace", "status": "connected"}]
        )
        mock_execute.return_value = CommandResult(
            return_code=0, stdout=stream, stderr="", timed_out=False
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            result = ask_claude_code_cli("Test question", logs_dir=tmpdir)

        assert result["session_id"] == "sess-mcp"
        assert result["text"] == "done"


class TestMcpServerGuardInStream:
    """ask_claude_code_cli_stream aborts when configured MCP servers fail."""

    @staticmethod
    def _stream_lines(servers: list[dict[str, str]]) -> list[str]:
        system_msg = json.dumps(
            {
                "type": "system",
                "subtype": "init",
                "session_id": "sess-mcp",
                "tools": [],
                "mcp_servers": servers,
            }
        )
        assistant_msg = json.dumps(
            {
                "type": "assistant",
                "message": {"content": [{"type": "text", "text": "blind answer"}]},
            }
        )
        result_msg = json.dumps(
            {
                "type": "result",
                "subtype": "success",
                "is_error": False,
                "result": "done",
                "session_id": "sess-mcp",
            }
        )
        return [system_msg, assistant_msg, result_msg]

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
    def test_raises_when_server_failed(
        self,
        mock_stream_sub: MagicMock,
        mock_log_path: MagicMock,
        _mock_find: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Streamed init with a non-connected server aborts before content."""
        mock_log_path.return_value = tmp_path / "stream.ndjson"
        lines = self._stream_lines(
            [
                {"name": "mcp-tools-py", "status": "failed"},
                {"name": "mcp-workspace", "status": "pending"},
            ]
        )
        mock_stream_sub.return_value = _make_mock_stream(lines)

        events: list[StreamEvent] = []
        with pytest.raises(McpServersUnavailableError) as exc_info:
            for event in ask_claude_code_cli_stream("test question"):
                events.append(event)

        assert "mcp-tools-py=failed" in str(exc_info.value)
        assert "mcp-workspace=pending" in str(exc_info.value)
        # Aborted before any assistant content was yielded.
        assert not [e for e in events if e.get("type") == "text_delta"]

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
    def test_no_servers_configured_does_not_raise(
        self,
        mock_stream_sub: MagicMock,
        mock_log_path: MagicMock,
        _mock_find: MagicMock,
        tmp_path: Path,
    ) -> None:
        """A no-MCP stream (zero configured servers) is not aborted."""
        mock_log_path.return_value = tmp_path / "stream.ndjson"
        mock_stream_sub.return_value = _make_mock_stream(self._stream_lines([]))

        events = list(ask_claude_code_cli_stream("test question"))
        text_deltas = [e for e in events if e.get("type") == "text_delta"]
        assert [e["text"] for e in text_deltas] == ["blind answer"]


class TestInitMessageCapture:
    """Regression for #998: the init event must survive later `system` events."""

    def test_init_kept_despite_trailing_thinking_tokens(self) -> None:
        """Stream shaped like the 21:41/21:52 runs: init(pending) then thinking_tokens.

        Previously `_parse_stream_lines` kept the LAST system event, so a trailing
        `thinking_tokens` (no `mcp_servers`) hid the failed startup from the guard.
        """
        init = json.dumps(
            {
                "type": "system",
                "subtype": "init",
                "session_id": "s1",
                "tools": [],
                "mcp_servers": [
                    {"name": "mcp-tools-py", "status": "pending"},
                    {"name": "mcp-workspace", "status": "pending"},
                ],
            }
        )
        think1 = json.dumps(
            {"type": "system", "subtype": "thinking_tokens", "session_id": "s1"}
        )
        think2 = json.dumps(
            {"type": "system", "subtype": "thinking_tokens", "session_id": "s1"}
        )
        assistant = json.dumps(
            {
                "type": "assistant",
                "message": {"content": [{"type": "text", "text": "hi"}]},
                "session_id": "s1",
            }
        )
        result = json.dumps(
            {"type": "result", "subtype": "success", "result": "hi", "session_id": "s1"}
        )
        content = "\n".join([init, think1, assistant, think2, result])

        parsed = parse_stream_json_string(content)
        sm = parsed["system_message"]
        assert sm is not None
        assert sm.get("subtype") == "init"
        # The guard now sees the init's pending servers (it would have missed them).
        assert find_unavailable_mcp_servers(sm) == [
            ("mcp-tools-py", "pending"),
            ("mcp-workspace", "pending"),
        ]

    def test_first_system_kept_when_no_init(self) -> None:
        """With no init event, fall back to the first system message (not the last)."""
        sys1 = json.dumps(
            {
                "type": "system",
                "subtype": "other",
                "session_id": "s1",
                "marker": "first",
            }
        )
        sys2 = json.dumps(
            {"type": "system", "subtype": "thinking_tokens", "session_id": "s1"}
        )
        result = json.dumps({"type": "result", "result": "x", "session_id": "s1"})
        parsed = parse_stream_json_string("\n".join([sys1, sys2, result]))
        sm = parsed["system_message"]
        assert sm is not None
        assert sm.get("marker") == "first"


class TestMcpFailureIsRetryable:
    """Classify which MCP-unavailable failures are worth retrying."""

    def test_all_pending_is_retryable(self) -> None:
        assert mcp_failure_is_retryable([("a", "pending"), ("b", "pending")]) is True

    def test_any_failed_is_not_retryable(self) -> None:
        assert mcp_failure_is_retryable([("a", "pending"), ("b", "failed")]) is False

    def test_unknown_is_not_retryable(self) -> None:
        assert mcp_failure_is_retryable([("a", "unknown")]) is False

    def test_empty_is_not_retryable(self) -> None:
        assert mcp_failure_is_retryable([]) is False


class TestMcpRetryInAskClaude:
    """ask_claude_code_cli retries transient 'pending' MCP startups (#998)."""

    @staticmethod
    def _stream(servers: list[dict[str, str]], text: str = "done") -> str:
        # Trailing thinking_tokens mirrors real long sessions (the #998 shape).
        init = json.dumps(
            {
                "type": "system",
                "subtype": "init",
                "session_id": "sess-r",
                "tools": [],
                "mcp_servers": servers,
            }
        )
        think = json.dumps(
            {"type": "system", "subtype": "thinking_tokens", "session_id": "sess-r"}
        )
        result = json.dumps(
            {
                "type": "result",
                "subtype": "success",
                "result": text,
                "session_id": "sess-r",
            }
        )
        return f"{init}\n{think}\n{result}"

    @patch("mcp_coder.llm.providers.claude.claude_code_cli.time.sleep")
    @patch("mcp_coder.llm.providers.claude.claude_code_cli._find_claude_executable")
    @patch("mcp_coder.llm.providers.claude.claude_code_cli.execute_subprocess")
    def test_pending_then_connected_succeeds_after_retry(
        self, mock_execute: MagicMock, mock_find: MagicMock, mock_sleep: MagicMock
    ) -> None:
        mock_find.return_value = "claude"
        pending = CommandResult(
            return_code=0,
            stdout=self._stream([{"name": "mcp-workspace", "status": "pending"}]),
            stderr="",
            timed_out=False,
        )
        connected = CommandResult(
            return_code=0,
            stdout=self._stream([{"name": "mcp-workspace", "status": "connected"}]),
            stderr="",
            timed_out=False,
        )
        mock_execute.side_effect = [pending, connected]

        with tempfile.TemporaryDirectory() as tmpdir:
            result = ask_claude_code_cli("q", logs_dir=tmpdir)

        assert result["session_id"] == "sess-r"
        assert result["text"] == "done"
        assert mock_execute.call_count == 2
        mock_sleep.assert_called_once()

    @patch("mcp_coder.llm.providers.claude.claude_code_cli.time.sleep")
    @patch("mcp_coder.llm.providers.claude.claude_code_cli._find_claude_executable")
    @patch("mcp_coder.llm.providers.claude.claude_code_cli.execute_subprocess")
    def test_pending_exhausts_retries_then_raises(
        self, mock_execute: MagicMock, mock_find: MagicMock, mock_sleep: MagicMock
    ) -> None:
        mock_find.return_value = "claude"
        mock_execute.return_value = CommandResult(
            return_code=0,
            stdout=self._stream([{"name": "mcp-workspace", "status": "pending"}]),
            stderr="",
            timed_out=False,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(McpServersUnavailableError):
                ask_claude_code_cli("q", logs_dir=tmpdir)

        # one initial attempt + MCP_UNAVAILABLE_MAX_RETRIES retries
        assert mock_execute.call_count == MCP_UNAVAILABLE_MAX_RETRIES + 1

    @patch("mcp_coder.llm.providers.claude.claude_code_cli.time.sleep")
    @patch("mcp_coder.llm.providers.claude.claude_code_cli._find_claude_executable")
    @patch("mcp_coder.llm.providers.claude.claude_code_cli.execute_subprocess")
    def test_failed_status_not_retried(
        self, mock_execute: MagicMock, mock_find: MagicMock, mock_sleep: MagicMock
    ) -> None:
        mock_find.return_value = "claude"
        mock_execute.return_value = CommandResult(
            return_code=0,
            stdout=self._stream([{"name": "mcp-tools-py", "status": "failed"}]),
            stderr="",
            timed_out=False,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(McpServersUnavailableError):
                ask_claude_code_cli("q", logs_dir=tmpdir)

        assert mock_execute.call_count == 1
        mock_sleep.assert_not_called()
