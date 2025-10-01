# Step 3: Enhance CLI Method with JSON Parsing and Session Support

## Context
Modify `ask_claude_code_cli()` to support JSON output parsing, session management, and return TypedDict. See `pr_info/steps/summary.md` for architectural overview.

## Objective
Add session continuity to CLI method and return structured TypedDict instead of plain string, while maintaining backward compatibility at higher levels.

## Changes Required

### WHERE: File Modification
**File**: `src/mcp_coder/llm_providers/claude/claude_code_cli.py`

### WHAT: Functions

**Pure Functions** (testable without I/O):
```python
def parse_cli_json_string(json_str: str) -> dict:
    """Parse CLI JSON and extract fields (pure function).
    
    Returns:
        dict with keys: 'text' (str), 'session_id' (str | None), 'raw_response' (dict)
    """

def build_cli_command(question: str, session_id: str | None, claude_cmd: str) -> list[str]:
    """Build CLI command arguments (pure function)."""

def create_response_dict(text: str, session_id: str | None, raw_response: dict) -> LLMResponseDict:
    """Create LLMResponseDict from parsed data (pure function)."""
```

**Note:** These pure functions are implementation details and are NOT exported in the module's `__all__` list. They are tested via unit tests but remain internal to the `claude_code_cli` module.

**Distinction from Step 2:** Unlike the serialization module (Step 2) which exports its pure functions for advanced use cases, these CLI parsing functions are provider-specific implementation details and should remain internal.

**I/O Wrapper** (subprocess execution):
```python
def ask_claude_code_cli(
    question: str,
    session_id: str | None = None,
    timeout: int = 30,
    cwd: str | None = None,
) -> LLMResponseDict:  # CHANGED: was str
    """Ask Claude via CLI (I/O wrapper)."""
```

### HOW: Integration Points

```python
# New imports at top of file
from datetime import datetime
from ...llm_types import LLMResponseDict, LLM_RESPONSE_VERSION

# Usage in claude_code_interface.py will be updated in Step 7
```

### ALGORITHM: Pure Functions

```python
def parse_cli_json_string(json_str):
    # 1. Parse JSON string with json.loads()
    # 2. Extract text from "result" field (verified from real CLI output)
    # 3. Extract session_id from "session_id" field
    # 4. Return dict with: text, session_id, raw_response

def build_cli_command(question, session_id, claude_cmd):
    # 1. Start with base: [claude_cmd, "--print", "--output-format", "json"]
    # 2. Add ["--resume", session_id] if session_id is not None
    # 3. Append question
    # 4. Return command list

def create_response_dict(text, session_id, raw_response):
    # 1. Get current timestamp
    # 2. Build LLMResponseDict with all required fields
    # 3. Set method="cli", provider="claude"
    # 4. Return complete dict
```

### ALGORITHM: I/O Wrapper

```python
def ask_claude_code_cli(question, session_id, timeout, cwd):
    # 1. Input validation
    # 2. Find Claude executable
    # 3. Build command (pure function)
    # 4. Execute subprocess
    # 5. Check for errors
    # 6. Parse JSON (pure function)
    # 7. Create response dict (pure function)
    # 8. Return LLMResponseDict
```

### DATA: Real CLI JSON Structure

**Actual CLI output** (verified - see `decisions.md` Decision 4 for details):
```json
{
  "type": "result",
  "result": "I'm here and ready to help!",  // ← Text field
  "session_id": "98fd3fe3-8272-49ff-86bb-e1ae99a5c1e4",
  "duration_ms": 3009,
  "total_cost_usd": 0.061996800000000005,
  "usage": {...},
  "modelUsage": {...}
}
```

**Return Value Structure**:
```python
{
    "version": "1.0",
    "timestamp": "2025-10-01T10:30:00.123456",
    "text": "I'm here and ready to help!",  # From "result" field
    "session_id": "98fd3fe3-8272-49ff-86bb-e1ae99a5c1e4",  # Or None
    "method": "cli",
    "provider": "claude",
    "raw_response": {  # Complete CLI JSON preserved
        "type": "result",
        "result": "...",
        "session_id": "...",
        "duration_ms": 3009,
        "total_cost_usd": 0.061996800000000005,
        ...
    }
}
```

## Implementation

### File: `src/mcp_coder/llm_providers/claude/claude_code_cli.py`

**Modifications**:

1. **Add imports at top**:
```python
import json
from datetime import datetime
from ...llm_types import LLMResponseDict, LLM_RESPONSE_VERSION
```

2. **Add pure functions** (before `ask_claude_code_cli`):

```python
def parse_cli_json_string(json_str: str) -> dict:
    """Parse CLI JSON and extract fields (pure function).
    
    Extracts text and session_id from CLI JSON output.
    Uses verified field names from real CLI testing.
    
    Args:
        json_str: JSON string from CLI --output-format json
        
    Returns:
        dict with keys:
        - 'text' (str): Extracted response text from 'result' field
        - 'session_id' (str | None): Session ID if present, None otherwise
        - 'raw_response' (dict): Complete parsed JSON response
        
    Raises:
        ValueError: If JSON cannot be parsed
        
    Example:
        >>> json_str = '{"result": "Hello", "session_id": "abc"}'
        >>> data = parse_cli_json_string(json_str)
        >>> assert data["text"] == "Hello"
    """
    try:
        raw_response = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse CLI JSON: {e}") from e
    
    # Extract text from "result" field (verified from real CLI output)
    text = raw_response.get("result", "")
    
    # Extract session_id
    session_id = raw_response.get("session_id")
    
    return {
        "text": text,
        "session_id": session_id,
        "raw_response": raw_response
    }


def build_cli_command(question: str, session_id: str | None, claude_cmd: str) -> list[str]:
    """Build CLI command arguments (pure function).
    
    Args:
        question: Question to ask
        session_id: Optional session ID for continuation
        claude_cmd: Path to claude executable
        
    Returns:
        Command list ready for subprocess execution
        
    Example:
        >>> cmd = build_cli_command("test", None, "claude")
        >>> assert cmd == ["claude", "--print", "--output-format", "json", "test"]
    """
    command = [claude_cmd, "--print", "--output-format", "json"]
    
    if session_id:
        command.extend(["--resume", session_id])
    
    command.append(question)
    return command


def create_response_dict(text: str, session_id: str | None, raw_response: dict) -> LLMResponseDict:
    """Create LLMResponseDict from parsed data (pure function).
    
    Args:
        text: Extracted response text
        session_id: Session ID (can be None)
        raw_response: Complete CLI JSON response
        
    Returns:
        Complete LLMResponseDict
        
    Example:
        >>> result = create_response_dict("Hello", "abc", {"result": "Hello"})
        >>> assert result["text"] == "Hello"
        >>> assert result["method"] == "cli"
    """
    return {
        "version": LLM_RESPONSE_VERSION,
        "timestamp": datetime.now().isoformat(),
        "text": text,
        "session_id": session_id,
        "method": "cli",
        "provider": "claude",
        "raw_response": raw_response,
    }
```

3. **Modify `ask_claude_code_cli` function** (I/O wrapper):
```python
def ask_claude_code_cli(
    question: str,
    session_id: str | None = None,
    timeout: int = 30,
    cwd: str | None = None,
) -> LLMResponseDict:
    """Ask Claude via CLI and return structured response (I/O wrapper).

    Thin wrapper that handles subprocess execution, delegating parsing
    and response construction to pure functions.

    Args:
        question: The question to ask Claude
        session_id: Optional session ID to resume previous conversation
        timeout: Timeout in seconds (default: 30)
        cwd: Working directory (default: None)

    Returns:
        LLMResponseDict with complete response data

    Raises:
        ValueError: If input validation fails or JSON parsing fails
        subprocess.TimeoutExpired: If command times out
        subprocess.CalledProcessError: If command fails

    Examples:
        >>> # Start new conversation
        >>> result = ask_claude_code_cli("What is Python?")
        >>> print(result["text"])
        >>> session_id = result["session_id"]
        
        >>> # Continue conversation
        >>> result2 = ask_claude_code_cli("Tell me more", session_id=session_id)
    """
    # Input validation
    if not question or not question.strip():
        raise ValueError("Question cannot be empty or whitespace only")
    if timeout <= 0:
        raise ValueError("Timeout must be a positive number")

    # Find executable
    claude_cmd = _find_claude_executable()

    # Build command (pure function)
    command = build_cli_command(question, session_id, claude_cmd)

    # Execute command (I/O)
    logger.debug(f"Executing CLI command (cwd={cwd})")
    result = execute_command(command, timeout_seconds=timeout, cwd=cwd)

    # Error handling
    if result.timed_out:
        logger.error(f"CLI timed out after {timeout}s")
        raise subprocess.TimeoutExpired(command, timeout)
    
    if result.return_code != 0:
        logger.error(f"CLI failed with code {result.return_code}")
        raise subprocess.CalledProcessError(
            result.return_code, command,
            output=result.stdout, stderr=result.stderr
        )

    logger.debug(f"CLI success: {len(result.stdout)} bytes")

    # Parse JSON (pure function)
    parsed = parse_cli_json_string(result.stdout.strip())
    
    # Create response dict (pure function)
    return create_response_dict(
        parsed["text"],
        parsed["session_id"],
        parsed["raw_response"]
    )
```

## Testing

### WHERE: Test File Modification
**File**: `tests/llm_providers/claude/test_claude_code_cli.py` (existing file)

### Test Cases

**Test Structure:**
- **Pure function tests** (~5 tests): Fast, no I/O, test parsing/building logic
- **I/O wrapper tests** (~2 tests): Minimal, test subprocess integration
- **Total: ~7 tests** (reduced from 10+ via separation of concerns)

```python
"""Tests for CLI session support and JSON parsing."""

import json
import pytest
from mcp_coder.llm_providers.claude.claude_code_cli import (
    parse_cli_json_string,
    build_cli_command,
    create_response_dict,
    ask_claude_code_cli,
)
from mcp_coder.llm_types import LLMResponseDict


# ============================================================================
# PURE FUNCTION TESTS (fast, no I/O)
# ============================================================================

def test_parse_cli_json_string_basic():
    """Test parsing basic CLI JSON with real structure."""
    json_str = json.dumps({
        "result": "Test response",
        "session_id": "abc-123"
    })
    
    result = parse_cli_json_string(json_str)
    
    assert result["text"] == "Test response"
    assert result["session_id"] == "abc-123"
    assert result["raw_response"]["result"] == "Test response"


def test_parse_cli_json_string_missing_session_id():
    """Test parsing when session_id is missing."""
    json_str = json.dumps({"result": "Response without session"})
    
    result = parse_cli_json_string(json_str)
    
    assert result["text"] == "Response without session"
    assert result["session_id"] is None


def test_parse_cli_json_string_invalid_json():
    """Test error handling for invalid JSON."""
    invalid_json = "not valid json {{"
    
    with pytest.raises(ValueError, match="Failed to parse CLI JSON"):
        parse_cli_json_string(invalid_json)


def test_build_cli_command_without_session():
    """Test command building without session ID."""
    cmd = build_cli_command("test question", None, "claude")
    
    assert cmd == ["claude", "--print", "--output-format", "json", "test question"]
    assert "--resume" not in cmd


def test_build_cli_command_with_session():
    """Test command building with session ID."""
    cmd = build_cli_command("follow up", "session-123", "claude")
    
    assert "--resume" in cmd
    assert "session-123" in cmd
    assert cmd[-1] == "follow up"


def test_create_response_dict_structure():
    """Test response dict creation."""
    result = create_response_dict(
        "Hello",
        "abc-123",
        {"result": "Hello", "session_id": "abc-123"}
    )
    
    assert result["text"] == "Hello"
    assert result["session_id"] == "abc-123"
    assert result["method"] == "cli"
    assert result["provider"] == "claude"
    assert "version" in result
    assert "timestamp" in result


# ============================================================================
# I/O WRAPPER TESTS (minimal, test subprocess integration)
# ============================================================================

def test_ask_claude_code_cli_returns_typed_dict(mock_claude_cli):
    """Test that CLI method returns complete LLMResponseDict."""
    mock_claude_cli.set_response(json.dumps({
        "result": "Test response",
        "session_id": "test-123"
    }))
    
    result = ask_claude_code_cli("Test question")
    
    # Check all required fields present
    assert isinstance(result, dict)
    for field in ["version", "timestamp", "text", "session_id", "method", "provider", "raw_response"]:
        assert field in result


def test_ask_claude_code_cli_with_session_integration(mock_claude_cli):
    """Test session ID passthrough in full workflow."""
    mock_claude_cli.set_response(json.dumps({
        "result": "Continued",
        "session_id": "existing"
    }))
    
    result = ask_claude_code_cli("Follow up", session_id="existing")
    
    # Verify --resume flag was used
    assert "--resume" in mock_claude_cli.last_command
    assert "existing" in mock_claude_cli.last_command
    assert result["session_id"] == "existing"
```
```

## Validation Checklist

- [ ] Imports added: `json`, `datetime`, `LLMResponseDict`, `LLM_RESPONSE_VERSION`
- [ ] `_parse_cli_json_response()` helper function implemented
- [ ] `ask_claude_code_cli()` signature updated with `session_id` parameter
- [ ] Return type changed to `LLMResponseDict`
- [ ] `--output-format json` flag added to command
- [ ] `--resume` flag added when session_id provided
- [ ] JSON parsing extracts text and session_id
- [ ] Complete LLMResponseDict structure returned
- [ ] All existing tests still pass
- [ ] New tests added and passing
- [ ] Docstrings updated with examples

## LLM Prompt

```
I am implementing Step 3 of the LLM Session Management implementation plan.

Please review:
- pr_info/steps/summary.md for architectural context
- pr_info/steps/step_1.md for LLMResponseDict type definition
- pr_info/steps/step_2.md for serialization functions

For Step 3, I need to modify src/mcp_coder/llm_providers/claude/claude_code_cli.py:

Requirements from pr_info/steps/step_3.md:
1. Add imports: json, datetime, LLMResponseDict, LLM_RESPONSE_VERSION
2. Implement _parse_cli_json_response() helper to parse CLI JSON output
3. Modify ask_claude_code_cli() to:
   - Accept optional session_id parameter
   - Use --output-format json flag
   - Use --resume flag when session_id provided
   - Parse JSON response
   - Return LLMResponseDict instead of str
4. Add comprehensive test cases to tests/llm_providers/claude/test_claude_code_cli.py

The function should build complete LLMResponseDict with all 7 required fields.
Handle missing session_id gracefully (use "unknown" placeholder).
Preserve all metadata in raw_response for future analysis.

Please implement following TDD principles with all tests passing.
```

## Dependencies
- **Requires**: Steps 1-2 complete (types and serialization)
- **Affects**: `claude_code_interface.py` routing (updated in Step 7)

## Success Criteria
1. ✅ Function signature updated with session_id parameter
2. ✅ Returns LLMResponseDict with all required fields
3. ✅ JSON output format flag used
4. ✅ Session resume flag used when applicable
5. ✅ JSON parsing handles various response formats
6. ✅ Missing session_id handled gracefully
7. ✅ All metadata preserved in raw_response
8. ✅ All existing CLI tests still pass
9. ✅ New test cases pass
10. ✅ Complete docstrings with examples
