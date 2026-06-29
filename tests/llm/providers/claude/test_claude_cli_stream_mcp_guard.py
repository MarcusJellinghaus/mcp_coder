#!/usr/bin/env python3
"""Tests for the Claude CLI MCP-availability guard.

Split from test_claude_cli_stream_parsing.py to keep file sizes manageable.
Covers find_unavailable_mcp_servers, find_fatal_mcp_servers, the init-event
capture regression (#998), and the guard behaviour in both the blocking and
streaming code paths.
"""

import json
import tempfile
from pathlib import Path
from typing import cast
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.llm.providers.claude.claude_code_cli import (
    McpServersUnavailableError,
    StreamMessage,
    ask_claude_code_cli,
    find_fatal_mcp_servers,
    find_unavailable_mcp_servers,
    parse_stream_json_string,
)
from mcp_coder.llm.providers.claude.claude_code_cli_streaming import (
    ask_claude_code_cli_stream,
)
from mcp_coder.llm.types import StreamEvent
from mcp_coder.utils.subprocess_runner import CommandResult


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


class TestFindUnavailableMcpServers:
    """Tests for the MCP server availability guard (find_unavailable_mcp_servers)."""

    def test_none_system_message_returns_empty(self) -> None:
        assert find_unavailable_mcp_servers(None) == {}

    def test_no_servers_configured_returns_empty(self) -> None:
        msg = cast(StreamMessage, {"type": "system", "subtype": "init", "tools": []})
        assert find_unavailable_mcp_servers(msg) == {}

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
        assert find_unavailable_mcp_servers(msg) == {}

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
        assert find_unavailable_mcp_servers(msg) == {
            "mcp-tools-py": "failed",
            "mcp-workspace": "pending",
        }

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
        assert find_unavailable_mcp_servers(msg) == {"mcp-workspace": "failed"}

    def test_missing_status_treated_as_unavailable(self) -> None:
        msg = cast(
            StreamMessage,
            {"type": "system", "subtype": "init", "mcp_servers": [{"name": "x"}]},
        )
        assert find_unavailable_mcp_servers(msg) == {"x": "unknown"}

    def test_status_is_case_insensitive(self) -> None:
        msg = cast(
            StreamMessage,
            {
                "type": "system",
                "subtype": "init",
                "mcp_servers": [{"name": "mcp-workspace", "status": "Connected"}],
            },
        )
        assert find_unavailable_mcp_servers(msg) == {}


class TestFindFatalMcpServers:
    """find_fatal_mcp_servers reports only terminal (non-pending) servers."""

    def test_none_system_message_returns_empty(self) -> None:
        assert find_fatal_mcp_servers(None) == {}

    def test_pending_is_tolerated(self) -> None:
        """A still-starting (pending) server self-heals via ToolSearch."""
        msg = cast(
            StreamMessage,
            {
                "type": "system",
                "subtype": "init",
                "mcp_servers": [
                    {"name": "mcp-tools-py", "status": "pending"},
                    {"name": "mcp-workspace", "status": "pending"},
                ],
            },
        )
        assert find_fatal_mcp_servers(msg) == {}

    def test_all_connected_returns_empty(self) -> None:
        msg = cast(
            StreamMessage,
            {
                "type": "system",
                "subtype": "init",
                "mcp_servers": [{"name": "mcp-workspace", "status": "connected"}],
            },
        )
        assert find_fatal_mcp_servers(msg) == {}

    def test_failed_and_unknown_are_reported(self) -> None:
        msg = cast(
            StreamMessage,
            {
                "type": "system",
                "subtype": "init",
                "mcp_servers": [
                    {"name": "mcp-tools-py", "status": "failed"},
                    {"name": "mcp-workspace"},
                ],
            },
        )
        assert find_fatal_mcp_servers(msg) == {
            "mcp-tools-py": "failed",
            "mcp-workspace": "unknown",
        }

    def test_mixed_failed_and_pending_reports_only_failed(self) -> None:
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
        assert find_fatal_mcp_servers(msg) == {"mcp-tools-py": "failed"}


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
        assert find_unavailable_mcp_servers(sm) == {
            "mcp-tools-py": "pending",
            "mcp-workspace": "pending",
        }

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


class TestStreamMcpGuard:
    """Streaming path aborts on init-pending even with trailing thinking_tokens (#998)."""

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
    def test_stream_aborts_on_pending_init(
        self,
        mock_stream_sub: MagicMock,
        mock_log_path: MagicMock,
        _mock_find: MagicMock,
        tmp_path: Path,
    ) -> None:
        mock_log_path.return_value = tmp_path / "stream.ndjson"
        init = json.dumps(
            {
                "type": "system",
                "subtype": "init",
                "session_id": "s",
                "tools": [],
                "mcp_servers": [{"name": "mcp-workspace", "status": "pending"}],
            }
        )
        think = json.dumps(
            {"type": "system", "subtype": "thinking_tokens", "session_id": "s"}
        )
        assistant = json.dumps(
            {
                "type": "assistant",
                "message": {"content": [{"type": "text", "text": "leak"}]},
            }
        )
        mock_stream_sub.return_value = _make_mock_stream([init, think, assistant])

        events: list[StreamEvent] = []
        with pytest.raises(McpServersUnavailableError) as exc:
            for event in ask_claude_code_cli_stream("q"):
                events.append(event)

        assert "mcp-workspace=pending" in str(exc.value)
        # Aborted before any assistant content was leaked to the consumer.
        assert not any(e.get("type") == "text_delta" for e in events)
