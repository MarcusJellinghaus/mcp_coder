# Step 4: Add Session Support to API Method

## Context
Modify `ask_claude_code_api()` and related functions to support session management and return TypedDict. See `pr_info/steps/summary.md` for architectural overview.

## Objective
Simplify API session support by leveraging existing `ask_claude_code_api_detailed_sync()` function, which already extracts session information.

**Note:** This step uses fewer helper functions compared to Step 3 because we're reusing existing infrastructure (per `decisions.md` Decision 6). The existing `ask_claude_code_api_detailed_sync()` already handles the heavy lifting of session extraction and metadata collection.

## Changes Required

### WHERE: File Modification
**File**: `src/mcp_coder/llm_providers/claude/claude_code_api.py`

### WHAT: Function Changes

**Strategy**: Leverage existing `ask_claude_code_api_detailed_sync()` which already:
- Extracts session_id from SystemMessage
- Returns structured data with session_info, result_info, raw_messages
- Supports ClaudeCodeOptions with resume parameter

**Modified Function Signature**:
```python
def ask_claude_code_api(
    question: str,
    session_id: str | None = None,  # NEW: For session continuity
    timeout: int = 30
) -> LLMResponseDict:  # CHANGED: was str
```

### HOW: Integration Points

```python
# Add imports at top
from ...llm_types import LLMResponseDict, LLM_RESPONSE_VERSION

# Use ClaudeCodeOptions with resume parameter
options = ClaudeCodeOptions(
    resume=session_id  # Pass session_id for continuation
)
```

### ALGORITHM: Simplified API Implementation

```python
def ask_claude_code_api(question, session_id, timeout):
    # 1. Create ClaudeCodeOptions with resume=session_id if provided
    # 2. Call ask_claude_code_api_detailed_sync() (does the heavy lifting)
    # 3. Extract session_id from detailed["session_info"]["session_id"]
    # 4. Build LLMResponseDict using create_response_dict() helper
    # 5. Return structured response
```

### DATA: Return Value Structure

```python
{
    "version": "1.0",
    "timestamp": "2025-10-01T10:30:00.123456",
    "text": "Response text from AssistantMessage",
    "session_id": "extracted-from-system-or-result-message",
    "method": "api",
    "provider": "claude",
    "raw_response": {
        "session_info": {...},
        "result_info": {...},
        "raw_messages": [...]
    }
}
```

## Implementation

### File: `src/mcp_coder/llm_providers/claude/claude_code_api.py`

**Modifications**:

1. **Add imports at top**:
```python
from datetime import datetime
from ...llm_types import LLMResponseDict, LLM_RESPONSE_VERSION
```

2. **Add helper function for response creation**:
```python
def create_api_response_dict(text: str, session_id: str | None, detailed_response: dict) -> LLMResponseDict:
    """Create LLMResponseDict from API detailed response.
    
    Args:
        text: Extracted response text
        session_id: Session ID from session_info
        detailed_response: Complete response from ask_claude_code_api_detailed_sync()
        
    Returns:
        Complete LLMResponseDict
    """
    return {
        "version": LLM_RESPONSE_VERSION,
        "timestamp": datetime.now().isoformat(),
        "text": text,
        "session_id": session_id,
        "method": "api",
        "provider": "claude",
        "raw_response": {
            "session_info": detailed_response["session_info"],
            "result_info": detailed_response["result_info"],
            "raw_messages": detailed_response["raw_messages"],
        }
    }
```

3. **Modify `ask_claude_code_api` function**:
```python
def ask_claude_code_api(
    question: str,
    session_id: str | None = None,
    timeout: int = 30
) -> LLMResponseDict:
    """Ask Claude via API and return structured response.
    
    Leverages existing ask_claude_code_api_detailed_sync() which handles
    session extraction and metadata collection.
    
    Args:
        question: The question to ask Claude
        session_id: Optional session ID to resume conversation
        timeout: Timeout in seconds (default: 30)
        
    Returns:
        LLMResponseDict with complete response data
        
    Raises:
        ValueError: If input validation fails
        subprocess.TimeoutExpired: If request times out
        subprocess.CalledProcessError: If request fails
        
    Examples:
        >>> result = ask_claude_code_api("What is Python?")
        >>> print(result["text"])
        >>> session_id = result["session_id"]
        
        >>> result2 = ask_claude_code_api("Tell me more", session_id=session_id)
    """
    # Input validation
    if not question or not question.strip():
        raise ValueError("Question cannot be empty or whitespace only")
    if timeout <= 0:
        raise ValueError("Timeout must be a positive number")
    
    # Create options with session resume if provided
    # Note: This modifies _create_claude_client() to accept resume parameter
    # or we pass it through ask_claude_code_api_detailed_sync if it supports it
    
    # Call detailed function (already extracts everything we need)
    detailed = ask_claude_code_api_detailed_sync(question, timeout)
    
    # Extract session_id from session_info
    session_id_result = detailed["session_info"].get("session_id")
    
    # Build and return response
    return create_api_response_dict(
        detailed["text"],
        session_id_result,
        detailed
    )
```

**Note**: If `ask_claude_code_api_detailed_sync()` needs session_id parameter added,
modify its signature to accept it and pass through to `_create_claude_client()`
with `ClaudeCodeOptions(resume=session_id)`.

## Testing

### WHERE: Test File Modification
**File**: `tests/llm_providers/claude/test_claude_code_api.py` (existing file)

### Test Cases

**Test Structure:**
- **Helper function test** (~1 test): Test response dict creation
- **Integration tests** (~2 tests): Test full API workflow
- **Total: ~3 tests** (simplified by using existing detailed function)

```python
"""Tests for API session support."""

import pytest
from mcp_coder.llm_providers.claude.claude_code_api import (
    create_api_response_dict,
    ask_claude_code_api
)
from mcp_coder.llm_types import LLMResponseDict


def test_create_api_response_dict_structure():
    """Test API response dict creation."""
    detailed = {
        "text": "API response",
        "session_info": {"session_id": "api-123", "model": "claude-sonnet-4"},
        "result_info": {"cost_usd": 0.058, "duration_ms": 2801},
        "raw_messages": []
    }
    
    result = create_api_response_dict("API response", "api-123", detailed)
    
    assert result["text"] == "API response"
    assert result["session_id"] == "api-123"
    assert result["method"] == "api"
    assert result["provider"] == "claude"
    assert "version" in result
    assert "timestamp" in result
    assert result["raw_response"]["session_info"]["session_id"] == "api-123"


def test_ask_claude_code_api_returns_typed_dict(mock_claude_api):
    """Test that API method returns complete LLMResponseDict."""
    mock_claude_api.set_detailed_response({
        "text": "Test response",
        "session_info": {"session_id": "test-123"},
        "result_info": {},
        "raw_messages": []
    })
    
    result = ask_claude_code_api("Test question")
    
    # Check all required fields
    assert isinstance(result, dict)
    for field in ["version", "timestamp", "text", "session_id", "method", "provider", "raw_response"]:
        assert field in result


def test_ask_claude_code_api_extracts_session_from_detailed(mock_claude_api):
    """Test session_id extraction from detailed response."""
    mock_claude_api.set_detailed_response({
        "text": "Response text",
        "session_info": {"session_id": "extracted-session", "model": "claude"},
        "result_info": {"cost_usd": 0.05},
        "raw_messages": []
    })
    
    result = ask_claude_code_api("Test")
    
    assert result["session_id"] == "extracted-session"
    assert result["raw_response"]["session_info"]["session_id"] == "extracted-session"
```

## Validation Checklist

- [ ] Imports added: `LLMResponseDict`, `LLM_RESPONSE_VERSION`, `datetime`
- [ ] `create_api_response_dict()` helper function implemented
- [ ] `ask_claude_code_api()` signature updated with `session_id` parameter
- [ ] Function leverages existing `ask_claude_code_api_detailed_sync()`
- [ ] Session ID extracted from `session_info`
- [ ] Return type changed to `LLMResponseDict`
- [ ] Complete LLMResponseDict structure returned
- [ ] All existing tests still pass
- [ ] New tests added and passing (~3 tests)
- [ ] Docstrings updated with examples

## LLM Prompt

```
I am implementing Step 4 of the LLM Session Management implementation plan.

Please review:
- pr_info/steps/summary.md for architectural context
- pr_info/steps/step_1.md for LLMResponseDict type definition
- pr_info/steps/decisions.md for architecture decisions

For Step 4, I need to modify src/mcp_coder/llm_providers/claude/claude_code_api.py:

Requirements from pr_info/steps/step_4.md:
1. Add imports: datetime, LLMResponseDict, LLM_RESPONSE_VERSION
2. Implement create_api_response_dict() helper function
3. Modify ask_claude_code_api() to:
   - Accept optional session_id parameter
   - Leverage existing ask_claude_code_api_detailed_sync() function
   - Extract session_id from detailed["session_info"]["session_id"]
   - Build and return LLMResponseDict
4. Add ~3 test cases to tests/llm_providers/claude/test_claude_code_api.py

Strategy: KISS - Use existing detailed function instead of reimplementing.
The detailed function already extracts session_id and metadata.

Note: If ask_claude_code_api_detailed_sync() needs session_id parameter,
modify it to accept and pass through to ClaudeCodeOptions(resume=session_id).

Please implement following TDD principles with all tests passing.
```

## Dependencies
- **Requires**: Steps 1-3 complete (types, serialization, CLI implementation)
- **Affects**: `claude_code_interface.py` routing (updated in Step 7)

## Success Criteria
1. ✅ Function signature updated with session_id parameter
2. ✅ Returns LLMResponseDict with all required fields
3. ✅ Leverages existing `ask_claude_code_api_detailed_sync()`
4. ✅ Session ID extracted from session_info
5. ✅ Missing session_id handled gracefully (None)
6. ✅ All metadata preserved in raw_response
7. ✅ All existing API tests still pass
8. ✅ New test cases pass (~3 tests)
9. ✅ Complete docstrings with examples
10. ✅ Simplified implementation (KISS principle)
