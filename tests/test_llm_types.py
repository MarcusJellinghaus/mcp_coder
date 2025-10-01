"""Tests for LLM type definitions."""

import pytest

from mcp_coder.llm_types import LLM_RESPONSE_VERSION, LLMResponseDict


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
        "method": "cli",
        "provider": "claude",
        "raw_response": {"test": "data"},
    }

    assert response["version"] == "1.0"
    assert response["text"] == "Test response"
    assert response["method"] in ["cli", "api"]
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
        "method",
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
    assert hints["method"] == str
    assert hints["provider"] == str
    assert hints["raw_response"] == dict[str, object]


def test_llm_response_dict_none_session_id() -> None:
    """Test that LLMResponseDict accepts None for session_id."""
    response: LLMResponseDict = {
        "version": "1.0",
        "timestamp": "2025-10-01T10:30:00.123456",
        "text": "Test response without session",
        "session_id": None,
        "method": "api",
        "provider": "claude",
        "raw_response": {"usage": {"tokens": 100}},
    }

    assert response["session_id"] is None
    assert response["text"] == "Test response without session"
