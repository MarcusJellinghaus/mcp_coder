# Step 5: Update Interface Router for TypedDict Returns

## Context
Update `ask_claude_code()` in the interface layer to handle TypedDict returns from CLI and API methods. See `pr_info/steps/summary.md` for architectural overview.

## Objective
Modify the routing function to pass session_id parameter and handle LLMResponseDict returns while maintaining the current string-only interface.

## Changes Required

### WHERE: File Modification
**File**: `src/mcp_coder/llm_providers/claude/claude_code_interface.py`

### WHAT: Function Changes

#### Modified Function Signature
```python
def ask_claude_code(
    question: str,
    method: str = "cli",
    session_id: str | None = None,  # NEW parameter
    timeout: int = 30,
    cwd: str | None = None
) -> str:  # UNCHANGED - still returns str for backward compat
```

### HOW: Integration Points

```python
# Pass session_id to underlying functions
if method == "cli":
    result = ask_claude_code_cli(question, session_id=session_id, timeout=timeout, cwd=cwd)
elif method == "api":
    result = ask_claude_code_api(question, session_id=session_id, timeout=timeout)

# Extract text from LLMResponseDict
return result["text"]
```

### ALGORITHM: Router Logic

```python
def ask_claude_code(question, method, session_id, timeout, cwd):
    # 1. Validate inputs (existing)
    # 2. Route to CLI or API method with session_id
    # 3. Receive LLMResponseDict from either method
    # 4. Extract and return text field only
    # 5. (Discard other fields - used in higher-level prompt_llm)
```

### DATA: Flow

```
Input: question, session_id -> ask_claude_code()
  -> Routes to ask_claude_code_cli() or ask_claude_code_api()
  -> Returns: LLMResponseDict
  -> Extracts: result["text"]
Output: str (text only)
```

## Implementation

### File: `src/mcp_coder/llm_providers/claude/claude_code_interface.py`

**Modifications**:

```python
"""Claude Code interface with routing between different implementation methods."""

from .claude_code_api import ask_claude_code_api
from .claude_code_cli import ask_claude_code_cli


def ask_claude_code(
    question: str,
    method: str = "cli",
    session_id: str | None = None,
    timeout: int = 30,
    cwd: str | None = None
) -> str:
    """
    Ask Claude a question using the specified implementation method.

    Routes between different Claude Code implementation methods (CLI, API, etc.).
    Supports both CLI and Python SDK (API) methods with session continuity.

    This function returns only the text response. For full session information
    and metadata, use the lower-level functions directly or use prompt_llm().

    Args:
        question: The question to ask Claude
        method: The implementation method to use ("cli" or "api")
        session_id: Optional session ID to resume previous conversation
        timeout: Timeout in seconds for the request (default: 30)
        cwd: Working directory for the command (only used for CLI method)
             This is important for Claude to find .claude/settings.local.json

    Returns:
        Claude's response text as a string

    Raises:
        ValueError: If the method is not supported or if input validation fails
        Various exceptions from underlying implementations

    Examples:
        >>> # Simple usage without session
        >>> response = ask_claude_code("Explain recursion")
        >>> print(response)

        >>> # With session continuity (text-only, session_id managed externally)
        >>> response1 = ask_claude_code("My color is blue")
        >>> # Note: session_id not available from this function
        >>> # Use ask_claude_code_cli/api directly or prompt_llm() for session management
    """
    # Input validation
    if not question or not question.strip():
        raise ValueError("Question cannot be empty or whitespace only")

    if timeout <= 0:
        raise ValueError("Timeout must be a positive number")

    # Route to appropriate method and pass session_id
    if method == "cli":
        result = ask_claude_code_cli(
            question,
            session_id=session_id,
            timeout=timeout,
            cwd=cwd
        )
    elif method == "api":
        result = ask_claude_code_api(
            question,
            session_id=session_id,
            timeout=timeout
        )
    else:
        raise ValueError(
            f"Unsupported method: {method}. Supported methods: 'cli', 'api'"
        )
    
    # Extract text from LLMResponseDict
    # (Full response data available from lower-level functions)
    return result["text"]
```

## Testing

### WHERE: Test File Modification
**File**: `tests/llm_providers/claude/test_claude_code_interface.py` (existing file)

### Test Cases to Add

```python
"""Additional tests for interface routing with sessions."""

import pytest
from mcp_coder.llm_providers.claude.claude_code_interface import ask_claude_code


def test_ask_claude_code_cli_with_session_id(mock_claude_cli):
    """Test that session_id is passed through to CLI method."""
    mock_claude_cli.set_response_dict({
        "text": "CLI response",
        "session_id": "cli-session-123"
    })
    
    response = ask_claude_code("Test", method="cli", session_id="cli-session-123")
    
    assert response == "CLI response"
    assert mock_claude_cli.received_session_id == "cli-session-123"


def test_ask_claude_code_api_with_session_id(mock_claude_api):
    """Test that session_id is passed through to API method."""
    mock_claude_api.set_response_dict({
        "text": "API response",
        "session_id": "api-session-456"
    })
    
    response = ask_claude_code("Test", method="api", session_id="api-session-456")
    
    assert response == "API response"
    assert mock_claude_api.received_session_id == "api-session-456"


def test_ask_claude_code_returns_text_only(mock_claude_cli):
    """Test that function returns only text, not full dict."""
    mock_claude_cli.set_response_dict({
        "text": "Just the text",
        "session_id": "test-123",
        "version": "1.0",
        "metadata": {"cost": 0.05}
    })
    
    response = ask_claude_code("Test", method="cli")
    
    # Should return string, not dict
    assert isinstance(response, str)
    assert response == "Just the text"


def test_ask_claude_code_without_session_id(mock_claude_cli):
    """Test that session_id is optional."""
    mock_claude_cli.set_response_dict({
        "text": "Response without session",
        "session_id": "auto-generated"
    })
    
    # Should not raise - session_id is optional
    response = ask_claude_code("Test", method="cli")
    assert response == "Response without session"


def test_ask_claude_code_session_id_none_by_default(mock_claude_cli):
    """Test that session_id defaults to None."""
    mock_claude_cli.set_response_dict({
        "text": "Default behavior",
        "session_id": "new-session"
    })
    
    response = ask_claude_code("Test", method="cli")
    
    # Should pass None as session_id to underlying function
    assert mock_claude_cli.received_session_id is None
```

## Validation Checklist

- [ ] `session_id` parameter added to function signature
- [ ] `session_id` passed to `ask_claude_code_cli()` when method="cli"
- [ ] `session_id` passed to `ask_claude_code_api()` when method="api"
- [ ] Return type unchanged (still `str`)
- [ ] Text extracted from LLMResponseDict via `result["text"]`
- [ ] Docstring updated to explain text-only return
- [ ] All existing tests still pass
- [ ] New tests added and passing
- [ ] Backward compatibility maintained (session_id optional)

## LLM Prompt

```
I am implementing Step 5 of the LLM Session Management implementation plan.

Please review:
- pr_info/steps/summary.md for architectural context
- pr_info/steps/step_3.md for CLI modifications
- pr_info/steps/step_4.md for API modifications
- pr_info/steps/decisions.md for architecture decisions

For Step 5, I need to modify src/mcp_coder/llm_providers/claude/claude_code_interface.py:

Requirements from pr_info/steps/step_5.md:
1. Add session_id parameter to ask_claude_code() function signature
2. Pass session_id to ask_claude_code_cli() when method="cli"
3. Pass session_id to ask_claude_code_api() when method="api"
4. Extract text field from LLMResponseDict: return result["text"]
5. Keep return type as str (backward compatible)
6. Update docstring to explain text-only return and session management
7. Add test cases to tests/llm_providers/claude/test_claude_code_interface.py

This is a routing layer that:
- Accepts session_id (optional, defaults to None)
- Passes it through to underlying methods
- Returns only text (discards session metadata)
- Maintains backward compatibility

Please implement following TDD principles with all tests passing.
```

## Dependencies
- **Requires**: Steps 3-4 complete (CLI and API return TypedDict)
- **Used by**: `ask_llm()` in llm_interface.py (Step 6)

## Success Criteria
1. ✅ `session_id` parameter added
2. ✅ Parameter passed through to both methods
3. ✅ Text extracted and returned
4. ✅ Return type remains `str`
5. ✅ All existing tests pass
6. ✅ New tests validate session_id passthrough
7. ✅ Backward compatible (session_id optional)
8. ✅ Docstring explains relationship to prompt_llm()
