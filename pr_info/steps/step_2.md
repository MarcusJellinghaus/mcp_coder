# Step 2: Implement Serialization Functions

## Context
Building on Step 1's type definitions, implement serialization and deserialization functions for storing and loading LLM responses. See `pr_info/steps/summary.md` for architectural overview.

## Objective
Create versioned JSON serialization/deserialization utilities that support future format evolution while maintaining backward compatibility.

## Changes Required

### WHERE: File Creation
**New File**: `src/mcp_coder/llm_serialization.py`

### WHAT: Main Functions

```python
def serialize_llm_response(response: LLMResponseDict, filepath: Path | str) -> None:
    """Serialize LLM response to JSON file with UTF-8 encoding."""

def deserialize_llm_response(filepath: Path | str) -> LLMResponseDict:
    """Deserialize LLM response from JSON file with version validation."""
```

### HOW: Integration Points

```python
# Import in modules that need serialization
from mcp_coder.llm_serialization import serialize_llm_response, deserialize_llm_response

# Usage
from mcp_coder.llm_types import LLMResponseDict
```

### ALGORITHM: Serialize

```python
def serialize_llm_response(response, filepath):
    # 1. Open file with UTF-8 encoding
    # 2. Dump response to JSON with indent=2
    # 3. Use ensure_ascii=False for Unicode support
    # 4. Use default=str for non-serializable types
    # 5. Close file automatically (context manager)
```

### ALGORITHM: Deserialize

```python
def deserialize_llm_response(filepath):
    # 1. Open file with UTF-8 encoding
    # 2. Load JSON data
    # 3. Check if version field exists
    # 4. Validate version starts with "1."
    # 5. Return data as-is (best effort, no field validation)
```

### DATA: Return Values

```python
# serialize_llm_response returns None (side effect: file written)
# deserialize_llm_response returns LLMResponseDict (may have missing fields)

# Raises:
# - ValueError: Version incompatible or missing
# - FileNotFoundError: File doesn't exist
# - json.JSONDecodeError: Invalid JSON
```

## Implementation

### File: `src/mcp_coder/llm_serialization.py`

```python
"""Serialization utilities for LLM responses.

This module provides functions to serialize and deserialize LLMResponseDict
objects to/from JSON files with versioning support for future compatibility.
"""

import json
from pathlib import Path

from .llm_types import LLMResponseDict

__all__ = [
    "serialize_llm_response",
    "deserialize_llm_response",
]


def serialize_llm_response(response: LLMResponseDict, filepath: Path | str) -> None:
    """Serialize LLM response to JSON file.
    
    Writes the LLM response to a JSON file with proper UTF-8 encoding and
    formatting. Handles non-serializable types by converting them to strings.
    
    Args:
        response: LLMResponseDict to serialize
        filepath: Path to save JSON file (will be created or overwritten)
        
    Raises:
        OSError: If file cannot be written (permissions, disk space, etc.)
        TypeError: If response contains truly unserializable data
        
    Example:
        >>> response = {
        ...     "version": "1.0",
        ...     "timestamp": "2025-10-01T10:30:00",
        ...     "text": "Response text",
        ...     "session_id": "abc-123",
        ...     "method": "cli",
        ...     "provider": "claude",
        ...     "raw_response": {"duration_ms": 2801}
        ... }
        >>> serialize_llm_response(response, "logs/abc-123.json")
    """
    filepath = Path(filepath)
    
    # Ensure parent directory exists
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(
            response,
            f,
            indent=2,
            ensure_ascii=False,  # Allow Unicode characters
            default=str  # Convert non-serializable types to strings
        )


def deserialize_llm_response(filepath: Path | str) -> LLMResponseDict:
    """Deserialize LLM response from JSON file.
    
    Loads an LLM response from a JSON file with version compatibility checking.
    Uses best-effort loading - returns whatever fields are present without
    strict validation.
    
    Args:
        filepath: Path to JSON file to load
        
    Returns:
        LLMResponseDict with available fields (may have missing fields)
        
    Raises:
        ValueError: If version is incompatible (not 1.x) or missing
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file contains invalid JSON
        
    Example:
        >>> response = deserialize_llm_response("logs/abc-123.json")
        >>> print(response["text"])
        >>> print(response["session_id"])
        
    Note:
        Only validates version compatibility. Missing or extra fields are
        allowed for flexibility and forward/backward compatibility.
    """
    filepath = Path(filepath)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Validate version compatibility
    version = data.get("version")
    if not version:
        raise ValueError(
            f"Missing 'version' field in {filepath}. "
            "This may not be a valid LLM response file."
        )
    
    if not isinstance(version, str) or not version.startswith("1."):
        raise ValueError(
            f"Incompatible version: {version}. Expected version 1.x "
            f"(found in {filepath}). "
            "This file may require a newer version of the software."
        )
    
    # Return data as-is (best effort - no strict field validation)
    return data  # type: ignore[return-value]
```

## Testing

### WHERE: Test File Creation
**New File**: `tests/test_llm_serialization.py`

### Test Cases

```python
"""Tests for LLM response serialization."""

import json
import pytest
from pathlib import Path
from mcp_coder.llm_serialization import (
    serialize_llm_response,
    deserialize_llm_response
)
from mcp_coder.llm_types import LLMResponseDict


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
        "raw_response": {
            "duration_ms": 2801,
            "cost_usd": 0.058
        }
    }


def test_serialize_creates_file(tmp_path, sample_response):
    """Test that serialize creates a JSON file."""
    filepath = tmp_path / "test.json"
    
    serialize_llm_response(sample_response, filepath)
    
    assert filepath.exists()
    assert filepath.is_file()


def test_serialize_creates_parent_directories(tmp_path, sample_response):
    """Test that serialize creates parent directories if needed."""
    filepath = tmp_path / "subdir" / "deep" / "test.json"
    
    serialize_llm_response(sample_response, filepath)
    
    assert filepath.exists()
    assert filepath.parent.exists()


def test_serialize_produces_valid_json(tmp_path, sample_response):
    """Test that serialized output is valid JSON."""
    filepath = tmp_path / "test.json"
    
    serialize_llm_response(sample_response, filepath)
    
    # Should not raise
    with open(filepath) as f:
        data = json.load(f)
    
    assert isinstance(data, dict)


def test_serialize_preserves_data(tmp_path, sample_response):
    """Test that all data is preserved in serialization."""
    filepath = tmp_path / "test.json"
    
    serialize_llm_response(sample_response, filepath)
    
    with open(filepath) as f:
        data = json.load(f)
    
    assert data["version"] == sample_response["version"]
    assert data["text"] == sample_response["text"]
    assert data["session_id"] == sample_response["session_id"]
    assert data["raw_response"] == sample_response["raw_response"]


def test_serialize_handles_unicode(tmp_path):
    """Test that Unicode characters are preserved."""
    response: LLMResponseDict = {
        "version": "1.0",
        "timestamp": "2025-10-01T10:30:00",
        "text": "Unicode test: 你好 🎉 café",
        "session_id": "abc-123",
        "method": "cli",
        "provider": "claude",
        "raw_response": {}
    }
    filepath = tmp_path / "unicode.json"
    
    serialize_llm_response(response, filepath)
    
    with open(filepath, encoding='utf-8') as f:
        data = json.load(f)
    
    assert data["text"] == "Unicode test: 你好 🎉 café"


def test_deserialize_loads_file(tmp_path, sample_response):
    """Test that deserialize loads a serialized file."""
    filepath = tmp_path / "test.json"
    serialize_llm_response(sample_response, filepath)
    
    loaded = deserialize_llm_response(filepath)
    
    assert loaded["version"] == sample_response["version"]
    assert loaded["text"] == sample_response["text"]
    assert loaded["session_id"] == sample_response["session_id"]


def test_deserialize_roundtrip(tmp_path, sample_response):
    """Test serialize -> deserialize roundtrip preserves data."""
    filepath = tmp_path / "roundtrip.json"
    
    serialize_llm_response(sample_response, filepath)
    loaded = deserialize_llm_response(filepath)
    
    assert loaded == sample_response


def test_deserialize_raises_on_missing_file(tmp_path):
    """Test that deserialize raises FileNotFoundError for missing files."""
    filepath = tmp_path / "nonexistent.json"
    
    with pytest.raises(FileNotFoundError):
        deserialize_llm_response(filepath)


def test_deserialize_raises_on_invalid_json(tmp_path):
    """Test that deserialize raises JSONDecodeError for invalid JSON."""
    filepath = tmp_path / "invalid.json"
    filepath.write_text("not valid json {{{")
    
    with pytest.raises(json.JSONDecodeError):
        deserialize_llm_response(filepath)


def test_deserialize_raises_on_missing_version(tmp_path):
    """Test that deserialize raises ValueError when version is missing."""
    filepath = tmp_path / "no_version.json"
    data = {"text": "test", "session_id": "abc"}
    
    with open(filepath, 'w') as f:
        json.dump(data, f)
    
    with pytest.raises(ValueError, match="Missing 'version' field"):
        deserialize_llm_response(filepath)


def test_deserialize_raises_on_incompatible_version(tmp_path):
    """Test that deserialize raises ValueError for incompatible versions."""
    filepath = tmp_path / "wrong_version.json"
    data = {"version": "2.0", "text": "test"}
    
    with open(filepath, 'w') as f:
        json.dump(data, f)
    
    with pytest.raises(ValueError, match="Incompatible version: 2.0"):
        deserialize_llm_response(filepath)


def test_deserialize_accepts_version_1_x(tmp_path):
    """Test that deserialize accepts any 1.x version."""
    for version in ["1.0", "1.1", "1.99"]:
        filepath = tmp_path / f"v{version.replace('.', '_')}.json"
        data = {
            "version": version,
            "text": "test",
            "session_id": "abc",
            "timestamp": "2025-10-01T10:30:00",
            "method": "cli",
            "provider": "claude",
            "raw_response": {}
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f)
        
        # Should not raise
        loaded = deserialize_llm_response(filepath)
        assert loaded["version"] == version


def test_deserialize_allows_missing_fields(tmp_path):
    """Test that deserialize doesn't validate field presence (best effort)."""
    filepath = tmp_path / "minimal.json"
    data = {
        "version": "1.0",
        "text": "minimal response"
        # Missing other fields - should still load
    }
    
    with open(filepath, 'w') as f:
        json.dump(data, f)
    
    # Should not raise - best effort loading
    loaded = deserialize_llm_response(filepath)
    assert loaded["version"] == "1.0"
    assert loaded["text"] == "minimal response"


def test_deserialize_allows_extra_fields(tmp_path):
    """Test that deserialize allows extra fields (forward compatibility)."""
    filepath = tmp_path / "extra.json"
    data = {
        "version": "1.0",
        "text": "test",
        "session_id": "abc",
        "timestamp": "2025-10-01T10:30:00",
        "method": "cli",
        "provider": "claude",
        "raw_response": {},
        "future_field": "new data"  # Extra field
    }
    
    with open(filepath, 'w') as f:
        json.dump(data, f)
    
    # Should not raise
    loaded = deserialize_llm_response(filepath)
    assert loaded["version"] == "1.0"
    assert "future_field" in loaded
```

## Validation Checklist

- [ ] `src/mcp_coder/llm_serialization.py` created
- [ ] Both functions implemented with complete docstrings
- [ ] Parent directory creation handled in serialize
- [ ] UTF-8 encoding used consistently
- [ ] Version validation in deserialize
- [ ] Best-effort loading (no strict field validation)
- [ ] `tests/test_llm_serialization.py` created
- [ ] All 16 test cases implemented
- [ ] All tests pass: `pytest tests/test_llm_serialization.py -v`
- [ ] Round-trip serialization preserves data
- [ ] Error cases properly handled

## LLM Prompt

```
I am implementing Step 2 of the LLM Session Management implementation plan.

Please review pr_info/steps/summary.md for architectural context and pr_info/steps/step_1.md for the type definitions created in the previous step.

For Step 2, I need to:
1. Create src/mcp_coder/llm_serialization.py with serialize_llm_response() and deserialize_llm_response() functions
2. Create tests/test_llm_serialization.py with comprehensive test coverage

Requirements from pr_info/steps/step_2.md:
- serialize_llm_response() writes JSON with UTF-8 encoding, creates parent directories
- deserialize_llm_response() validates version compatibility (must be 1.x)
- Best-effort loading - don't validate field presence, allow missing/extra fields
- Handle Unicode characters correctly
- Raise ValueError for version issues, FileNotFoundError for missing files
- Include complete docstrings with examples

Please implement following TDD principles with all 16 test cases passing.
```

## Dependencies
- **Requires**: Step 1 complete (`llm_types.py` with LLMResponseDict)

## Success Criteria
1. ✅ Serialization creates valid JSON files
2. ✅ Parent directories created automatically
3. ✅ Unicode characters preserved correctly
4. ✅ Deserialization validates version (1.x only)
5. ✅ Round-trip preserves all data
6. ✅ Best-effort loading allows missing/extra fields
7. ✅ Proper error handling for all edge cases
8. ✅ All 16 tests pass
9. ✅ Complete docstrings with examples
