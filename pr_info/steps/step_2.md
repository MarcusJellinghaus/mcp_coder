# Step 2: Implement Serialization Functions

## Context
Building on Step 1's type definitions, implement serialization and deserialization functions for storing and loading LLM responses. See `pr_info/steps/summary.md` for architectural overview.

## Objective
Create versioned JSON serialization/deserialization utilities that support future format evolution while maintaining backward compatibility.

## Changes Required

### WHERE: File Creation
**New File**: `src/mcp_coder/llm_serialization.py`

### WHAT: Functions

**Pure Functions** (testable without I/O):
```python
def to_json_string(response: LLMResponseDict) -> str:
    """Convert LLMResponseDict to JSON string (pure function)."""

def from_json_string(json_str: str) -> LLMResponseDict:
    """Parse JSON string and validate version (pure function)."""
```

**I/O Wrappers** (thin delegation layer):
```python
def serialize_llm_response(response: LLMResponseDict, filepath: Path | str) -> None:
    """Write LLM response to JSON file."""

def deserialize_llm_response(filepath: Path | str) -> LLMResponseDict:
    """Load LLM response from JSON file."""
```

### HOW: Integration Points

```python
# Import in modules that need serialization
from mcp_coder.llm_serialization import serialize_llm_response, deserialize_llm_response

# Usage
from mcp_coder.llm_types import LLMResponseDict
```

### ALGORITHM: Pure Functions

```python
def to_json_string(response):
    # 1. Use json.dumps() with formatting options
    # 2. indent=2 for readability
    # 3. ensure_ascii=False for Unicode
    # 4. default=str for non-serializable types
    # 5. Return JSON string

def from_json_string(json_str):
    # 1. Parse JSON string with json.loads()
    # 2. Check if version field exists
    # 3. Validate version starts with "1."
    # 4. Return data as-is (best effort)
```

### ALGORITHM: I/O Wrappers

```python
def serialize_llm_response(response, filepath):
    # 1. Ensure parent directory exists
    # 2. Call to_json_string() to get JSON
    # 3. Write to file with UTF-8 encoding

def deserialize_llm_response(filepath):
    # 1. Read file content with UTF-8 encoding
    # 2. Call from_json_string() to parse and validate
    # 3. Return result
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
    "to_json_string",
    "from_json_string",
    "serialize_llm_response",
    "deserialize_llm_response",
]

# Note: All four functions are exported (including pure functions)
# to allow advanced users to use them directly for custom workflows


def to_json_string(response: LLMResponseDict) -> str:
    """Convert LLMResponseDict to JSON string (pure function).
    
    This pure function handles serialization logic without file I/O,
    making it easy to test and reuse.
    
    Args:
        response: LLMResponseDict to convert to JSON
        
    Returns:
        Formatted JSON string with proper encoding
        
    Example:
        >>> response = {"version": "1.0", "text": "Hello", ...}
        >>> json_str = to_json_string(response)
        >>> print(json_str)
    """
    return json.dumps(
        response,
        indent=2,
        ensure_ascii=False,  # Allow Unicode characters
        default=str  # Convert non-serializable types to strings
    )


def from_json_string(json_str: str) -> LLMResponseDict:
    """Parse JSON string and validate version (pure function).
    
    This pure function handles deserialization and validation logic
    without file I/O, making it easy to test.
    
    Args:
        json_str: JSON string to parse
        
    Returns:
        LLMResponseDict with available fields
        
    Raises:
        ValueError: If version is incompatible or missing
        json.JSONDecodeError: If JSON is invalid
        
    Example:
        >>> json_str = '{"version": "1.0", "text": "Hello", ...}'
        >>> response = from_json_string(json_str)
    """
    data = json.loads(json_str)
    
    # Validate version compatibility
    version = data.get("version")
    if not version:
        raise ValueError(
            "Missing 'version' field. "
            "This may not be a valid LLM response."
        )
    
    if not isinstance(version, str) or not version.startswith("1."):
        raise ValueError(
            f"Incompatible version: {version}. Expected version 1.x. "
            "This may require a newer version of the software."
        )
    
    # Return data as-is (best effort - no strict field validation)
    return data  # type: ignore[return-value]


def serialize_llm_response(response: LLMResponseDict, filepath: Path | str) -> None:
    """Write LLM response to JSON file (I/O wrapper).
    
    Thin wrapper that handles file I/O, delegating serialization logic
    to the pure to_json_string() function.
    
    Args:
        response: LLMResponseDict to serialize
        filepath: Path to save JSON file (will be created or overwritten)
        
    Raises:
        OSError: If file cannot be written (permissions, disk space, etc.)
        
    Example:
        >>> response = {"version": "1.0", "text": "Hello", ...}
        >>> serialize_llm_response(response, "logs/abc-123.json")
    """
    filepath = Path(filepath)
    
    # Ensure parent directory exists
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    # Use pure function for serialization
    json_str = to_json_string(response)
    
    # Write to file
    filepath.write_text(json_str, encoding='utf-8')


def deserialize_llm_response(filepath: Path | str) -> LLMResponseDict:
    """Load LLM response from JSON file (I/O wrapper).
    
    Thin wrapper that handles file I/O, delegating parsing and validation
    logic to the pure from_json_string() function.
    
    Args:
        filepath: Path to JSON file to load
        
    Returns:
        LLMResponseDict with available fields
        
    Raises:
        ValueError: If version is incompatible or missing
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file contains invalid JSON
        
    Example:
        >>> response = deserialize_llm_response("logs/abc-123.json")
        >>> print(response["text"])
    """
    filepath = Path(filepath)
    
    # Read file content
    json_str = filepath.read_text(encoding='utf-8')
    
    # Use pure function for parsing and validation
    return from_json_string(json_str)
```

## Testing

### WHERE: Test File Creation
**New File**: `tests/test_llm_serialization.py`

### Test Cases

**Test Structure:**
- **Pure function tests** (~6 tests): Fast, no I/O, test serialization/parsing logic
- **I/O wrapper tests** (~2 tests): Minimal, test file operations only
- **Total: ~8 tests** (reduced from 16 via separation of concerns)

```python
"""Tests for LLM response serialization."""

import json
import pytest
from pathlib import Path
from mcp_coder.llm_serialization import (
    to_json_string,
    from_json_string,
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
        "raw_response": {"duration_ms": 2801, "cost_usd": 0.058}
    }


# ============================================================================
# PURE FUNCTION TESTS (fast, no I/O)
# ============================================================================

def test_to_json_string_produces_valid_json(sample_response):
    """Test that to_json_string produces valid JSON."""
    json_str = to_json_string(sample_response)
    
    # Should be parseable
    data = json.loads(json_str)
    assert isinstance(data, dict)
    assert data == sample_response


def test_to_json_string_handles_unicode():
    """Test that Unicode characters are preserved."""
    response: LLMResponseDict = {
        "version": "1.0",
        "timestamp": "2025-10-01T10:30:00",
        "text": "Unicode: 你好 🎉 café",
        "session_id": "abc",
        "method": "cli",
        "provider": "claude",
        "raw_response": {}
    }
    
    json_str = to_json_string(response)
    data = json.loads(json_str)
    
    assert data["text"] == "Unicode: 你好 🎉 café"


def test_from_json_string_parses_valid_data(sample_response):
    """Test that from_json_string parses valid JSON."""
    json_str = json.dumps(sample_response)
    
    result = from_json_string(json_str)
    
    assert result == sample_response


def test_from_json_string_raises_on_invalid_json():
    """Test that from_json_string raises JSONDecodeError for invalid JSON."""
    invalid_json = "not valid json {{{"
    
    with pytest.raises(json.JSONDecodeError):
        from_json_string(invalid_json)


def test_from_json_string_raises_on_missing_version():
    """Test that from_json_string raises ValueError when version missing."""
    data = {"text": "test", "session_id": "abc"}
    json_str = json.dumps(data)
    
    with pytest.raises(ValueError, match="Missing 'version' field"):
        from_json_string(json_str)


def test_from_json_string_raises_on_incompatible_version():
    """Test that from_json_string raises ValueError for bad version."""
    data = {"version": "2.0", "text": "test"}
    json_str = json.dumps(data)
    
    with pytest.raises(ValueError, match="Incompatible version: 2.0"):
        from_json_string(json_str)


def test_json_string_roundtrip(sample_response):
    """Test to_json_string -> from_json_string preserves data."""
    json_str = to_json_string(sample_response)
    result = from_json_string(json_str)
    
    assert result == sample_response


# ============================================================================
# I/O WRAPPER TESTS (minimal, test file operations only)
# ============================================================================

def test_serialize_creates_file_and_directories(tmp_path, sample_response):
    """Test that serialize creates file with parent directories."""
    filepath = tmp_path / "subdir" / "deep" / "test.json"
    
    serialize_llm_response(sample_response, filepath)
    
    assert filepath.exists()
    assert filepath.is_file()


def test_deserialize_file_roundtrip(tmp_path, sample_response):
    """Test serialize -> deserialize file roundtrip."""
    filepath = tmp_path / "roundtrip.json"
    
    serialize_llm_response(sample_response, filepath)
    loaded = deserialize_llm_response(filepath)
    
    assert loaded == sample_response
```

## Validation Checklist

- [ ] `src/mcp_coder/llm_serialization.py` created
- [ ] Pure functions implemented: `to_json_string()`, `from_json_string()`
- [ ] I/O wrappers implemented: `serialize_llm_response()`, `deserialize_llm_response()`
- [ ] All functions have complete docstrings
- [ ] Parent directory creation handled
- [ ] UTF-8 encoding used consistently
- [ ] Version validation in `from_json_string()`
- [ ] `tests/test_llm_serialization.py` created
- [ ] ~8 test cases implemented (6 pure function + 2 I/O wrapper)
- [ ] All tests pass: `pytest tests/test_llm_serialization.py -v`
- [ ] Round-trip preserves data (both string and file)
- [ ] Error cases properly handled

## LLM Prompt

```
I am implementing Step 2 of the LLM Session Management implementation plan.

Please review:
- pr_info/steps/summary.md for architectural context
- pr_info/steps/step_1.md for LLMResponseDict type definition
- pr_info/steps/decisions.md for architecture decisions

For Step 2, I need to:
1. Create src/mcp_coder/llm_serialization.py with pure functions and I/O wrappers
2. Create tests/test_llm_serialization.py with ~8 test cases

Architecture (separation of concerns):
- Pure functions: to_json_string(), from_json_string() - testable without I/O
- I/O wrappers: serialize_llm_response(), deserialize_llm_response() - thin delegation

Requirements from pr_info/steps/step_2.md:
- to_json_string(): Convert dict to JSON string with proper formatting
- from_json_string(): Parse JSON and validate version (must be 1.x)
- serialize_llm_response(): Create directories, write file using to_json_string()
- deserialize_llm_response(): Read file, parse using from_json_string()
- Handle Unicode correctly, raise ValueError for version issues

Please implement following TDD with ~8 test cases (6 pure function + 2 I/O wrapper).
```

## Dependencies
- **Requires**: Step 1 complete (`llm_types.py` with LLMResponseDict)

## Success Criteria
1. ✅ Pure functions (to_json_string, from_json_string) implemented
2. ✅ I/O wrappers delegate to pure functions
3. ✅ Serialization creates valid JSON files
4. ✅ Parent directories created automatically
5. ✅ Unicode characters preserved correctly
6. ✅ Version validation (1.x only) in from_json_string()
7. ✅ Round-trip preserves all data (both string and file)
8. ✅ Proper error handling for edge cases
9. ✅ All ~8 tests pass (6 pure + 2 I/O)
10. ✅ Complete docstrings with examples
