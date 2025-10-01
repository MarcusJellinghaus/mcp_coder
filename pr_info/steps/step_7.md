# Step 7: Implement prompt_llm() for Full Session Management

## Context
Create new `prompt_llm()` function that returns complete LLMResponseDict with session_id and metadata. See `pr_info/steps/summary.md` for architectural overview.

## Objective
Provide a high-level interface for session-aware LLM interactions that returns full response data including session_id for conversation continuity.

## Changes Required

### WHERE: File Modification
**File**: `src/mcp_coder/llm_interface.py`

### WHAT: New Function

```python
def prompt_llm(
    question: str,
    provider: str = "claude",
    method: str = "cli",
    session_id: str | None = None,
    timeout: int = 30,
    cwd: str | None = None,
) -> LLMResponseDict:  # Returns full structured response
```

### HOW: Integration Points

```python
# Import types
from .llm_types import LLMResponseDict

# Call provider-specific functions directly to get LLMResponseDict
from .llm_providers.claude.claude_code_cli import ask_claude_code_cli
from .llm_providers.claude.claude_code_api import ask_claude_code_api

# Import serialization for convenience
from .llm_serialization import serialize_llm_response, deserialize_llm_response

# Export all public functions
__all__ = ["ask_llm", "prompt_llm", "serialize_llm_response", "deserialize_llm_response"]
```

### ALGORITHM: Direct Provider Call

```python
def prompt_llm(question, provider, method, session_id, timeout, cwd):
    # 1. Validate inputs
    # 2. If provider is "claude":
    #    a. If method is "cli": call ask_claude_code_cli directly
    #    b. If method is "api": call ask_claude_code_api directly
    # 3. Return full LLMResponseDict (no extraction)
    # 4. Raise ValueError for unsupported provider/method
```

### DATA: Return Structure

```python
{
    "version": "1.0",
    "timestamp": "2025-10-01T10:30:00.123456",
    "text": "Full response text",
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "method": "cli" or "api",
    "provider": "claude",
    "raw_response": {...}  # Complete metadata
}
```

## Implementation

### File: `src/mcp_coder/llm_interface.py`

**Additions**:

```python
"""High-level LLM interface for extensible provider support."""

from .llm_providers.claude.claude_code_interface import ask_claude_code
from .llm_providers.claude.claude_code_cli import ask_claude_code_cli
from .llm_providers.claude.claude_code_api import ask_claude_code_api
from .llm_types import LLMResponseDict
from .llm_serialization import serialize_llm_response, deserialize_llm_response

__all__ = [
    "ask_llm",
    "prompt_llm",
    "serialize_llm_response",
    "deserialize_llm_response",
]


def ask_llm(
    question: str,
    provider: str = "claude",
    method: str = "cli",
    session_id: str | None = None,
    timeout: int = 30,
    cwd: str | None = None,
) -> str:
    """... existing docstring ..."""
    # ... existing implementation ...


def prompt_llm(
    question: str,
    provider: str = "claude",
    method: str = "cli",
    session_id: str | None = None,
    timeout: int = 30,
    cwd: str | None = None,
) -> LLMResponseDict:
    """
    Ask a question to an LLM provider with full session management.

    This function returns complete response data including session_id and metadata,
    enabling conversation continuity and comprehensive logging.

    Args:
        question: The question to ask the LLM
        provider: The LLM provider to use (currently only "claude" is supported)
        method: The implementation method to use ("cli" or "api")
                - "cli": Uses Claude Code CLI executable (requires installation)
                - "api": Uses Claude Code Python SDK (automatic authentication)
        session_id: Optional session ID to resume previous conversation
        timeout: Timeout in seconds for the request (default: 30)
        cwd: Working directory for the command (only used for CLI method)
             This is important for Claude to find .claude/settings.local.json

    Returns:
        LLMResponseDict containing:
        - version: Serialization format version
        - timestamp: ISO format timestamp
        - text: The response text
        - session_id: Session ID for conversation continuity
        - method: Communication method used ("cli" or "api")
        - provider: LLM provider name ("claude")
        - raw_response: Complete metadata (duration, cost, usage, etc.)

    Raises:
        ValueError: If the provider or method is not supported, or if input validation fails
        Various exceptions from underlying implementations (e.g., subprocess errors)

    Examples:
        >>> # Start new conversation
        >>> result = prompt_llm("My favorite color is blue")
        >>> print(result["text"])
        >>> session_id = result["session_id"]
        
        >>> # Continue conversation
        >>> result2 = prompt_llm("What's my favorite color?", session_id=session_id)
        >>> print(result2["text"])  # "Your favorite color is blue"
        
        >>> # Save conversation for later analysis
        >>> serialize_llm_response(result2, f"logs/{session_id}.json")
        
        >>> # Access metadata
        >>> print(f"Cost: ${result2['raw_response'].get('cost_usd', 0)}")
        >>> print(f"Duration: {result2['raw_response'].get('duration_ms')}ms")

    Note:
        For simple text-only responses without session management, use ask_llm().
        This function is designed for:
        - Conversation continuity across multiple turns
        - Comprehensive logging and analysis
        - Cost tracking and usage monitoring
        - Parallel usage safety (each conversation has unique session_id)
    """
    # Input validation
    if not question or not question.strip():
        raise ValueError("Question cannot be empty or whitespace only")

    if timeout <= 0:
        raise ValueError("Timeout must be a positive number")

    # Route to provider-specific implementation
    # Call lower-level functions directly to get LLMResponseDict
    if provider == "claude":
        if method == "cli":
            return ask_claude_code_cli(
                question,
                session_id=session_id,
                timeout=timeout,
                cwd=cwd
            )
        elif method == "api":
            return ask_claude_code_api(
                question,
                session_id=session_id,
                timeout=timeout
            )
        else:
            raise ValueError(
                f"Unsupported method: {method}. Supported methods: 'cli', 'api'"
            )
    else:
        raise ValueError(
            f"Unsupported provider: {provider}. Currently supported: 'claude'"
        )
```

## Testing

### WHERE: Test File Modification
**File**: `tests/test_llm_interface.py`

### Test Cases to Add

```python
"""Tests for prompt_llm function."""

import pytest
from mcp_coder.llm_interface import prompt_llm
from mcp_coder.llm_types import LLMResponseDict


def test_prompt_llm_returns_typed_dict_cli(mock_claude_cli):
    """Test that prompt_llm returns LLMResponseDict with CLI."""
    mock_claude_cli.set_response_dict({
        "version": "1.0",
        "timestamp": "2025-10-01T10:30:00",
        "text": "CLI response",
        "session_id": "cli-123",
        "method": "cli",
        "provider": "claude",
        "raw_response": {}
    })
    
    result = prompt_llm("Test question", method="cli")
    
    assert isinstance(result, dict)
    assert result["version"] == "1.0"
    assert result["text"] == "CLI response"
    assert result["session_id"] == "cli-123"
    assert result["method"] == "cli"
    assert result["provider"] == "claude"


def test_prompt_llm_returns_typed_dict_api(mock_claude_api):
    """Test that prompt_llm returns LLMResponseDict with API."""
    mock_claude_api.set_response_dict({
        "version": "1.0",
        "timestamp": "2025-10-01T10:30:00",
        "text": "API response",
        "session_id": "api-456",
        "method": "api",
        "provider": "claude",
        "raw_response": {}
    })
    
    result = prompt_llm("Test question", method="api")
    
    assert isinstance(result, dict)
    assert result["method"] == "api"
    assert result["session_id"] == "api-456"


def test_prompt_llm_with_session_id_cli(mock_claude_cli):
    """Test session continuity with CLI."""
    mock_claude_cli.set_response_dict({
        "version": "1.0",
        "timestamp": "2025-10-01T10:30:00",
        "text": "Continued response",
        "session_id": "existing-session",
        "method": "cli",
        "provider": "claude",
        "raw_response": {}
    })
    
    result = prompt_llm("Follow up", method="cli", session_id="existing-session")
    
    assert result["session_id"] == "existing-session"
    assert mock_claude_cli.received_session_id == "existing-session"


def test_prompt_llm_with_session_id_api(mock_claude_api):
    """Test session continuity with API."""
    mock_claude_api.set_response_dict({
        "version": "1.0",
        "timestamp": "2025-10-01T10:30:00",
        "text": "Continued API response",
        "session_id": "api-session",
        "method": "api",
        "provider": "claude",
        "raw_response": {}
    })
    
    result = prompt_llm("Follow up", method="api", session_id="api-session")
    
    assert result["session_id"] == "api-session"
    assert mock_claude_api.received_session_id == "api-session"


def test_prompt_llm_preserves_metadata(mock_claude_cli):
    """Test that metadata is preserved in response."""
    mock_claude_cli.set_response_dict({
        "version": "1.0",
        "timestamp": "2025-10-01T10:30:00",
        "text": "Response with metadata",
        "session_id": "meta-test",
        "method": "cli",
        "provider": "claude",
        "raw_response": {
            "duration_ms": 2801,
            "cost_usd": 0.058,
            "usage": {"input_tokens": 100}
        }
    })
    
    result = prompt_llm("Test")
    
    assert result["raw_response"]["duration_ms"] == 2801
    assert result["raw_response"]["cost_usd"] == 0.058


def test_prompt_llm_unsupported_provider(mock_claude_cli):
    """Test error for unsupported provider."""
    with pytest.raises(ValueError, match="Unsupported provider"):
        prompt_llm("Test", provider="gpt")


def test_prompt_llm_unsupported_method(mock_claude_cli):
    """Test error for unsupported method."""
    with pytest.raises(ValueError, match="Unsupported method"):
        prompt_llm("Test", method="unknown")


def test_prompt_llm_empty_question(mock_claude_cli):
    """Test validation for empty question."""
    with pytest.raises(ValueError, match="cannot be empty"):
        prompt_llm("")


def test_prompt_llm_invalid_timeout(mock_claude_cli):
    """Test validation for invalid timeout."""
    with pytest.raises(ValueError, match="positive number"):
        prompt_llm("Test", timeout=0)
```

## Validation Checklist

- [ ] `prompt_llm()` function implemented
- [ ] Imports added: `LLMResponseDict`, provider functions, serialization
- [ ] `__all__` updated to export new functions
- [ ] Returns `LLMResponseDict` (not `str`)
- [ ] Calls provider functions directly (not through routing layer)
- [ ] Session_id parameter passed through
- [ ] Complete docstring with examples
- [ ] Error handling for unsupported provider/method
- [ ] All tests added and passing
- [ ] Integration with serialization functions shown in examples

## LLM Prompt

```
I am implementing Step 7 of the LLM Session Management implementation plan.

Please review:
- pr_info/steps/summary.md for architectural context
- pr_info/steps/step_1.md for LLMResponseDict definition
- pr_info/steps/step_3-4.md for provider implementations
- pr_info/steps/decisions.md for architecture decisions

For Step 7, I need to modify src/mcp_coder/llm_interface.py:

Requirements from pr_info/steps/step_7.md:
1. Add imports: LLMResponseDict, ask_claude_code_cli, ask_claude_code_api, serialization functions
2. Update __all__ to export: ask_llm, prompt_llm, serialize_llm_response, deserialize_llm_response
3. Implement prompt_llm() function that:
   - Accepts same parameters as ask_llm()
   - Returns LLMResponseDict instead of str
   - Calls provider functions directly (ask_claude_code_cli or ask_claude_code_api)
   - No text extraction - returns full response
4. Add comprehensive docstring with examples showing:
   - Session continuity usage
   - Serialization usage
   - Metadata access
5. Add test cases to tests/test_llm_interface.py

This is the main user-facing function for session management.

Please implement following TDD principles with all tests passing.
```

## Dependencies
- **Requires**: Steps 1-6 complete (all infrastructure ready)

## Success Criteria
1. ✅ `prompt_llm()` implemented and exported
2. ✅ Returns `LLMResponseDict` with all fields
3. ✅ Session continuity works for both CLI and API
4. ✅ Serialization functions exported for convenience
5. ✅ Complete docstring with practical examples
6. ✅ All tests pass
7. ✅ Clear distinction from `ask_llm()` in documentation
8. ✅ Examples demonstrate session management workflow
