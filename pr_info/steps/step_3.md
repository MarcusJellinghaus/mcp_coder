# Step 3: Enhance CLI Method with JSON Parsing and Session Support

## Context
Modify `ask_claude_code_cli()` to support JSON output parsing, session management, and return TypedDict. See `pr_info/steps/summary.md` for architectural overview.

## Objective
Add session continuity to CLI method and return structured TypedDict instead of plain string, while maintaining backward compatibility at higher levels.

## Changes Required

### WHERE: File Modification
**File**: `src/mcp_coder/llm_providers/claude/claude_code_cli.py`

### WHAT: Function Changes

#### Modified Function Signature
```python
def ask_claude_code_cli(
    question: str,
    session_id: str | None = None,  # NEW: For session continuity
    timeout: int = 30,
    cwd: str | None = None,
) -> LLMResponseDict:  # CHANGED: was str
```

### HOW: Integration Points

```python
# New imports at top of file
from datetime import datetime
from ...llm_types import LLMResponseDict, LLM_RESPONSE_VERSION

# Usage in claude_code_interface.py will be updated in Step 7
```

### ALGORITHM: Enhanced CLI Call

```python
def ask_claude_code_cli(question, session_id, timeout, cwd):
    # 1. Find claude executable (existing)
    # 2. Build command with --output-format json flag
    # 3. Add --resume flag if session_id provided
    # 4. Execute command (existing subprocess logic)
    # 5. Parse JSON response to extract text, session_id, metadata
    # 6. Build and return LLMResponseDict with all fields
```

### ALGORITHM: JSON Response Parsing

```python
def _parse_cli_json_response(json_output: str) -> dict:
    # 1. Parse JSON string to dict
    # 2. Extract text from response (may be in 'text' or 'content' field)
    # 3. Extract session_id from response
    # 4. Return dict with extracted fields + full raw response
```

### DATA: Return Value Structure

```python
{
    "version": "1.0",
    "timestamp": "2025-10-01T10:30:00.123456",
    "text": "Extracted response text",
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "method": "cli",
    "provider": "claude",
    "raw_response": {
        # Complete CLI JSON output
        "text": "...",
        "session_id": "...",
        "duration_ms": 2801,
        "total_cost_usd": 0.058,
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

2. **Add helper function** (before `ask_claude_code_cli`):
```python
def _parse_cli_json_response(json_output: str, question: str) -> dict:
    """Parse CLI JSON response and extract key fields.
    
    Args:
        json_output: JSON string from CLI --output-format json
        question: Original question (for error context)
        
    Returns:
        Dict with extracted text, session_id, and raw response
        
    Raises:
        ValueError: If JSON cannot be parsed or required fields missing
    """
    try:
        raw_response = json.loads(json_output)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse CLI JSON response: {e}") from e
    
    # Extract text - try common field names
    text = ""
    if isinstance(raw_response, dict):
        # Try different possible field names for response text
        text = raw_response.get("text", "")
        if not text:
            text = raw_response.get("content", "")
        if not text:
            text = raw_response.get("response", "")
        
        # If still no text, convert entire response to string
        if not text:
            logger.warning(
                f"Could not find text field in CLI JSON response. "
                f"Available fields: {list(raw_response.keys())}"
            )
            text = str(raw_response)
    else:
        # Response is not a dict, convert to string
        text = str(raw_response)
    
    # Extract session_id
    session_id = ""
    if isinstance(raw_response, dict):
        session_id = raw_response.get("session_id", "")
        if not session_id:
            session_id = raw_response.get("sessionId", "")
    
    if not session_id:
        # No session ID found - generate warning
        logger.warning(
            "No session_id found in CLI JSON response. "
            "Session continuity may not work."
        )
        # Use a placeholder to avoid breaking
        session_id = "unknown"
    
    return {
        "text": text,
        "session_id": session_id,
        "raw_response": raw_response
    }
```

3. **Modify `ask_claude_code_cli` function**:
```python
def ask_claude_code_cli(
    question: str,
    session_id: str | None = None,
    timeout: int = 30,
    cwd: str | None = None,
) -> LLMResponseDict:
    """
    Ask Claude a question via Claude Code CLI and return structured response.

    Uses JSON output format to capture session information and metadata.
    Supports session continuity via session_id parameter.

    Args:
        question: The question to ask Claude
        session_id: Optional session ID to resume previous conversation
        timeout: Timeout in seconds for the command (default: 30)
        cwd: Working directory for the command (default: None, uses current directory)
             This is important for Claude to find .claude/settings.local.json

    Returns:
        LLMResponseDict with text response, session_id, timestamp, and raw CLI data

    Raises:
        ValueError: If input validation fails or JSON parsing fails
        subprocess.TimeoutExpired: If the command times out
        subprocess.CalledProcessError: If the command fails
        FileNotFoundError: If Claude Code CLI is not found

    Examples:
        >>> # Start new conversation
        >>> result = ask_claude_code_cli("What is Python?")
        >>> print(result["text"])
        >>> session_id = result["session_id"]
        
        >>> # Continue conversation
        >>> result2 = ask_claude_code_cli("Tell me more", session_id=session_id)
        >>> print(result2["text"])
    """
    # Input validation
    if not question or not question.strip():
        raise ValueError("Question cannot be empty or whitespace only")

    if timeout <= 0:
        raise ValueError("Timeout must be a positive number")

    # Find the Claude executable
    claude_cmd = _find_claude_executable()

    # Build command with JSON output and optional session resume
    command = [claude_cmd, "--print", "--output-format", "json"]
    
    # Add session resume flag if provided
    if session_id:
        command.extend(["--resume", session_id])
    
    # Add the question
    command.append(question)

    # Execute command
    logger.debug(f"Executing: {' '.join(command[:4])} ... (cwd={cwd})")
    
    result = execute_command(
        command,
        timeout_seconds=timeout,
        cwd=cwd,
    )

    if result.timed_out:
        logger.error(f"Claude Code CLI timed out after {timeout} seconds")
        raise subprocess.TimeoutExpired(
            result.command or [claude_cmd],
            timeout,
            f"Claude Code command timed out after {timeout} seconds",
        )

    if result.return_code != 0:
        logger.error(f"Claude Code CLI failed with return code {result.return_code}")
        raise subprocess.CalledProcessError(
            result.return_code,
            result.command or [claude_cmd],
            output=result.stdout,
            stderr=f"Claude Code command failed: {result.stderr}",
        )

    logger.debug(f"Claude CLI success: response length={len(result.stdout.strip())}")

    # Parse JSON response
    parsed = _parse_cli_json_response(result.stdout.strip(), question)
    
    # Build structured response
    response: LLMResponseDict = {
        "version": LLM_RESPONSE_VERSION,
        "timestamp": datetime.now().isoformat(),
        "text": parsed["text"],
        "session_id": parsed["session_id"],
        "method": "cli",
        "provider": "claude",
        "raw_response": parsed["raw_response"],
    }
    
    return response
```

## Testing

### WHERE: Test File Modification
**File**: `tests/llm_providers/claude/test_claude_code_cli.py` (existing file)

### Test Cases to Add

```python
"""Additional tests for CLI session support and JSON parsing."""

import json
import pytest
from mcp_coder.llm_providers.claude.claude_code_cli import (
    ask_claude_code_cli,
    _parse_cli_json_response,
)
from mcp_coder.llm_types import LLMResponseDict


def test_parse_cli_json_response_basic():
    """Test parsing basic CLI JSON response."""
    json_output = json.dumps({
        "text": "Test response",
        "session_id": "abc-123"
    })
    
    result = _parse_cli_json_response(json_output, "test question")
    
    assert result["text"] == "Test response"
    assert result["session_id"] == "abc-123"
    assert result["raw_response"]["text"] == "Test response"


def test_parse_cli_json_response_alternative_fields():
    """Test parsing with alternative field names."""
    # Try 'content' instead of 'text'
    json_output = json.dumps({
        "content": "Alternative response",
        "sessionId": "def-456"  # Alternative casing
    })
    
    result = _parse_cli_json_response(json_output, "test")
    
    assert result["text"] == "Alternative response"
    assert result["session_id"] == "def-456"


def test_parse_cli_json_response_missing_session_id():
    """Test parsing when session_id is missing."""
    json_output = json.dumps({
        "text": "Response without session"
    })
    
    result = _parse_cli_json_response(json_output, "test")
    
    assert result["text"] == "Response without session"
    assert result["session_id"] == "unknown"  # Placeholder


def test_parse_cli_json_response_invalid_json():
    """Test error handling for invalid JSON."""
    invalid_json = "not valid json {{"
    
    with pytest.raises(ValueError, match="Failed to parse CLI JSON response"):
        _parse_cli_json_response(invalid_json, "test")


def test_ask_claude_code_cli_returns_typed_dict(mock_claude_cli):
    """Test that ask_claude_code_cli returns LLMResponseDict."""
    mock_claude_cli.set_response(json.dumps({
        "text": "Test response",
        "session_id": "test-session-123"
    }))
    
    result = ask_claude_code_cli("Test question")
    
    # Check structure
    assert isinstance(result, dict)
    assert "version" in result
    assert "timestamp" in result
    assert "text" in result
    assert "session_id" in result
    assert "method" in result
    assert "provider" in result
    assert "raw_response" in result


def test_ask_claude_code_cli_with_session_id(mock_claude_cli):
    """Test that session_id is passed to CLI with --resume flag."""
    mock_claude_cli.set_response(json.dumps({
        "text": "Continued response",
        "session_id": "existing-session"
    }))
    
    result = ask_claude_code_cli("Follow up", session_id="existing-session")
    
    # Check that --resume flag was used
    assert "--resume" in mock_claude_cli.last_command
    assert "existing-session" in mock_claude_cli.last_command
    assert result["session_id"] == "existing-session"


def test_ask_claude_code_cli_json_format_flag(mock_claude_cli):
    """Test that --output-format json flag is used."""
    mock_claude_cli.set_response(json.dumps({
        "text": "JSON response",
        "session_id": "json-test"
    }))
    
    result = ask_claude_code_cli("Test")
    
    # Check that JSON format flag was used
    assert "--output-format" in mock_claude_cli.last_command
    assert "json" in mock_claude_cli.last_command


def test_ask_claude_code_cli_metadata_fields(mock_claude_cli):
    """Test that metadata fields are preserved in raw_response."""
    cli_response = {
        "text": "Response",
        "session_id": "meta-test",
        "duration_ms": 2801,
        "total_cost_usd": 0.058,
        "usage": {"input_tokens": 100, "output_tokens": 50}
    }
    mock_claude_cli.set_response(json.dumps(cli_response))
    
    result = ask_claude_code_cli("Test")
    
    # Metadata should be in raw_response
    assert result["raw_response"]["duration_ms"] == 2801
    assert result["raw_response"]["total_cost_usd"] == 0.058
    assert result["raw_response"]["usage"]["input_tokens"] == 100


def test_ask_claude_code_cli_provider_and_method(mock_claude_cli):
    """Test that provider and method are set correctly."""
    mock_claude_cli.set_response(json.dumps({
        "text": "Test",
        "session_id": "abc"
    }))
    
    result = ask_claude_code_cli("Test")
    
    assert result["method"] == "cli"
    assert result["provider"] == "claude"


def test_ask_claude_code_cli_version(mock_claude_cli):
    """Test that version is set correctly."""
    mock_claude_cli.set_response(json.dumps({
        "text": "Test",
        "session_id": "abc"
    }))
    
    result = ask_claude_code_cli("Test")
    
    assert result["version"] == "1.0"


# Note: Integration tests will be in Step 9
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
