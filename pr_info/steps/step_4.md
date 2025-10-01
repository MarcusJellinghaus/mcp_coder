# Step 4: Add Session Support to API Method

## Context
Modify `ask_claude_code_api()` and related functions to support session management and return TypedDict. See `pr_info/steps/summary.md` for architectural overview.

## Objective
Add session continuity to API method by passing session_id through ClaudeCodeOptions, and return structured TypedDict instead of plain string.

## Changes Required

### WHERE: File Modification
**File**: `src/mcp_coder/llm_providers/claude/claude_code_api.py`

### WHAT: Function Changes

#### Modified Function Signatures
```python
def ask_claude_code_api(
    question: str,
    session_id: str | None = None,  # NEW: For session continuity
    timeout: int = 30
) -> LLMResponseDict:  # CHANGED: was str

def _ask_claude_code_api_async(
    question: str,
    session_id: str | None = None,  # NEW
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

### ALGORITHM: API Call with Session

```python
def ask_claude_code_api(question, session_id, timeout):
    # 1. Verify Claude installation (existing)
    # 2. Create ClaudeCodeOptions with resume=session_id if provided
    # 3. Call _ask_claude_code_api_async with session_id
    # 4. Return LLMResponseDict (already structured)
```

### ALGORITHM: Async Implementation

```python
async def _ask_claude_code_api_async(question, session_id, timeout):
    # 1. Create ClaudeCodeOptions with resume parameter
    # 2. Query Claude SDK (existing)
    # 3. Collect response text from AssistantMessage blocks
    # 4. Extract session_id from SystemMessage or ResultMessage
    # 5. Build LLMResponseDict with all fields
    # 6. Return structured response
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

1. **Add import at top**:
```python
from ...llm_types import LLMResponseDict, LLM_RESPONSE_VERSION
from datetime import datetime  # Add if not present
```

2. **Modify `_ask_claude_code_api_async` function**: Add session support and return LLMResponseDict

3. **Modify `ask_claude_code_api` function**: Update to accept session_id and return LLMResponseDict

See step_3.md for similar implementation pattern with CLI.

## Testing

### WHERE: Test File Modification
**File**: `tests/llm_providers/claude/test_claude_code_api.py` (existing file)

### Test Cases to Add

```python
"""Additional tests for API session support."""

import pytest
from mcp_coder.llm_providers.claude.claude_code_api import ask_claude_code_api
from mcp_coder.llm_types import LLMResponseDict


def test_ask_claude_code_api_returns_typed_dict(mock_claude_api):
    """Test that API method returns LLMResponseDict."""
    mock_claude_api.set_response("Test response", session_id="api-test-123")
    
    result = ask_claude_code_api("Test question")
    
    assert isinstance(result, dict)
    assert "version" in result
    assert "timestamp" in result
    assert "text" in result
    assert "session_id" in result
    assert "method" in result
    assert "provider" in result
    assert "raw_response" in result


def test_ask_claude_code_api_with_session_id(mock_claude_api):
    """Test that session_id is passed to SDK."""
    mock_claude_api.set_response("Continued", session_id="existing-session")
    
    result = ask_claude_code_api("Follow up", session_id="existing-session")
    
    assert mock_claude_api.last_options.resume == "existing-session"
    assert result["session_id"] == "existing-session"


def test_ask_claude_code_api_extracts_session_from_messages(mock_claude_api):
    """Test session_id extraction from SDK messages."""
    mock_claude_api.set_response(
        "Response",
        session_id="msg-session-123",
        include_system_message=True
    )
    
    result = ask_claude_code_api("Test")
    assert result["session_id"] == "msg-session-123"


def test_ask_claude_code_api_preserves_metadata(mock_claude_api):
    """Test that metadata is preserved in raw_response."""
    mock_claude_api.set_response(
        "Response",
        session_id="meta-test",
        cost_usd=0.058,
        duration_ms=2801,
        usage={"input_tokens": 100, "output_tokens": 50}
    )
    
    result = ask_claude_code_api("Test")
    
    assert "result_info" in result["raw_response"]
    assert result["raw_response"]["result_info"]["cost_usd"] == 0.058
    assert result["raw_response"]["result_info"]["duration_ms"] == 2801


def test_ask_claude_code_api_provider_and_method(mock_claude_api):
    """Test that provider and method are set correctly."""
    mock_claude_api.set_response("Test", session_id="abc")
    
    result = ask_claude_code_api("Test")
    
    assert result["method"] == "api"
    assert result["provider"] == "claude"


def test_ask_claude_code_api_version(mock_claude_api):
    """Test that version is set correctly."""
    mock_claude_api.set_response("Test", session_id="abc")
    
    result = ask_claude_code_api("Test")
    assert result["version"] == "1.0"


def test_ask_claude_code_api_missing_session_id(mock_claude_api):
    """Test handling when session_id not found in messages."""
    mock_claude_api.set_response("Response", session_id=None)
    
    result = ask_claude_code_api("Test")
    assert result["session_id"] == "unknown"


def test_ask_claude_code_api_raw_messages_preserved(mock_claude_api):
    """Test that raw messages are preserved."""
    mock_claude_api.set_response("Test", session_id="abc")
    
    result = ask_claude_code_api("Test")
    
    assert "raw_messages" in result["raw_response"]
    assert isinstance(result["raw_response"]["raw_messages"], list)
```

## Validation Checklist

- [ ] Imports added: `LLMResponseDict`, `LLM_RESPONSE_VERSION`, `datetime`
- [ ] `_ask_claude_code_api_async()` signature updated with `session_id`
- [ ] `ClaudeCodeOptions(resume=session_id)` used when session_id provided
- [ ] Return type changed to `LLMResponseDict`
- [ ] Session ID extracted from SystemMessage or ResultMessage
- [ ] Complete LLMResponseDict structure returned
- [ ] `ask_claude_code_api()` updated to pass session_id through
- [ ] All existing tests still pass
- [ ] New tests added and passing
- [ ] Docstrings updated with examples

## LLM Prompt

```
I am implementing Step 4 of the LLM Session Management implementation plan.

Please review:
- pr_info/steps/summary.md for architectural context
- pr_info/steps/step_1.md for LLMResponseDict type definition
- pr_info/steps/step_3.md for CLI implementation pattern

For Step 4, I need to modify src/mcp_coder/llm_providers/claude/claude_code_api.py:

Requirements from pr_info/steps/step_4.md:
1. Add imports: datetime, LLMResponseDict, LLM_RESPONSE_VERSION
2. Modify _ask_claude_code_api_async() to:
   - Accept optional session_id parameter
   - Create ClaudeCodeOptions with resume=session_id when provided
   - Extract session_id from SystemMessage or ResultMessage
   - Build and return LLMResponseDict with all 7 required fields
3. Modify ask_claude_code_api() to:
   - Accept optional session_id parameter
   - Pass session_id to async function
   - Return LLMResponseDict instead of str
4. Add comprehensive test cases to tests/llm_providers/claude/test_claude_code_api.py

The function should:
- Extract session_id from messages (SystemMessage.session_id or ResultMessage.session_id)
- Use "unknown" placeholder if session_id not found
- Preserve all metadata in raw_response (session_info, result_info, raw_messages)

Please implement following TDD principles with all tests passing.
```

## Dependencies
- **Requires**: Steps 1-3 complete (types, serialization, CLI implementation)
- **Affects**: `claude_code_interface.py` routing (updated in Step 7)

## Success Criteria
1. ✅ Function signatures updated with session_id parameter
2. ✅ Returns LLMResponseDict with all required fields
3. ✅ ClaudeCodeOptions uses resume parameter for sessions
4. ✅ Session ID extracted from API messages
5. ✅ Missing session_id handled gracefully (use "unknown")
6. ✅ All metadata preserved in raw_response
7. ✅ All existing API tests still pass
8. ✅ New test cases pass
9. ✅ Complete docstrings with examples
10. ✅ Consistent with CLI implementation from Step 3
