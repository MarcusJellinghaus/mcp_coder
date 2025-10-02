"""Tests for LLM response serialization."""

import json
from pathlib import Path

import pytest

from mcp_coder.llm_serialization import (
    deserialize_llm_response,
    from_json_string,
    serialize_llm_response,
    to_json_string,
)
from mcp_coder.llm.types import LLMResponseDict


@pytest.fixture
def sample_response() -> LLMResponseDict:
    """Create a sample LLM response for testing."""
    return {
        "version": "1.0",
        "timestamp": "2025-10-01T10:30:00.123456",
        "text": "Test response",
        "session_id": "550e8400-e29b-41d4-a716-446655440000",
        "method": "cli",
        "provider": "claude",
        "raw_response": {"duration_ms": 2801, "cost_usd": 0.058},
    }


# ============================================================================
# PURE FUNCTION TESTS (fast, no I/O)
# ============================================================================


def test_to_json_string_produces_valid_json(sample_response: LLMResponseDict) -> None:
    """Test that to_json_string produces valid JSON."""
    json_str = to_json_string(sample_response)

    # Should be parseable
    data = json.loads(json_str)
    assert isinstance(data, dict)
    assert data == sample_response


def test_to_json_string_handles_unicode() -> None:
    """Test that Unicode characters are preserved."""
    response: LLMResponseDict = {
        "version": "1.0",
        "timestamp": "2025-10-01T10:30:00",
        "text": "Unicode: 你好 🎉 café",
        "session_id": "abc",
        "method": "cli",
        "provider": "claude",
        "raw_response": {},
    }

    json_str = to_json_string(response)
    data = json.loads(json_str)

    assert data["text"] == "Unicode: 你好 🎉 café"


def test_from_json_string_parses_valid_data(sample_response: LLMResponseDict) -> None:
    """Test that from_json_string parses valid JSON."""
    json_str = json.dumps(sample_response)

    result = from_json_string(json_str)

    assert result == sample_response


def test_from_json_string_raises_on_invalid_json() -> None:
    """Test that from_json_string raises JSONDecodeError for invalid JSON."""
    invalid_json = "not valid json {{{"

    with pytest.raises(json.JSONDecodeError):
        from_json_string(invalid_json)


def test_from_json_string_raises_on_missing_version() -> None:
    """Test that from_json_string raises ValueError when version missing."""
    data = {"text": "test", "session_id": "abc"}
    json_str = json.dumps(data)

    with pytest.raises(ValueError, match="Missing 'version' field"):
        from_json_string(json_str)


def test_from_json_string_raises_on_incompatible_version() -> None:
    """Test that from_json_string raises ValueError for bad version."""
    data = {"version": "2.0", "text": "test"}
    json_str = json.dumps(data)

    with pytest.raises(ValueError, match="Incompatible version: 2.0"):
        from_json_string(json_str)


def test_json_string_roundtrip(sample_response: LLMResponseDict) -> None:
    """Test to_json_string -> from_json_string preserves data."""
    json_str = to_json_string(sample_response)
    result = from_json_string(json_str)

    assert result == sample_response


# ============================================================================
# I/O WRAPPER TESTS (minimal, test file operations only)
# ============================================================================


def test_serialize_creates_file_and_directories(
    tmp_path: Path, sample_response: LLMResponseDict
) -> None:
    """Test that serialize creates file with parent directories."""
    filepath = tmp_path / "subdir" / "deep" / "test.json"

    serialize_llm_response(sample_response, filepath)

    assert filepath.exists()
    assert filepath.is_file()


def test_deserialize_file_roundtrip(
    tmp_path: Path, sample_response: LLMResponseDict
) -> None:
    """Test serialize -> deserialize file roundtrip."""
    filepath = tmp_path / "roundtrip.json"

    serialize_llm_response(sample_response, filepath)
    loaded = deserialize_llm_response(filepath)

    assert loaded == sample_response
