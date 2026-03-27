"""Tests for LLM type definitions."""

import pytest

from mcp_coder.llm.types import (
    LLM_RESPONSE_VERSION,
    LLMResponseDict,
    ResponseAssembler,
    StreamEvent,
)


def test_llm_response_version_format() -> None:
    """Test that LLM_RESPONSE_VERSION follows semantic versioning."""
    assert isinstance(LLM_RESPONSE_VERSION, str)
    assert "." in LLM_RESPONSE_VERSION
    parts = LLM_RESPONSE_VERSION.split(".")
    assert len(parts) == 2
    assert parts[0].isdigit()
    assert parts[1].isdigit()


def test_llm_response_dict_structure() -> None:
    """Test that LLMResponseDict can be instantiated with correct fields."""
    response: LLMResponseDict = {
        "version": "1.0",
        "timestamp": "2025-10-01T10:30:00.123456",
        "text": "Test response",
        "session_id": "550e8400-e29b-41d4-a716-446655440000",
        "provider": "claude",
        "raw_response": {"test": "data"},
    }

    assert response["version"] == "1.0"
    assert response["text"] == "Test response"
    assert response["provider"] == "claude"
    assert isinstance(response["raw_response"], dict)


def test_llm_response_dict_required_fields() -> None:
    """Test that all required fields are present in type definition."""
    from typing import get_type_hints

    hints = get_type_hints(LLMResponseDict)
    required_fields = {
        "version",
        "timestamp",
        "text",
        "session_id",
        "provider",
        "raw_response",
    }

    assert set(hints.keys()) == required_fields


def test_llm_response_dict_field_types() -> None:
    """Test that field types are correct."""
    import typing
    from typing import get_type_hints

    hints = get_type_hints(LLMResponseDict)

    assert hints["version"] == str
    assert hints["timestamp"] == str
    assert hints["text"] == str
    # session_id is str | None (Optional[str])
    assert (
        hints["session_id"] == str | None
        or hints["session_id"] == typing.Union[str, None]
    )
    assert hints["provider"] == str
    assert hints["raw_response"] == dict[str, object]


def test_llm_response_dict_none_session_id() -> None:
    """Test that LLMResponseDict accepts None for session_id."""
    response: LLMResponseDict = {
        "version": "1.0",
        "timestamp": "2025-10-01T10:30:00.123456",
        "text": "Test response without session",
        "session_id": None,
        "provider": "claude",
        "raw_response": {"usage": {"tokens": 100}},
    }

    assert response["session_id"] is None
    assert response["text"] == "Test response without session"


# --- StreamEvent tests ---


def test_stream_event_type_alias() -> None:
    """Verify StreamEvent is dict[str, object]."""
    assert StreamEvent == dict[str, object]
    # A StreamEvent should be usable as a plain dict
    event: StreamEvent = {"type": "text_delta", "text": "hello"}
    assert event["type"] == "text_delta"


# --- ResponseAssembler tests ---


def test_response_assembler_text_delta() -> None:
    """Feed text_delta events, verify assembled text."""
    assembler = ResponseAssembler(provider="claude")
    assembler.add({"type": "text_delta", "text": "Hello"})
    assembler.add({"type": "text_delta", "text": " world"})
    result = assembler.result()
    assert result["text"] == "Hello world"


def test_response_assembler_done_event() -> None:
    """Feed done event with usage/session_id, verify result."""
    assembler = ResponseAssembler(provider="claude")
    assembler.add({"type": "text_delta", "text": "Hi"})
    assembler.add(
        {
            "type": "done",
            "usage": {"input_tokens": 100, "output_tokens": 50},
            "session_id": "abc123",
        }
    )
    result = assembler.result()
    assert result["text"] == "Hi"
    assert result["session_id"] == "abc123"
    assert result["raw_response"]["usage"] == {
        "input_tokens": 100,
        "output_tokens": 50,
    }


def test_response_assembler_error_event() -> None:
    """Feed error event, verify error in raw_response."""
    assembler = ResponseAssembler(provider="claude")
    assembler.add({"type": "error", "message": "Connection reset"})
    result = assembler.result()
    assert result["raw_response"]["error"] == "Connection reset"


def test_response_assembler_tool_events() -> None:
    """Feed tool_use_start + tool_result, verify in raw_response events."""
    assembler = ResponseAssembler(provider="langchain")
    assembler.add({"type": "tool_use_start", "name": "sleep", "args": {"seconds": 2}})
    assembler.add({"type": "tool_result", "name": "sleep", "output": "done"})
    result = assembler.result()
    events = result["raw_response"]["events"]
    assert isinstance(events, list)
    assert len(events) == 2
    assert events[0]["type"] == "tool_use_start"
    assert events[1]["type"] == "tool_result"


def test_response_assembler_empty() -> None:
    """No events, result has empty text and None session_id."""
    assembler = ResponseAssembler(provider="claude")
    result = assembler.result()
    assert result["text"] == ""
    assert result["session_id"] is None
    assert result["version"] == LLM_RESPONSE_VERSION


def test_response_assembler_provider() -> None:
    """Verify provider field matches constructor arg."""
    assembler = ResponseAssembler(provider="langchain")
    result = assembler.result()
    assert result["provider"] == "langchain"


# --- ResponseAssembler tool_trace tests ---


class TestResponseAssemblerToolTrace:
    """ResponseAssembler accumulates tool events into tool_trace."""

    def test_tool_use_start_accumulated(self) -> None:
        """tool_use_start events appear in tool_trace."""
        assembler = ResponseAssembler(provider="langchain")
        assembler.add(
            {
                "type": "tool_use_start",
                "name": "read_file",
                "args": {"path": "x.py"},
                "tool_call_id": "tc_1",
            }
        )
        result = assembler.result()
        assert result["raw_response"]["tool_trace"] == [
            {
                "type": "tool_use_start",
                "name": "read_file",
                "args": {"path": "x.py"},
                "tool_call_id": "tc_1",
            }
        ]

    def test_tool_result_accumulated(self) -> None:
        """tool_result events appear in tool_trace."""
        assembler = ResponseAssembler(provider="langchain")
        assembler.add(
            {
                "type": "tool_result",
                "name": "read_file",
                "output": "content",
                "tool_call_id": "tc_1",
            }
        )
        result = assembler.result()
        assert result["raw_response"]["tool_trace"] == [
            {
                "type": "tool_result",
                "name": "read_file",
                "output": "content",
                "tool_call_id": "tc_1",
            }
        ]

    def test_full_tool_cycle_in_order(self) -> None:
        """tool_use_start + tool_result accumulate in order."""
        assembler = ResponseAssembler(provider="langchain")
        assembler.add(
            {
                "type": "tool_use_start",
                "name": "sleep",
                "args": {"s": 1},
                "tool_call_id": "tc_1",
            }
        )
        assembler.add(
            {
                "type": "tool_result",
                "name": "sleep",
                "output": "ok",
                "tool_call_id": "tc_1",
            }
        )
        result = assembler.result()
        trace = result["raw_response"]["tool_trace"]
        assert isinstance(trace, list)
        assert len(trace) == 2
        assert trace[0]["type"] == "tool_use_start"
        assert trace[1]["type"] == "tool_result"

    def test_empty_tool_trace_not_in_result(self) -> None:
        """When no tool events, tool_trace key is absent from raw_response."""
        assembler = ResponseAssembler(provider="langchain")
        assembler.add({"type": "text_delta", "text": "hi"})
        assembler.add({"type": "done", "session_id": "s1", "usage": {}})
        result = assembler.result()
        assert "tool_trace" not in result["raw_response"]

    def test_tool_trace_with_text_deltas(self) -> None:
        """Tool events interleaved with text still accumulate correctly."""
        assembler = ResponseAssembler(provider="langchain")
        assembler.add({"type": "text_delta", "text": "thinking..."})
        assembler.add(
            {
                "type": "tool_use_start",
                "name": "run",
                "args": {},
                "tool_call_id": "tc_1",
            }
        )
        assembler.add(
            {
                "type": "tool_result",
                "name": "run",
                "output": "done",
                "tool_call_id": "tc_1",
            }
        )
        assembler.add({"type": "text_delta", "text": "Result is done."})
        result = assembler.result()
        assert result["text"] == "thinking...Result is done."
        tool_trace = result["raw_response"]["tool_trace"]
        assert isinstance(tool_trace, list)
        assert len(tool_trace) == 2
