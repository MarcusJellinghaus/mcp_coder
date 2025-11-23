# LLM Implementation Prompts - Issue #165

These are the prompts to use when implementing each step. Each prompt references the corresponding step document and the summary for context.

## Prompt Format

Each prompt:
1. References the overall summary (`pr_info/steps/summary.md`)
2. References the specific step document
3. Provides the key requirements
4. Specifies where to modify code
5. Includes test expectations

---

## Step 1 Prompt: Create Logging Helper Function

```
I need to implement Step 1 of Issue #165: Enhanced Debug Logging for LLM Calls.

Reference documents:
- Summary: pr_info/steps/summary.md
- Implementation guide: pr_info/steps/step_1.md
- Architectural overview: pr_info/steps/ARCHITECTURAL_OVERVIEW.md

## Task

Create a reusable logging helper function `_log_llm_request_debug()` in 
`src/mcp_coder/llm/providers/claude/claude_code_cli.py`.

## Requirements

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
```

### Logging Format

Use DEBUG level logging with proper indentation and alignment:

1. **Header Line**: 
   - Format: `Claude {method} execution [{status}]:`
   - Where status is "new" if session_id is None, else "resuming"
   - Log each field on separate line with consistent indentation

2. **Fields** (in order):
   - Provider: `claude`
   - Method: `cli` or `api`
   - Session: session_id value or "None"
   - Command: First arg on same line, rest indented further (CLI only)
   - Prompt: Character count + first 250 chars + "..." if truncated
   - cwd: Working directory or "None"
   - Timeout: Timeout in seconds (format: "{timeout}s")
   - env_vars: Full Python dict representation
   - MCP config: Path or "None" (CLI only)

3. **Indentation**:
   - Field labels: 4 spaces indent
   - Values: Aligned at column 17 (after "    Label: ")
   - Continuation lines: 17 spaces (for multi-line values like commands)

4. **Example Output**:
```
Claude CLI execution [new]:
    Provider:  claude
    Method:    cli
    Command:   /usr/bin/claude
                 -p ""
                 --output-format json
    Session:   None
    Prompt:    21 chars - Implement feature X
    cwd:       /home/user/project
    Timeout:   3600s
    env_vars:  {'MCP_CODER_PROJECT_DIR': '/project'}
    MCP config: .mcp.json
```

### Special Cases

1. **Prompt Preview**:
   - Show: `{len(prompt)} chars - {prompt[:250]}...` if len > 250
   - Show: `{len(prompt)} chars - {prompt}` if len ≤ 250

2. **None Values**:
   - Display as: "None" (string, not empty)

3. **Dict Values**:
   - Use Python dict representation: `{'key': 'value', ...}`

4. **Command Formatting** (CLI only):
   - First argument on same line as field label
   - Each subsequent argument on new line, indented to continue list
   - Example:
     ```
     Command:   /usr/bin/claude
                 -p ""
                 --output-format json
     ```

### Implementation Notes

- Use `logger.debug()` for all output
- Each field should be a separate logger.debug() call OR
  combine into single multi-line call (implementation choice)
- Handle None values gracefully (don't skip, show "None")
- Keep function pure: only logging, no side effects other than logs
- Support both CLI and API parameter combinations

### Testing

Create unit test in `tests/llm/providers/claude/test_claude_code_cli.py`:

```python
def test_log_llm_request_debug_formats_output_correctly():
    """Verify logging helper formats all fields correctly."""
    # Mock logger
    # Call helper with sample data
    # Verify header has session status [new] or [resuming]
    # Verify all fields logged
    # Verify prompt preview truncates at 250 chars with ellipsis
    # Verify command formatting (first arg on same line, rest indented)
    # Verify env_vars shown as dict
    # Verify alignment consistent
```

## Success Criteria

- ✅ Function created with correct signature
- ✅ Formats output exactly as specified
- ✅ Handles all parameter combinations
- ✅ Logs at DEBUG level
- ✅ Unit test passes
- ✅ pylint, mypy, pytest all pass
- ✅ No changes to ask_claude_code_cli() yet
```

---

## Step 2 Prompt: Add CLI Request Logging

```
I need to implement Step 2 of Issue #165: Enhanced Debug Logging for LLM Calls.

Reference documents:
- Summary: pr_info/steps/summary.md
- Implementation guide: pr_info/steps/step_2.md
- Architectural overview: pr_info/steps/ARCHITECTURAL_OVERVIEW.md
- Step 1: pr_info/steps/step_1.md (completed)

## Task

Add request logging to `ask_claude_code_cli()` function in 
`src/mcp_coder/llm/providers/claude/claude_code_cli.py`.

## Requirements

### Location

File: `src/mcp_coder/llm/providers/claude/claude_code_cli.py`
Function: `ask_claude_code_cli()`
Position: After `command = build_cli_command(...)` and before subprocess execution

### Code Change

Add a single call to the logging helper created in Step 1:

```python
# After building the command
command = build_cli_command(session_id, claude_cmd, mcp_config)

# Add this logging call:
_log_llm_request_debug(
    method="cli",
    provider="claude",
    session_id=session_id,
    command=command,
    prompt=question,
    timeout=timeout,
    env_vars=env_vars,
    cwd=cwd,
    mcp_config=mcp_config,
)

# Then continue with existing subprocess execution code
options = CommandOptions(...)
```

### Testing

Add test case to `tests/llm/providers/claude/test_claude_code_cli.py`:

1. **test_ask_claude_code_cli_logs_new_session**:
   - Call ask_claude_code_cli() with session_id=None
   - Verify logs show "[new]" session indicator
   - Verify all required fields present

2. **test_ask_claude_code_cli_logs_resuming_session**:
   - Call ask_claude_code_cli() with session_id="existing-id"
   - Verify logs show "[resuming]" session indicator
   - Verify session_id shown in logs

3. **test_ask_claude_code_cli_logs_prompt_preview**:
   - Test short prompt (< 250 chars): verify no ellipsis
   - Test long prompt (> 250 chars): verify ellipsis after 250 chars
   - Verify character count shown

4. **test_ask_claude_code_cli_logs_command_arguments**:
   - Verify all command arguments logged
   - Verify proper indentation for multi-line command
   - Verify first arg on same line as "Command:" label

### Mock Strategy

Mock these to avoid actual subprocess execution:
- `execute_subprocess()` - return success response
- `_find_claude_executable()` - return "/usr/bin/claude"

Capture logs with pytest `caplog` fixture at DEBUG level.

### Example Test

```python
def test_ask_claude_code_cli_logs_request_details(caplog, mocker):
    """Verify CLI request logging includes all fields."""
    # Mock subprocess and executable finder
    mocker.patch(
        'mcp_coder.llm.providers.claude.claude_code_cli.execute_subprocess',
        return_value=...
    )
    mocker.patch(
        'mcp_coder.llm.providers.claude.claude_code_cli._find_claude_executable',
        return_value='claude'
    )
    
    # Capture logs
    with caplog.at_level(logging.DEBUG):
        ask_claude_code_cli(
            "Test question",
            session_id=None,
            timeout=60,
            env_vars={"TEST": "value"},
            cwd="/test/cwd"
        )
    
    # Verify logs
    log_text = '\n'.join(r.message for r in caplog.records)
    assert "Claude CLI execution [new]" in log_text
    assert "Provider:  claude" in log_text
    assert "Method:    cli" in log_text
    assert "Session:   None" in log_text
    assert "Prompt:    13 chars - Test question" in log_text
    assert "Timeout:   60s" in log_text
    assert "cwd:       /test/cwd" in log_text
```

## Success Criteria

- ✅ Logging call added to ask_claude_code_cli()
- ✅ All parameters passed to logging helper
- ✅ Function behavior unchanged (no breaking changes)
- ✅ Test verifies comprehensive logging output
- ✅ [new] and [resuming] indicators work correctly
- ✅ Prompt preview truncation works
- ✅ Command formatting correct
- ✅ pylint, mypy, pytest all pass
```

---

## Step 3 Prompt: Add API Request and Response Logging

```
I need to implement Step 3 of Issue #165: Enhanced Debug Logging for LLM Calls.

Reference documents:
- Summary: pr_info/steps/summary.md
- Implementation guide: pr_info/steps/step_3.md
- Architectural overview: pr_info/steps/ARCHITECTURAL_OVERVIEW.md
- Step 1: pr_info/steps/step_1.md (completed)
- Step 2: pr_info/steps/step_2.md (completed)

## Task

Add request and response logging to `ask_claude_code_api()` function in 
`src/mcp_coder/llm/providers/claude/claude_code_api.py`.

## Requirements

### Part A: Request Logging

**Location**: Before calling `ask_claude_code_api_detailed_sync()`

```python
try:
    # Add this request logging:
    from .claude_code_cli import _log_llm_request_debug
    
    _log_llm_request_debug(
        method="api",
        provider="claude",
        session_id=session_id,
        command=None,  # API doesn't use command line
        prompt=question,
        timeout=timeout,
        env_vars=env_vars,
        cwd=cwd,
        mcp_config=None,  # API doesn't use mcp_config
    )
    
    # Then existing code continues:
    detailed = ask_claude_code_api_detailed_sync(...)
```

### Part B: Response Logging Helper

**Location**: New helper function in claude_code_api.py

```python
def _log_api_response_debug(detailed_response: dict[str, Any]) -> None:
    """Log API response metadata (cost, duration, usage, etc).
    
    Args:
        detailed_response: Full response dict from ask_claude_code_api_detailed_sync()
    """
    result_info = detailed_response.get("result_info", {})
    
    if not result_info:
        logger.debug("    Response:  {}")
        return
    
    logger.debug("    Response:")
    for key, value in result_info.items():
        logger.debug(f"                 {key}: {value}")
```

### Part C: Response Logging Call

**Location**: In `ask_claude_code_api()`, before return statement

```python
# Build response
response = create_api_response_dict(detailed["text"], actual_session_id, detailed)

# Add response logging:
_log_api_response_debug(detailed)

return response
```

### Response Fields to Log

Log all fields from result_info dict:
- `duration_ms`: Total time in milliseconds
- `duration_api_ms`: API call time in milliseconds
- `cost_usd`: Cost in USD
- `usage`: Dict with token counts
- `result`: Success/error status
- `num_turns`: Number of conversation turns
- `is_error`: Error flag (boolean)

### Testing

Add test cases to `tests/llm/providers/claude/test_claude_code_api.py`:

1. **test_ask_claude_code_api_logs_request_details**:
   - Verify logs before API call
   - Check for "Claude API execution [new]" header
   - Verify Method: api (not cli)
   - Verify no Command field (API only)
   - Verify all request fields present

2. **test_ask_claude_code_api_logs_response_metadata**:
   - Verify logs after API call
   - Check for "Response:" header
   - Verify duration_ms logged
   - Verify cost_usd logged
   - Verify usage dict logged
   - Verify num_turns logged
   - Verify is_error logged

3. **test_ask_claude_code_api_logs_resuming_session**:
   - Call with existing session_id
   - Verify "[resuming]" indicator in logs
   - Verify session_id shown in logs

### Mock Strategy

Mock:
- `ask_claude_code_api_detailed_sync()` - return detailed response dict
- Return response with sample values:
  ```python
  {
      'text': 'Test response',
      'session_info': {'session_id': 'session-123'},
      'result_info': {
          'duration_ms': 2801,
          'duration_api_ms': 2500,
          'cost_usd': 0.058779,
          'usage': {'input_tokens': 100, 'output_tokens': 50},
          'result': 'success',
          'num_turns': 1,
          'is_error': False,
      },
      'raw_messages': []
  }
  ```

Capture logs with pytest `caplog` at DEBUG level.

### Example Test

```python
def test_ask_claude_code_api_logs_response_metadata(mocker, caplog):
    """Verify API response metadata logging."""
    mock_response = {
        'text': 'Response text',
        'session_info': {'session_id': 'session-123'},
        'result_info': {
            'duration_ms': 2801,
            'duration_api_ms': 2500,
            'cost_usd': 0.058779,
            'usage': {'input_tokens': 100, 'output_tokens': 50},
            'result': 'success',
            'num_turns': 1,
            'is_error': False,
        },
        'raw_messages': []
    }
    
    mocker.patch(
        'mcp_coder.llm.providers.claude.claude_code_api.ask_claude_code_api_detailed_sync',
        return_value=mock_response
    )
    
    with caplog.at_level(logging.DEBUG):
        result = ask_claude_code_api("Test question")
    
    log_text = '\n'.join(r.message for r in caplog.records if r.levelname == 'DEBUG')
    
    # Verify request logging
    assert "Claude API execution [new]" in log_text
    assert "Method:    api" in log_text
    
    # Verify response logging
    assert "Response:" in log_text
    assert "duration_ms: 2801" in log_text
    assert "cost_usd: 0.058779" in log_text
    assert "usage:" in log_text
    assert "num_turns: 1" in log_text
```

## Success Criteria

- ✅ Request logging added before detailed API call
- ✅ Response logging helper created
- ✅ Response logging added after response creation
- ✅ All parameters passed to request logging helper
- ✅ Response metadata extracted and logged
- ✅ Session status indicator shows [new] or [resuming]
- ✅ Function behavior unchanged (no breaking changes)
- ✅ Tests verify both request and response logging
- ✅ Tests verify session indicators
- ✅ pylint, mypy, pytest all pass
```

---

## Post-Implementation Verification Prompt

```
I have completed the implementation of Issue #165: Enhanced Debug Logging for LLM Calls.

The changes include:
- Step 1: Created _log_llm_request_debug() helper in claude_code_cli.py
- Step 2: Added request logging to ask_claude_code_cli()
- Step 3: Added request and response logging to ask_claude_code_api()

## Verification Tasks

1. **Run Code Quality Checks**:
   - pylint: mcp__code-checker__run_pylint_check()
   - pytest: mcp__code-checker__run_pytest_check(extra_args=["-n", "auto", ...])
   - mypy: mcp__code-checker__run_mypy_check()

2. **Test Logging Manually**:
   - Set logging level to DEBUG
   - Call ask_claude_code_cli() and verify output shows:
     - "Claude CLI execution [new]:" or "[resuming]"
     - All fields present: Provider, Method, Session, Command, Prompt, cwd, Timeout, env_vars
     - Proper formatting and alignment
   - Call ask_claude_code_api() and verify output shows:
     - "Claude API execution [new]:" or "[resuming]"
     - Request fields present (no Command field for API)
     - Response metadata: duration_ms, cost_usd, usage, etc.

3. **Verify No Breaking Changes**:
   - ask_claude_code_cli() still returns LLMResponseDict
   - ask_claude_code_api() still returns LLMResponseDict
   - Function signatures unchanged
   - All existing callers still work

4. **Check Test Coverage**:
   - Unit tests for _log_llm_request_debug()
   - Unit tests for ask_claude_code_cli() logging
   - Unit tests for ask_claude_code_api() logging
   - Test for prompt preview truncation
   - Test for command formatting
   - Test for [new] vs [resuming] indicators

## Expected Results

When running with DEBUG logging:

CLI Execution:
```
DEBUG:mcp_coder.llm.providers.claude.claude_code_cli:Claude CLI execution [new]:
DEBUG:mcp_coder.llm.providers.claude.claude_code_cli:    Provider:  claude
...
```

API Execution:
```
DEBUG:mcp_coder.llm.providers.claude.claude_code_api:Claude API execution [resuming]:
DEBUG:mcp_coder.llm.providers.claude.claude_code_api:    Provider:  claude
...
DEBUG:mcp_coder.llm.providers.claude.claude_code_api:    Response:
DEBUG:mcp_coder.llm.providers.claude.claude_code_api:                 duration_ms: 2801
...
```

All code quality checks passing, all tests passing, no breaking changes.
```

---

## Notes for LLM Implementation

1. **Follow the step documents closely** - They contain specific formatting requirements
2. **Test format matters** - Logging output must match the examples exactly (indentation, field order, etc.)
3. **Use DEBUG level** - Only logger.debug(), not logger.info()
4. **Mock subprocess** - Tests should mock execute_subprocess to avoid real CLI calls
5. **Verify alignment** - Field labels should align at column 17 (after indent + "Label: ")
6. **Prompt truncation** - Must show ellipsis only if > 250 chars
7. **Session indicator** - "new" for None, "resuming" for existing session_id

---

**Each prompt should be used sequentially. Step 1 must be complete before Step 2, Step 2 before Step 3.**
