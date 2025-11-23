# Step 1: Add Enhanced Logging Helper Function

## Where

**File**: `src/mcp_coder/llm/providers/claude/claude_code_cli.py`

**Location**: Add new module-level helper function at the end of the file (before `ask_claude_code_cli()` definition, or after other helpers)

## What

Create a reusable logging helper function to format and log debug information consistently for both CLI and API calls.

### Function Signature

```python
def _log_llm_request_debug(
    method: str,
    provider: str,
    session_id: str | None,
    command: list[str] | None = None,
    prompt: str | None = None,
    timeout: int | None = None,
    env_vars: dict[str, str] | None = None,
    cwd: str | None = None,
    mcp_config: str | None = None,
) -> None:
    """Log comprehensive debug information for LLM requests.
    
    Args:
        method: 'cli' or 'api'
        provider: 'claude' or other provider name
        session_id: Session ID (None for new, string for resuming)
        command: CLI command list (only for CLI method)
        prompt: Full prompt text (for preview)
        timeout: Timeout in seconds
        env_vars: Environment variables dict
        cwd: Working directory
        mcp_config: MCP config file path
    """
```

## How

### Pseudocode

```
1. Determine session status: "new" if session_id is None, else "resuming"
2. Create header: f"Claude {method} execution [{status}]:"
3. Log provider and method fields
4. Log session status
5. If CLI method: format and log command (first arg on same line, rest indented)
6. Format and log prompt preview (chars + first 250 chars with ellipsis if needed)
7. Log timeout, cwd, mcp_config, env_vars (full dict)
8. All fields aligned with proper indentation
9. Use logger.debug() for all output
```

## Algorithm

```python
# Session indicator
status = "resuming" if session_id else "new"
header = f"Claude {method} execution [{status}]:"

# Build field list (tuples of label and value)
fields = [
    ("Provider", provider),
    ("Method", method),
    ("Session", session_id or "None"),
    # ... add more fields ...
]

# Format each field with alignment
# Log header
# Log each field on separate line with consistent indentation
```

## Data Structures

### Return Value
- **Type**: `None`
- **Side Effect**: Calls `logger.debug()` multiple times with formatted strings

### Internal Format
```python
# Example log output (single logger.debug call per line):
# Line 1: Header with session status
# Line 2+: Each field indented consistently
```

## Implementation Details

### Command Formatting (CLI only)
```python
if command:
    cmd_first = command[0]
    cmd_rest = [f"                 {arg}" for arg in command[1:]]
    # Format: first arg on same line, rest indented further
```

### Prompt Preview
```python
if prompt:
    prompt_preview = prompt[:250]
    ellipsis = "..." if len(prompt) > 250 else ""
    preview_text = f"{len(prompt)} chars - {prompt_preview}{ellipsis}"
```

### Environment Variables
```python
if env_vars:
    # Log full dict as Python dict representation
    logger.debug(f"    env_vars:  {env_vars}")
```

## Testing

**Unit Test File**: `tests/llm/providers/claude/test_claude_code_cli.py` (existing)

**Test Case Name**: `test_log_llm_request_debug_formats_output_correctly`

### Test Steps
1. Mock `logger.debug`
2. Call `_log_llm_request_debug()` with sample data (CLI method, new session)
3. Verify:
   - Header line logged with correct session status
   - Each field logged on separate line
   - Command arguments properly formatted and indented
   - Prompt preview shows count and first 250 chars
   - Env vars logged as dict
   - Alignment consistent (check indentation)
4. Repeat for API method and resuming session

### Expected Behavior
- Function logs nothing to stdout/stderr
- Function uses `logger.debug()` for all output
- No exceptions raised
- Works with None values for optional parameters

## Files to Create/Modify

| File | Type | Details |
|------|------|---------|
| `src/mcp_coder/llm/providers/claude/claude_code_cli.py` | Modify | Add `_log_llm_request_debug()` function |
| `tests/llm/providers/claude/test_claude_code_cli.py` | Modify | Add unit test for logging function |

## Integration Points

- **Called by**: `ask_claude_code_cli()` in Step 2
- **Called by**: `ask_claude_code_api()` in Step 3 (but imported from this module)
- **Imports**: `logging` (already imported)
- **Decorators**: None
- **Dependencies**: None (uses only standard library)

## Success Criteria

- ✅ Helper function defined and callable
- ✅ Formats all fields correctly
- ✅ Handles None values gracefully
- ✅ Unit test passes
- ✅ No changes to `ask_claude_code_cli()` or API file yet
