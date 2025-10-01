# Step 1: Define LLM Response Types and Constants

## Context
This is the foundation step that establishes type definitions and constants for the LLM session management and serialization system. See `pr_info/steps/summary.md` for complete architectural overview.

## Objective
Create TypedDict definitions and version constants to support structured LLM responses with session management and serialization.

## Changes Required

### WHERE: File Creation
**New File**: `src/mcp_coder/llm_types.py`

### WHAT: Type Definitions

#### Main Types
```python
class LLMResponseDict(TypedDict):
    """Structured LLM response with session and serialization support."""
    version: str           # Serializer version (e.g., "1.0")
    timestamp: str         # ISO format timestamp
    text: str              # The response text
    session_id: str | None # Session ID for continuation (None if unavailable)
    method: str            # "cli" or "api"
    provider: str          # "claude"
    raw_response: dict     # Complete unmodified CLI JSON or API response
```

#### Constants
```python
LLM_RESPONSE_VERSION = "1.0"  # Current serialization version
```

### HOW: Integration Points
```python
# Import in other modules
from mcp_coder.llm_types import LLMResponseDict, LLM_RESPONSE_VERSION

# Usage in function signatures
def prompt_llm(...) -> LLMResponseDict:
    ...
```

### ALGORITHM: None Required
This step only defines types and constants.

### DATA: Type Structure
```python
LLMResponseDict = {
    "version": "1.0",
    "timestamp": "2025-10-01T10:30:00.123456",
    "text": "Response from LLM",
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "method": "cli",
    "provider": "claude",
    "raw_response": {...}  # Complete CLI/API response
}
```

## Implementation

### File: `src/mcp_coder/llm_types.py`

```python
"""Type definitions for LLM responses and serialization.

This module provides TypedDict definitions and constants for structured
LLM responses with session management and versioned serialization support.
"""

from typing import TypedDict

__all__ = [
    "LLMResponseDict",
    "LLM_RESPONSE_VERSION",
]


class LLMResponseDict(TypedDict):
    """Structured LLM response with session and serialization support.
    
    This TypedDict defines the complete structure for LLM responses that include
    session management, timestamps, and raw response data for comprehensive logging.
    
    Attributes:
        version: Serialization format version (e.g., "1.0")
        timestamp: ISO format timestamp when response was created
        text: The actual text response from the LLM
        session_id: Unique session identifier for conversation continuity.
                   None if session ID is not available or not provided by LLM.
        method: LLM communication method ("cli" or "api")
        provider: LLM provider name (e.g., "claude")
        raw_response: Complete unmodified response data from CLI JSON or API
                     This preserves all metadata, usage stats, and provider-specific
                     information for future analysis and parsing
    
    Example:
        {
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00.123456",
            "text": "Python is a programming language...",
            "session_id": "550e8400-e29b-41d4-a716-446655440000",
            "method": "cli",
            "provider": "claude",
            "raw_response": {
                "duration_ms": 2801,
                "cost_usd": 0.058,
                ...
            }
        }
    """
    
    version: str
    timestamp: str
    text: str
    session_id: str | None
    method: str
    provider: str
    raw_response: dict


# Current serialization version
# Version numbering:
# - Major version (X.0): Breaking changes to structure
# - Minor version (1.X): Backward-compatible additions
LLM_RESPONSE_VERSION = "1.0"
```

## Testing

### WHERE: Test File Creation
**New File**: `tests/test_llm_types.py`

### Test Cases

```python
"""Tests for LLM type definitions."""

import pytest
from mcp_coder.llm_types import LLMResponseDict, LLM_RESPONSE_VERSION


def test_llm_response_version_format():
    """Test that LLM_RESPONSE_VERSION follows semantic versioning."""
    assert isinstance(LLM_RESPONSE_VERSION, str)
    assert "." in LLM_RESPONSE_VERSION
    parts = LLM_RESPONSE_VERSION.split(".")
    assert len(parts) == 2
    assert parts[0].isdigit()
    assert parts[1].isdigit()


def test_llm_response_dict_structure():
    """Test that LLMResponseDict can be instantiated with correct fields."""
    response: LLMResponseDict = {
        "version": "1.0",
        "timestamp": "2025-10-01T10:30:00.123456",
        "text": "Test response",
        "session_id": "550e8400-e29b-41d4-a716-446655440000",
        "method": "cli",
        "provider": "claude",
        "raw_response": {"test": "data"}
    }
    
    assert response["version"] == "1.0"
    assert response["text"] == "Test response"
    assert response["method"] in ["cli", "api"]
    assert response["provider"] == "claude"
    assert isinstance(response["raw_response"], dict)


def test_llm_response_dict_required_fields():
    """Test that all required fields are present in type definition."""
    from typing import get_type_hints
    
    hints = get_type_hints(LLMResponseDict)
    required_fields = {
        "version", "timestamp", "text", "session_id", 
        "method", "provider", "raw_response"
    }
    
    assert set(hints.keys()) == required_fields


def test_llm_response_dict_field_types():
    """Test that field types are correct."""
    from typing import get_type_hints
    
    hints = get_type_hints(LLMResponseDict)
    
    assert hints["version"] == str
    assert hints["timestamp"] == str
    assert hints["text"] == str
    # session_id is str | None (Optional[str])
    import typing
    assert hints["session_id"] == str | None or hints["session_id"] == typing.Union[str, None]
    assert hints["method"] == str
    assert hints["provider"] == str
    assert hints["raw_response"] == dict
```

## Validation Checklist

- [ ] `src/mcp_coder/llm_types.py` created with TypedDict definition
- [ ] `LLM_RESPONSE_VERSION` constant defined as "1.0"
- [ ] All required fields present in LLMResponseDict
- [ ] Complete docstrings with examples
- [ ] `tests/test_llm_types.py` created with test cases
- [ ] All tests pass: `pytest tests/test_llm_types.py -v`
- [ ] Type hints validate correctly
- [ ] Module imports successfully

## LLM Prompt

```
I am implementing Step 1 of the LLM Session Management implementation plan.

Please review pr_info/steps/summary.md for the complete architectural overview.

For Step 1, I need to:
1. Create src/mcp_coder/llm_types.py with LLMResponseDict TypedDict and LLM_RESPONSE_VERSION constant
2. Create tests/test_llm_types.py with comprehensive tests

Requirements:
- Follow the exact structure specified in pr_info/steps/step_1.md
- LLMResponseDict must have 7 fields: version, timestamp, text, session_id, method, provider, raw_response
- LLM_RESPONSE_VERSION should be "1.0"
- Include complete docstrings with examples
- All tests must pass

Please implement these files following TDD principles and best practices.
```

## Dependencies
- None (foundation step)

## Success Criteria
1. ✅ TypedDict properly defines all 7 required fields
2. ✅ Version constant set to "1.0"
3. ✅ Complete docstrings with usage examples
4. ✅ All type validation tests pass
5. ✅ Module can be imported without errors
6. ✅ Code follows project style guidelines
