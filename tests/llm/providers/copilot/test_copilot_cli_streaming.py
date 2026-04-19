"""Tests for Copilot CLI streaming implementation."""

import json
import logging
from collections.abc import Iterator
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.llm.providers.copilot.copilot_cli_streaming import (
    _map_copilot_message_to_event,
    ask_copilot_cli_stream,
)
from mcp_coder.llm.types import StreamEvent

# ──────────────────────────────────────────────────────────────────────
# Event mapping tests (unit, no subprocess)
# ──────────────────────────────────────────────────────────────────────


class TestMapAssistantMessageText:
    """Test assistant.message with text content → text_delta event."""

    def test_map_assistant_message_text(self) -> None:
        msg: dict[str, Any] = {
            "type": "assistant.message",
            "data": {
                "content": "Hello world",
                "toolRequests": [],
            },
        }
        events = list(_map_copilot_message_to_event(msg))
        assert len(events) == 1
        assert events[0] == {"type": "text_delta", "text": "Hello world"}

    def test_map_assistant_message_content_list_fallback(self) -> None:
        """Content as list of blocks is also handled."""
        msg: dict[str, Any] = {
            "type": "assistant.message",
            "data": {
                "content": [
                    {"type": "text", "text": "Part 1"},
                    {"type": "text", "text": "Part 2"},
                ],
                "toolRequests": [],
            },
        }
        events = list(_map_copilot_message_to_event(msg))
        assert len(events) == 2
        assert events[0]["text"] == "Part 1"
        assert events[1]["text"] == "Part 2"


class TestMapAssistantMessageToolRequest:
    """Test assistant.message with toolRequests → tool_use_start event."""

    def test_map_assistant_message_tool_request(self) -> None:
        msg: dict[str, Any] = {
            "type": "assistant.message",
            "data": {
                "content": "",
                "toolRequests": [
                    {"id": "t1", "name": "read_file", "args": {"path": "foo.py"}}
                ],
            },
        }
        events = list(_map_copilot_message_to_event(msg))
        assert len(events) == 1
        assert events[0] == {
            "type": "tool_use_start",
            "name": "read_file",
            "args": {"path": "foo.py"},
        }

    def test_map_assistant_message_text_and_tool(self) -> None:
        msg: dict[str, Any] = {
            "type": "assistant.message",
            "data": {
                "content": "Reading file...",
                "toolRequests": [
                    {"id": "t1", "name": "read_file", "args": {"path": "bar.py"}}
                ],
            },
        }
        events = list(_map_copilot_message_to_event(msg))
        assert len(events) == 2
        assert events[0]["type"] == "text_delta"
        assert events[1]["type"] == "tool_use_start"


class TestMapToolExecutionComplete:
    """Test tool.execution_complete → tool_result event."""

    def test_map_tool_execution_complete(self) -> None:
        msg: dict[str, Any] = {
            "type": "tool.execution_complete",
            "toolId": "t1",
            "result": "file contents here",
        }
        events = list(_map_copilot_message_to_event(msg))
        assert len(events) == 1
        assert events[0] == {
            "type": "tool_result",
            "name": "t1",
            "output": "file contents here",
        }


class TestMapResultToDone:
    """Test result → done event with session_id and usage."""

    def test_map_result_to_done(self) -> None:
        msg: dict[str, Any] = {
            "type": "result",
            "sessionId": "sess-abc",
            "usage": {"outputTokens": 100, "inputTokens": 50},
        }
        events = list(_map_copilot_message_to_event(msg))
        assert len(events) == 1
        assert events[0] == {
            "type": "done",
            "session_id": "sess-abc",
            "usage": {"output_tokens": 100, "input_tokens": 50},
        }

    def test_map_result_minimal(self) -> None:
        msg: dict[str, Any] = {"type": "result"}
        events = list(_map_copilot_message_to_event(msg))
        assert len(events) == 1
        assert events[0]["type"] == "done"
        assert events[0]["session_id"] is None
        assert events[0]["usage"] == {}


class TestMapSessionInfoUnknownToolWarning:
    """Test session.info with unknown-tool → error event + warning logged."""

    def test_map_session_info_unknown_tool_warning(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        msg: dict[str, Any] = {
            "type": "session.info",
            "data": {"message": "Unknown tool 'custom_tool' not available"},
        }
        with caplog.at_level(logging.WARNING):
            events = list(_map_copilot_message_to_event(msg))
        assert len(events) == 1
        assert events[0]["type"] == "error"
        assert "Unknown tool" in str(events[0]["message"])
        assert any("unknown tool" in r.message.lower() for r in caplog.records)

    def test_map_session_info_no_unknown_tool(self) -> None:
        msg: dict[str, Any] = {
            "type": "session.info",
            "data": {"message": "Session started successfully"},
        }
        events = list(_map_copilot_message_to_event(msg))
        assert len(events) == 0


class TestMapEphemeralTypesSkipped:
    """Test that ephemeral types yield nothing."""

    @pytest.mark.parametrize(
        "msg_type",
        [
            "session.mcp_servers_loaded",
            "assistant.reasoning",
            "session.start",
            "session.end",
        ],
    )
    def test_map_ephemeral_types_skipped(self, msg_type: str) -> None:
        msg: dict[str, Any] = {"type": msg_type, "data": "some data"}
        events = list(_map_copilot_message_to_event(msg))
        assert len(events) == 0


class TestMapAssistantMessageDeltaSkipped:
    """Test that assistant.message_delta yields nothing."""

    def test_map_assistant_message_delta_skipped(self) -> None:
        msg: dict[str, Any] = {
            "type": "assistant.message_delta",
            "delta": {"text": "partial"},
        }
        events = list(_map_copilot_message_to_event(msg))
        assert len(events) == 0


# ──────────────────────────────────────────────────────────────────────
# Stream integration tests (mocked subprocess)
# ──────────────────────────────────────────────────────────────────────


def _make_mock_stream(
    lines: list[str],
    *,
    timed_out: bool = False,
    return_code: int = 0,
) -> MagicMock:
    """Create a mock stream_subprocess return value."""
    mock_stream = MagicMock()
    mock_stream.__iter__ = lambda self: iter(lines)
    mock_stream.result = MagicMock()
    mock_stream.result.timed_out = timed_out
    mock_stream.result.return_code = return_code
    return mock_stream


@pytest.fixture()
def _mock_copilot_deps() -> Iterator[dict[str, Any]]:
    """Mock all external dependencies for stream tests."""
    with (
        patch(
            "mcp_coder.llm.providers.copilot.copilot_cli_streaming.find_executable",
            return_value="/usr/bin/copilot",
        ),
        patch(
            "mcp_coder.llm.providers.copilot.copilot_cli_streaming._read_settings_allow",
            return_value=None,
        ),
        patch(
            "mcp_coder.llm.providers.copilot.copilot_cli_streaming.get_stream_log_path",
        ) as mock_log_path,
        patch(
            "mcp_coder.llm.providers.copilot.copilot_cli_streaming.stream_subprocess",
        ) as mock_stream,
    ):
        yield {"mock_stream": mock_stream, "mock_log_path": mock_log_path}


class TestStreamYieldsRawLineForEachLine:
    """Every line produces a raw_line event."""

    @pytest.mark.usefixtures("_mock_copilot_deps")
    def test_stream_yields_raw_line_for_each_line(
        self,
        _mock_copilot_deps: dict[str, Any],
        tmp_path: Any,
    ) -> None:
        log_file = tmp_path / "stream.ndjson"
        _mock_copilot_deps["mock_log_path"].return_value = log_file

        lines = [
            json.dumps({"type": "session.start"}),
            json.dumps({"type": "result", "sessionId": "s1"}),
        ]
        _mock_copilot_deps["mock_stream"].return_value = _make_mock_stream(lines)

        events = list(ask_copilot_cli_stream("test question"))
        raw_events = [e for e in events if e.get("type") == "raw_line"]
        assert len(raw_events) == 2
        assert raw_events[0]["line"] == lines[0]
        assert raw_events[1]["line"] == lines[1]


class TestStreamYieldsTextAndDone:
    """Full JSONL output produces text_delta + done."""

    @pytest.mark.usefixtures("_mock_copilot_deps")
    def test_stream_yields_text_and_done(
        self,
        _mock_copilot_deps: dict[str, Any],
        tmp_path: Any,
    ) -> None:
        log_file = tmp_path / "stream.ndjson"
        _mock_copilot_deps["mock_log_path"].return_value = log_file

        lines = [
            json.dumps(
                {
                    "type": "assistant.message",
                    "data": {"content": "Hello", "toolRequests": []},
                }
            ),
            json.dumps(
                {
                    "type": "result",
                    "sessionId": "s1",
                    "usage": {"outputTokens": 10},
                }
            ),
        ]
        _mock_copilot_deps["mock_stream"].return_value = _make_mock_stream(lines)

        events = list(ask_copilot_cli_stream("test question"))
        typed_events = [e for e in events if e.get("type") != "raw_line"]
        assert len(typed_events) == 2
        assert typed_events[0] == {"type": "text_delta", "text": "Hello"}
        assert typed_events[1]["type"] == "done"
        assert typed_events[1]["session_id"] == "s1"


class TestStreamTimeoutYieldsError:
    """Timeout → error event."""

    @pytest.mark.usefixtures("_mock_copilot_deps")
    def test_stream_timeout_yields_error(
        self,
        _mock_copilot_deps: dict[str, Any],
        tmp_path: Any,
    ) -> None:
        log_file = tmp_path / "stream.ndjson"
        _mock_copilot_deps["mock_log_path"].return_value = log_file
        _mock_copilot_deps["mock_stream"].return_value = _make_mock_stream(
            [], timed_out=True
        )

        events = list(ask_copilot_cli_stream("test question"))
        error_events = [e for e in events if e.get("type") == "error"]
        assert len(error_events) == 1
        assert "timeout" in str(error_events[0]["message"]).lower()


class TestStreamNonzeroExitYieldsError:
    """Failed process → error event."""

    @pytest.mark.usefixtures("_mock_copilot_deps")
    def test_stream_nonzero_exit_yields_error(
        self,
        _mock_copilot_deps: dict[str, Any],
        tmp_path: Any,
    ) -> None:
        log_file = tmp_path / "stream.ndjson"
        _mock_copilot_deps["mock_log_path"].return_value = log_file
        _mock_copilot_deps["mock_stream"].return_value = _make_mock_stream(
            [], return_code=1
        )

        events = list(ask_copilot_cli_stream("test question"))
        error_events = [e for e in events if e.get("type") == "error"]
        assert len(error_events) == 1
        assert "code 1" in str(error_events[0]["message"])


class TestStreamWritesLogFile:
    """Verify JSONL written to copilot-sessions/."""

    @pytest.mark.usefixtures("_mock_copilot_deps")
    def test_stream_writes_log_file(
        self,
        _mock_copilot_deps: dict[str, Any],
        tmp_path: Any,
    ) -> None:
        log_file = tmp_path / "stream.ndjson"
        _mock_copilot_deps["mock_log_path"].return_value = log_file

        lines = [
            json.dumps({"type": "result", "sessionId": "s1"}),
        ]
        _mock_copilot_deps["mock_stream"].return_value = _make_mock_stream(lines)

        list(ask_copilot_cli_stream("test question"))

        assert log_file.exists()
        content = log_file.read_text(encoding="utf-8")
        assert lines[0] in content


class TestStreamInputValidation:
    """Validate input parameters."""

    def test_empty_question_raises(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            list(ask_copilot_cli_stream(""))

    def test_whitespace_question_raises(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            list(ask_copilot_cli_stream("   "))

    def test_zero_timeout_raises(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            list(ask_copilot_cli_stream("question", timeout=0))

    def test_negative_timeout_raises(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            list(ask_copilot_cli_stream("question", timeout=-1))
