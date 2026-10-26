import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.llm.providers.claude.claude_code_cli_streaming import (
    ask_claude_code_cli_stream,
)

from .conftest import _make_stream_gen


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
            for raw_event, original_line in zip(raw_lines, lines, strict=True):
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

            assert len(error_events) == 1  # elif suppresses the second error
            msg = str(error_events[0]["message"])
            assert "LLM inactivity timeout (claude)" in msg
            assert "no output for 30s" in msg
            assert "--timeout" in msg

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
    def test_ask_claude_stream_passes_settings_file(
        self,
        mock_get_path: MagicMock,
        mock_stream: MagicMock,
        mock_find: MagicMock,
    ) -> None:
        """Verify ask_claude_code_cli_stream forwards settings_file to build_cli_command."""
        mock_find.return_value = "claude"
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_get_path.return_value = Path(tmpdir) / "test.ndjson"
            mock_stream.return_value = _make_stream_gen(
                [json.dumps({"type": "result", "session_id": "s1"})]
            )

            settings_path = "C:/path/.claude/settings.local.json"
            list(ask_claude_code_cli_stream("Hello", settings_file=settings_path))

            call_args = mock_stream.call_args
            command = call_args[0][0]
            assert "--settings" in command
            assert settings_path in command
            idx = command.index("--settings")
            assert command[idx + 1] == settings_path

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
