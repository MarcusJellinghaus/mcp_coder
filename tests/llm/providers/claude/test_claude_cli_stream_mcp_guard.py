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
    MCP_NEEDS_AUTH_STATUS,
    McpServersUnavailableError,
    StreamMessage,
    ask_claude_code_cli,
    find_exposed_mcp_tools,
    find_fatal_mcp_servers,
    find_unavailable_mcp_servers,
    load_mcp_server_names,
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

    def test_needs_auth_is_reported(self) -> None:
        """Unauthenticated account connectors stay visible to reporting consumers."""
        msg = cast(
            StreamMessage,
            {
                "type": "system",
                "subtype": "init",
                "mcp_servers": [
                    {"name": "a", "status": "connected"},
                    {"name": "b", "status": "pending"},
                    {"name": "c", "status": "needs-auth"},
                ],
            },
        )
        assert find_unavailable_mcp_servers(msg) == {
            "b": "pending",
            "c": MCP_NEEDS_AUTH_STATUS,
        }

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

    def test_needs_auth_is_tolerated(self) -> None:
        """Unauthenticated claude.ai account connectors are optional, never fatal (#1090)."""
        msg = cast(
            StreamMessage,
            {
                "type": "system",
                "subtype": "init",
                "mcp_servers": [
                    {"name": "a", "status": "connected"},
                    {"name": "b", "status": "pending"},
                    {"name": "c", "status": "needs-auth"},
                ],
            },
        )
        assert find_fatal_mcp_servers(msg) == {}

    def test_failed_still_fatal_alongside_needs_auth(self) -> None:
        """Tolerating needs-auth must not mask genuinely failed servers."""
        msg = cast(
            StreamMessage,
            {
                "type": "system",
                "subtype": "init",
                "mcp_servers": [
                    {"name": "a", "status": "connected"},
                    {"name": "b", "status": "pending"},
                    {"name": "c", "status": "needs-auth"},
                    {"name": "d", "status": "failed"},
                ],
            },
        )
        assert find_fatal_mcp_servers(msg) == {"d": "failed"}

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


class TestFindExposedMcpTools:
    """find_exposed_mcp_tools reads the init event's ``tools`` field.

    Fixtures mirror the verified real init-event shape: a connected server
    publishes its ``mcp__*`` names into ``tools`` (non-zero count), while a
    pending/cold-starting server exposes only ``ToolSearch`` (zero count).
    """

    def test_none_system_message_returns_empty(self) -> None:
        assert find_exposed_mcp_tools(None) == []

    def test_no_tools_key_returns_empty(self) -> None:
        msg = cast(StreamMessage, {"type": "system", "subtype": "init"})
        assert find_exposed_mcp_tools(msg) == []

    def test_healthy_returns_sorted_mcp_names_only(self) -> None:
        """Connected server: ``tools`` mixes builtin + mcp names (real shape)."""
        msg = cast(
            StreamMessage,
            {
                "type": "system",
                "subtype": "init",
                "tools": [
                    "ToolSearch",
                    "mcp__mcp-tools-py__run_pytest_check",
                    "mcp__mcp-workspace__read_file",
                ],
            },
        )
        assert find_exposed_mcp_tools(msg) == [
            "mcp__mcp-tools-py__run_pytest_check",
            "mcp__mcp-workspace__read_file",
        ]

    def test_degraded_connected_but_no_tools_returns_empty(self) -> None:
        """Pending/cold-start: only ToolSearch published → zero MCP tools."""
        msg = cast(
            StreamMessage,
            {"type": "system", "subtype": "init", "tools": ["ToolSearch"]},
        )
        assert find_exposed_mcp_tools(msg) == []

    def test_empty_tools_list_returns_empty(self) -> None:
        msg = cast(StreamMessage, {"type": "system", "subtype": "init", "tools": []})
        assert find_exposed_mcp_tools(msg) == []

    def test_dict_shaped_entries_are_supported(self) -> None:
        msg = cast(
            StreamMessage,
            {
                "type": "system",
                "subtype": "init",
                "tools": [{"name": "mcp__x__y"}, {"name": "Bash"}],
            },
        )
        assert find_exposed_mcp_tools(msg) == ["mcp__x__y"]

    def test_duplicates_collapse_and_output_is_sorted(self) -> None:
        msg = cast(
            StreamMessage,
            {
                "type": "system",
                "subtype": "init",
                "tools": [
                    "mcp__b__two",
                    "mcp__a__one",
                    "mcp__b__two",
                ],
            },
        )
        assert find_exposed_mcp_tools(msg) == ["mcp__a__one", "mcp__b__two"]


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

    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming._find_claude_executable"
    )
    @patch("mcp_coder.llm.providers.claude.claude_code_cli_streaming.stream_subprocess")
    def test_raises_when_server_failed(
        self, mock_stream: MagicMock, mock_find: MagicMock
    ) -> None:
        """A failed server (alongside pending) still aborts; message lists fatal."""
        mock_find.return_value = "claude"
        lines = self._stream_with_servers(
            [
                {"name": "mcp-tools-py", "status": "failed"},
                {"name": "mcp-workspace", "status": "pending"},
            ]
        ).split("\n")
        mock_stream.return_value = _make_mock_stream(lines)

        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(McpServersUnavailableError) as exc_info:
                ask_claude_code_cli("Test question", logs_dir=tmpdir)

        # Only the fatal server is carried in the abort message; pending is
        # tolerated (self-heals via ToolSearch) and need not appear.
        assert "mcp-tools-py=failed" in str(exc_info.value)

    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming._find_claude_executable"
    )
    @patch("mcp_coder.llm.providers.claude.claude_code_cli_streaming.stream_subprocess")
    def test_failed_aborts_single_attempt(
        self, mock_stream: MagicMock, mock_find: MagicMock
    ) -> None:
        """A fatal (failed) server aborts in exactly one attempt — no retry."""
        mock_find.return_value = "claude"
        lines = self._stream_with_servers(
            [{"name": "mcp-tools-py", "status": "failed"}]
        ).split("\n")
        mock_stream.return_value = _make_mock_stream(lines)

        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(McpServersUnavailableError) as exc_info:
                ask_claude_code_cli("Test question", logs_dir=tmpdir)

        assert "mcp-tools-py=failed" in str(exc_info.value)
        assert mock_stream.call_count == 1

    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming._find_claude_executable"
    )
    @patch("mcp_coder.llm.providers.claude.claude_code_cli_streaming.stream_subprocess")
    def test_pending_only_succeeds_single_attempt(
        self, mock_stream: MagicMock, mock_find: MagicMock
    ) -> None:
        """A pending-only init is tolerated: no raise, normal result, one call."""
        mock_find.return_value = "claude"
        lines = self._stream_with_servers(
            [
                {"name": "mcp-tools-py", "status": "pending"},
                {"name": "mcp-workspace", "status": "pending"},
            ]
        ).split("\n")
        mock_stream.return_value = _make_mock_stream(lines)

        with tempfile.TemporaryDirectory() as tmpdir:
            result = ask_claude_code_cli("Test question", logs_dir=tmpdir)

        assert result["session_id"] == "sess-mcp"
        assert result["text"] == "done"
        assert mock_stream.call_count == 1

    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming._find_claude_executable"
    )
    @patch("mcp_coder.llm.providers.claude.claude_code_cli_streaming.stream_subprocess")
    def test_succeeds_when_all_connected(
        self, mock_stream: MagicMock, mock_find: MagicMock
    ) -> None:
        mock_find.return_value = "claude"
        lines = self._stream_with_servers(
            [{"name": "mcp-workspace", "status": "connected"}]
        ).split("\n")
        mock_stream.return_value = _make_mock_stream(lines)

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

        # Only the fatal server is carried in the abort message; pending is
        # tolerated (self-heals via ToolSearch) and need not appear.
        assert "mcp-tools-py=failed" in str(exc_info.value)
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
    """Streaming path tolerates pending but still aborts on fatal (#998, #999)."""

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
    def test_stream_pending_init_proceeds(
        self,
        mock_stream_sub: MagicMock,
        mock_log_path: MagicMock,
        _mock_find: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Pending-only init self-heals via ToolSearch: proceed and yield content.

        Matches the blocking path (D4): a still-starting server is tolerated,
        even with a trailing thinking_tokens system event, so the stream
        proceeds and the assistant text_delta reaches the consumer.
        """
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
                "message": {"content": [{"type": "text", "text": "real answer"}]},
            }
        )
        mock_stream_sub.return_value = _make_mock_stream([init, think, assistant])

        events = list(ask_claude_code_cli_stream("q"))

        text_deltas = [e for e in events if e.get("type") == "text_delta"]
        assert [e["text"] for e in text_deltas] == ["real answer"]

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
    def test_stream_needs_auth_only_proceeds(
        self,
        mock_stream_sub: MagicMock,
        mock_log_path: MagicMock,
        _mock_find: MagicMock,
        tmp_path: Path,
    ) -> None:
        """needs-auth-only connectors are optional account connectors: no abort (#1090)."""
        mock_log_path.return_value = tmp_path / "stream.ndjson"
        init = json.dumps(
            {
                "type": "system",
                "subtype": "init",
                "session_id": "s",
                "tools": [],
                "mcp_servers": [
                    {"name": "mcp-workspace", "status": "connected"},
                    {"name": "claude.ai Google Drive", "status": "needs-auth"},
                ],
            }
        )
        assistant = json.dumps(
            {
                "type": "assistant",
                "message": {"content": [{"type": "text", "text": "real answer"}]},
            }
        )
        mock_stream_sub.return_value = _make_mock_stream([init, assistant])

        events = list(ask_claude_code_cli_stream("q"))

        text_deltas = [e for e in events if e.get("type") == "text_delta"]
        assert [e["text"] for e in text_deltas] == ["real answer"]

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
    def test_stream_incident_1090_shape_proceeds(
        self,
        mock_stream_sub: MagicMock,
        mock_log_path: MagicMock,
        _mock_find: MagicMock,
        tmp_path: Path,
    ) -> None:
        """The #1090 incident init (pending + 3 needs-auth connectors) must not abort."""
        mock_log_path.return_value = tmp_path / "stream.ndjson"
        init = json.dumps(
            {
                "type": "system",
                "subtype": "init",
                "session_id": "s",
                "tools": [],
                "mcp_servers": [
                    {"name": "obsidian-wiki", "status": "pending"},
                    {"name": "claude.ai Google Drive", "status": "needs-auth"},
                    {"name": "claude.ai Gmail", "status": "needs-auth"},
                    {"name": "claude.ai Google Calendar", "status": "needs-auth"},
                ],
            }
        )
        assistant = json.dumps(
            {
                "type": "assistant",
                "message": {"content": [{"type": "text", "text": "commit msg"}]},
            }
        )
        mock_stream_sub.return_value = _make_mock_stream([init, assistant])

        events = list(ask_claude_code_cli_stream("q"))

        text_deltas = [e for e in events if e.get("type") == "text_delta"]
        assert [e["text"] for e in text_deltas] == ["commit msg"]

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
    def test_stream_aborts_on_failed_alongside_needs_auth(
        self,
        mock_stream_sub: MagicMock,
        mock_log_path: MagicMock,
        _mock_find: MagicMock,
        tmp_path: Path,
    ) -> None:
        """A failed configured server still aborts even with needs-auth connectors present."""
        mock_log_path.return_value = tmp_path / "stream.ndjson"
        init = json.dumps(
            {
                "type": "system",
                "subtype": "init",
                "session_id": "s",
                "tools": [],
                "mcp_servers": [
                    {"name": "mcp-workspace", "status": "failed"},
                    {"name": "claude.ai Gmail", "status": "needs-auth"},
                ],
            }
        )
        mock_stream_sub.return_value = _make_mock_stream([init])

        with pytest.raises(McpServersUnavailableError) as exc:
            list(ask_claude_code_cli_stream("q"))

        assert "mcp-workspace=failed" in str(exc.value)
        assert exc.value.unavailable_servers == {"mcp-workspace": "failed"}

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
    def test_stream_aborts_on_fatal_despite_thinking(
        self,
        mock_stream_sub: MagicMock,
        mock_log_path: MagicMock,
        _mock_find: MagicMock,
        tmp_path: Path,
    ) -> None:
        """A failed server still aborts even when followed by thinking_tokens (#998)."""
        mock_log_path.return_value = tmp_path / "stream.ndjson"
        init = json.dumps(
            {
                "type": "system",
                "subtype": "init",
                "session_id": "s",
                "tools": [],
                "mcp_servers": [{"name": "mcp-workspace", "status": "failed"}],
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

        assert "mcp-workspace=failed" in str(exc.value)
        # Aborted before any assistant content was leaked to the consumer.
        assert not any(e.get("type") == "text_delta" for e in events)


class TestLoadMcpServerNames:
    """load_mcp_server_names parses the mcpServers keys of an mcp-config file."""

    def test_happy_path_returns_server_names(self, tmp_path: Path) -> None:
        config = tmp_path / "mcp.json"
        config.write_text(
            json.dumps(
                {
                    "mcpServers": {
                        "mcp-tools-py": {"command": "x"},
                        "mcp-workspace": {"command": "y"},
                    }
                }
            ),
            encoding="utf-8",
        )
        assert load_mcp_server_names(str(config)) == {"mcp-tools-py", "mcp-workspace"}

    def test_relative_path_resolves_against_base_dir(self, tmp_path: Path) -> None:
        """A relative path resolves against base_dir (subprocess cwd), not our cwd."""
        (tmp_path / "sub").mkdir()
        config = tmp_path / "sub" / "mcp.json"
        config.write_text(
            json.dumps({"mcpServers": {"only-server": {}}}), encoding="utf-8"
        )
        result = load_mcp_server_names("sub/mcp.json", base_dir=str(tmp_path))
        assert result == {"only-server"}

    def test_missing_file_raises_value_error_naming_path(self, tmp_path: Path) -> None:
        missing = tmp_path / "nope.json"
        with pytest.raises(ValueError) as exc:
            load_mcp_server_names(str(missing))
        assert str(missing) in str(exc.value)

    def test_malformed_json_raises_value_error(self, tmp_path: Path) -> None:
        config = tmp_path / "broken.json"
        config.write_text("{not json", encoding="utf-8")
        with pytest.raises(ValueError) as exc:
            load_mcp_server_names(str(config))
        assert str(config) in str(exc.value)

    def test_top_level_non_dict_raises_value_error(self, tmp_path: Path) -> None:
        config = tmp_path / "list.json"
        config.write_text(json.dumps(["not", "a", "dict"]), encoding="utf-8")
        with pytest.raises(ValueError):
            load_mcp_server_names(str(config))

    def test_mcp_servers_non_dict_raises_value_error(self, tmp_path: Path) -> None:
        config = tmp_path / "bad_servers.json"
        config.write_text(json.dumps({"mcpServers": ["a", "b"]}), encoding="utf-8")
        with pytest.raises(ValueError) as exc:
            load_mcp_server_names(str(config))
        assert "mcpServers" in str(exc.value)

    def test_missing_mcp_servers_key_yields_empty_set(self, tmp_path: Path) -> None:
        """No mcpServers key is valid: a session deliberately without servers."""
        config = tmp_path / "empty.json"
        config.write_text(json.dumps({"other": 1}), encoding="utf-8")
        assert load_mcp_server_names(str(config)) == set()


class TestStreamMcpGuardScoping:
    """With mcp_config supplied, only servers listed in it can abort (#1090)."""

    @staticmethod
    def _write_config(tmp_path: Path, server_names: list[str]) -> str:
        config = tmp_path / "mcp.json"
        config.write_text(
            json.dumps({"mcpServers": {name: {} for name in server_names}}),
            encoding="utf-8",
        )
        return str(config)

    @staticmethod
    def _init_line(servers: list[dict[str, str]]) -> str:
        return json.dumps(
            {
                "type": "system",
                "subtype": "init",
                "session_id": "s",
                "tools": [],
                "mcp_servers": servers,
            }
        )

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
    def test_non_configured_failed_server_does_not_raise(
        self,
        mock_stream_sub: MagicMock,
        mock_log_path: MagicMock,
        _mock_find: MagicMock,
        tmp_path: Path,
    ) -> None:
        """A failed server outside --mcp-config is ignored (with needs-auth too)."""
        mock_log_path.return_value = tmp_path / "stream.ndjson"
        mcp_config = self._write_config(tmp_path, ["mcp-workspace"])
        init = self._init_line(
            [
                {"name": "mcp-workspace", "status": "connected"},
                {"name": "obsidian-wiki", "status": "failed"},
                {"name": "claude.ai Gmail", "status": "needs-auth"},
            ]
        )
        assistant = json.dumps(
            {
                "type": "assistant",
                "message": {"content": [{"type": "text", "text": "real answer"}]},
            }
        )
        mock_stream_sub.return_value = _make_mock_stream([init, assistant])

        events = list(ask_claude_code_cli_stream("q", mcp_config=mcp_config))

        text_deltas = [e for e in events if e.get("type") == "text_delta"]
        assert [e["text"] for e in text_deltas] == ["real answer"]

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
    def test_configured_failed_server_still_raises(
        self,
        mock_stream_sub: MagicMock,
        mock_log_path: MagicMock,
        _mock_find: MagicMock,
        tmp_path: Path,
    ) -> None:
        """A failed server that IS listed in --mcp-config still aborts."""
        mock_log_path.return_value = tmp_path / "stream.ndjson"
        mcp_config = self._write_config(tmp_path, ["mcp-workspace"])
        init = self._init_line([{"name": "mcp-workspace", "status": "failed"}])
        mock_stream_sub.return_value = _make_mock_stream([init])

        with pytest.raises(McpServersUnavailableError) as exc:
            list(ask_claude_code_cli_stream("q", mcp_config=mcp_config))

        assert "mcp-workspace=failed" in str(exc.value)

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
    def test_mixed_failures_raise_naming_only_configured(
        self,
        mock_stream_sub: MagicMock,
        mock_log_path: MagicMock,
        _mock_find: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Configured and non-configured failures: only the configured one aborts."""
        mock_log_path.return_value = tmp_path / "stream.ndjson"
        mcp_config = self._write_config(tmp_path, ["mcp-workspace"])
        init = self._init_line(
            [
                {"name": "mcp-workspace", "status": "failed"},
                {"name": "obsidian-wiki", "status": "failed"},
            ]
        )
        mock_stream_sub.return_value = _make_mock_stream([init])

        with pytest.raises(McpServersUnavailableError) as exc:
            list(ask_claude_code_cli_stream("q", mcp_config=mcp_config))

        assert exc.value.unavailable_servers == {"mcp-workspace": "failed"}
        assert "obsidian-wiki" not in str(exc.value)

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
    def test_bad_config_path_raises_before_subprocess(
        self,
        mock_stream_sub: MagicMock,
        mock_log_path: MagicMock,
        _mock_find: MagicMock,
        tmp_path: Path,
    ) -> None:
        """An unreadable --mcp-config is an operator error: fail fast, no launch."""
        mock_log_path.return_value = tmp_path / "stream.ndjson"
        missing = tmp_path / "missing.json"

        with pytest.raises(ValueError) as exc:
            list(ask_claude_code_cli_stream("q", mcp_config=str(missing)))

        assert str(missing) in str(exc.value)
        mock_stream_sub.assert_not_called()
