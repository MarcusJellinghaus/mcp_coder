# Step 6: Update Top-Level ask_llm() Interface

## Context
Update `ask_llm()` in the main LLM interface to support session_id parameter while maintaining backward compatibility. See `pr_info/steps/summary.md` for architectural overview.

## Objective
Add session_id parameter to ask_llm() and pass it through the call chain, keeping the simple string-return interface intact.

## Changes Required

### WHERE: File Modification
**File**: `src/mcp_coder/llm_interface.py`

### WHAT: Function Changes

#### Modified Function Signature
```python
def ask_llm(
    question: str,
    provider: str = "claude",
    method: str = "cli",
    session_id: str | None = None,  # NEW parameter
    timeout: int = 30,
    cwd: str | None = None,
) -> str:  # UNCHANGED - still returns str
```

### HOW: Integration Points

```python
# Pass session_id through to provider-specific function
if provider == "claude":
    return ask_claude_code(
        question,
        method=method,
        session_id=session_id,  # NEW
        timeout=timeout,
        cwd=cwd
    )
```

### ALGORITHM: Simple Passthrough

```python
def ask_llm(question, provider, method, session_id, timeout, cwd):
    # 1. Validate inputs (existing)
    # 2. Route to provider with session_id
    # 3. Return text response (existing behavior)
```

### DATA: No Change

```
Input: question, session_id
Output: str (text response only)
```

## Implementation

### File: `src/mcp_coder/llm_interface.py`

**Modifications**:

```python
"""High-level LLM interface for extensible provider support."""

from .llm_providers.claude.claude_code_interface import ask_claude_code


def ask_llm(
    question: str,
    provider: str = "claude",
    method: str = "cli",
    session_id: str | None = None,
    timeout: int = 30,
    cwd: str | None = None,
) -> str:
    """
    Ask a question to an LLM provider using the specified method.

    This is the main entry point for simple LLM interactions. It returns only
    the text response. For full session management with metadata, use prompt_llm()
    or the provider-specific functions directly.

    Args:
        question: The question to ask the LLM
        provider: The LLM provider to use (currently only "claude" is supported)
        method: The implementation method to use ("cli" or "api")
                - "cli": Uses Claude Code CLI executable (requires installation)
                - "api": Uses Claude Code Python SDK (automatic authentication)
        session_id: Optional session ID to resume previous conversation
                   Note: This function doesn't return session_id. Use prompt_llm()
                   for full session management capabilities.
        timeout: Timeout in seconds for the request (default: 30)
        cwd: Working directory for the command (only used for CLI method)
             This is important for Claude to find .claude/settings.local.json

    Returns:
        The LLM's response text as a string

    Raises:
        ValueError: If the provider or method is not supported, or if input validation fails
        Various exceptions from underlying implementations (e.g., subprocess errors)

    Examples:
        >>> # Simple usage (backward compatible)
        >>> response = ask_llm("What is Python?")
        >>> print(response)

        >>> # With API method
        >>> response = ask_llm("Explain recursion", method="api")
        >>> print(response)

        >>> # With session (managed externally - see prompt_llm for better approach)
        >>> response = ask_llm("My color is blue", session_id="known-session-id")
        >>> # Note: session_id not returned - use prompt_llm() instead

    Note:
        For session management with access to session_id and metadata, use:
        - prompt_llm() for high-level session-aware interface
        - ask_claude_code_cli() or ask_claude_code_api() directly for provider-specific control
    """
    # Input validation
    if not question or not question.strip():
        raise ValueError("Question cannot be empty or whitespace only")

    if timeout <= 0:
        raise ValueError("Timeout must be a positive number")

    if provider == "claude":
        return ask_claude_code(
            question,
            method=method,
            session_id=session_id,
            timeout=timeout,
            cwd=cwd
        )
    else:
        raise ValueError(
            f"Unsupported provider: {provider}. Currently supported: 'claude'"
        )
```

## Testing

### WHERE: Test File Modification
**File**: `tests/test_llm_interface.py` (existing file)

### Test Cases to Add

```python
"""Additional tests for ask_llm session parameter."""

import pytest
from mcp_coder.llm_interface import ask_llm


def test_ask_llm_with_session_id_cli(mock_claude_cli):
    """Test that session_id is passed through with CLI method."""
    mock_claude_cli.set_response("CLI response with session")
    
    response = ask_llm(
        "Test question",
        provider="claude",
        method="cli",
        session_id="test-session-123"
    )
    
    assert response == "CLI response with session"
    assert mock_claude_cli.received_session_id == "test-session-123"


def test_ask_llm_with_session_id_api(mock_claude_api):
    """Test that session_id is passed through with API method."""
    mock_claude_api.set_response("API response with session")
    
    response = ask_llm(
        "Test question",
        provider="claude",
        method="api",
        session_id="api-session-456"
    )
    
    assert response == "API response with session"
    assert mock_claude_api.received_session_id == "api-session-456"


def test_ask_llm_without_session_id(mock_claude_cli):
    """Test that session_id is optional and defaults to None."""
    mock_claude_cli.set_response("Response without session")
    
    # Should work without session_id (backward compatible)
    response = ask_llm("Test question")
    
    assert response == "Response without session"
    assert mock_claude_cli.received_session_id is None


def test_ask_llm_returns_string_not_dict(mock_claude_cli):
    """Test that ask_llm still returns string, not LLMResponseDict."""
    mock_claude_cli.set_response_dict({
        "text": "Just the text",
        "session_id": "hidden-session",
        "version": "1.0"
    })
    
    response = ask_llm("Test")
    
    # Should return string only
    assert isinstance(response, str)
    assert response == "Just the text"


def test_ask_llm_session_id_backward_compatible(mock_claude_cli):
    """Test that existing code without session_id still works."""
    mock_claude_cli.set_response("Backward compatible response")
    
    # Old calling pattern should still work
    response = ask_llm("Question", provider="claude", method="cli", timeout=30)
    
    assert response == "Backward compatible response"
```

## Validation Checklist

- [ ] `session_id` parameter added to function signature (optional, default None)
- [ ] `session_id` passed through to `ask_claude_code()`
- [ ] Return type unchanged (still `str`)
- [ ] Docstring updated with session parameter explanation
- [ ] Docstring notes limitation and points to `prompt_llm()`
- [ ] All existing tests still pass (backward compatible)
- [ ] New tests added and passing
- [ ] Parameter order maintains backward compatibility

## LLM Prompt

```
I am implementing Step 6 of the LLM Session Management implementation plan.

Please review:
- pr_info/steps/summary.md for architectural context
- pr_info/steps/step_5.md for the interface routing layer
- pr_info/steps/decisions.md for architecture decisions

For Step 6, I need to modify src/mcp_coder/llm_interface.py:

Requirements from pr_info/steps/step_6.md:
1. Add session_id parameter to ask_llm() function signature (optional, defaults to None)
2. Pass session_id through to ask_claude_code()
3. Keep return type as str (backward compatible)
4. Update docstring to:
   - Explain session_id parameter
   - Note that this function doesn't return session_id
   - Point users to prompt_llm() for full session management
5. Add test cases to tests/test_llm_interface.py

This maintains backward compatibility:
- Existing code works without changes
- session_id is optional
- Still returns str, not dict

Please implement following TDD principles with all tests passing.
```

## Dependencies
- **Requires**: Step 5 complete (interface routing updated)
- **Prepares for**: Step 7 (implement prompt_llm())

## Success Criteria
1. ✅ `session_id` parameter added (optional, default None)
2. ✅ Parameter passed through to provider layer
3. ✅ Return type unchanged (`str`)
4. ✅ All existing tests pass (backward compatible)
5. ✅ New tests validate session_id passthrough
6. ✅ Docstring explains session parameter
7. ✅ Docstring points to prompt_llm() for full session management
8. ✅ No breaking changes to existing API
