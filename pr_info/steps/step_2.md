# Step 2: Add CLI Request Logging to ask_claude_code_cli()

## Where

**File**: `src/mcp_coder/llm/providers/claude/claude_code_cli.py`

**Location**: In `ask_claude_code_cli()` function, after command is built but before subprocess execution

**Line Context**: After `command = build_cli_command(...)` and before `options = CommandOptions(...)`

## What

Call the logging helper (from Step 1) to log CLI execution details, then execute the command as before.

### Change Type
- **Modification**: Add 1 function call + 1 comment line
- **Non-breaking**: Existing code behavior unchanged
- **Logging only**: No execution path changes

## How

### Pseudocode

```
1. After building the CLI command
2. Call _log_llm_request_debug() with all CLI parameters:
   - method="cli"
   - provider="claude"
   - session_id=<from parameter>
   - command=<built command list>
   - prompt=<question>
   - timeout=<timeout>
   - env_vars=<env_vars>
   - cwd=<cwd>
   - mcp_config=<mcp_config>
3. Continue with existing subprocess execution code
```

## Algorithm

```python
# After: command = build_cli_command(session_id, claude_cmd, mcp_config)

# Log comprehensive request details
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

# Existing code continues: options = CommandOptions(...)
```

## Code Changes

### Current Code Location
File: `src/mcp_coder/llm/providers/claude/claude_code_cli.py`

Function: `ask_claude_code_cli()`

Around line: ~164 (after `command = build_cli_command(...)`)

### Exact Change

**Before**:
```python
    # Build command with optional --resume and --mcp-config (pure function)
    command = build_cli_command(session_id, claude_cmd, mcp_config)

    # Execute command with stdin input (I/O)
    # cwd parameter controls where Claude subprocess runs
    # This affects .mcp.json discovery and relative path resolution
    logger.debug(
        f"Executing CLI command with stdin (prompt_len={len(question)}, "
        f"session_id={session_id}, cwd={cwd})"
    )
```

**After**:
```python
    # Build command with optional --resume and --mcp-config (pure function)
    command = build_cli_command(session_id, claude_cmd, mcp_config)

    # Log comprehensive request details (includes env vars, cwd, command, prompt, etc.)
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

    # Execute command with stdin input (I/O)
    # cwd parameter controls where Claude subprocess runs
    # This affects .mcp.json discovery and relative path resolution
    # Old brief logging line can be removed (replaced by comprehensive logging above)
```

## Data Structures

### Input Parameters (passed to logger)
- `method`: str = "cli"
- `provider`: str = "claude"
- `session_id`: str | None (from function parameter)
- `command`: list[str] (from build_cli_command())
- `prompt`: str (from question parameter)
- `timeout`: int (from timeout parameter)
- `env_vars`: dict[str, str] | None (from function parameter)
- `cwd`: str | None (from function parameter)
- `mcp_config`: str | None (from function parameter)

### Return Value
- **Type**: `None`
- **Side Effect**: Debug logs are written (from helper function)

## Testing

**Test File**: `tests/llm/providers/claude/test_claude_code_cli.py`

**Test Case Name**: `test_ask_claude_code_cli_logs_request_details`

### Test Approach
```python
def test_ask_claude_code_cli_logs_request_details(caplog, mocker):
    """Verify CLI request logging is comprehensive."""
    # Mock the subprocess execution
    mocker.patch('mcp_coder.llm.providers.claude.claude_code_cli.execute_subprocess')
    # Mock Claude executable finder
    mocker.patch('mcp_coder.llm.providers.claude.claude_code_cli._find_claude_executable', 
                 return_value='claude')
    
    # Capture logs at DEBUG level
    with caplog.at_level(logging.DEBUG):
        # Make a test call
        ask_claude_code_cli(
            "Test question",
            session_id="test-session",
            timeout=60,
            env_vars={"TEST": "value"},
            cwd="/test/cwd",
            mcp_config=".mcp.json"
        )
    
    # Verify logs contain expected fields
    debug_logs = [r for r in caplog.records if r.levelname == 'DEBUG']
    log_text = '\n'.join(r.message for r in debug_logs)
    
    # Check for key fields in logs
    assert "Claude CLI execution [new]" in log_text  # New session
    assert "Provider:  claude" in log_text
    assert "Method:    cli" in log_text
    assert "Session:   test-session" in log_text
    assert "Prompt:    12 chars" in log_text  # len("Test question")
    assert "Timeout:   60s" in log_text
    assert "cwd:       /test/cwd" in log_text
```

### Test Cases to Add

1. **New Session Logging**: Verify "[new]" indicator when session_id=None
2. **Resuming Session Logging**: Verify "[resuming]" indicator when session_id provided
3. **Prompt Preview Truncation**: Verify ellipsis when prompt > 250 chars
4. **Command Formatting**: Verify multi-line command with proper indentation
5. **Environment Variables**: Verify env_vars dict logged correctly
6. **None Values**: Verify None values displayed as "None" not blank

## Files to Create/Modify

| File | Type | Details |
|------|------|---------|
| `src/mcp_coder/llm/providers/claude/claude_code_cli.py` | Modify | Add logging call in `ask_claude_code_cli()` |
| `tests/llm/providers/claude/test_claude_code_cli.py` | Modify | Add test cases for request logging |

## Integration Points

- **Imports**: Already has `logging` and helper function from Step 1
- **Function Called**: `_log_llm_request_debug()` from Step 1
- **Called By**: `ask_claude_code_cli()` entry point
- **Decorators**: None needed

## Success Criteria

- ✅ Logging call added to `ask_claude_code_cli()`
- ✅ All parameters passed to logging helper
- ✅ Old brief debug line still works (or removed if superseded)
- ✅ Existing CLI functionality unchanged
- ✅ Test verifies comprehensive logging output
- ✅ No breaking changes to function signature
- ✅ Code quality checks pass

## Example Log Output

When user runs:
```python
result = ask_claude_code_cli(
    "Implement feature X",
    session_id=None,
    timeout=3600,
    env_vars={'MCP_CODER_PROJECT_DIR': '/home/user/project'},
    cwd='/home/user/project',
    mcp_config='.mcp.json'
)
```

Should log:
```
DEBUG:mcp_coder.llm.providers.claude.claude_code_cli:Claude CLI execution [new]:
DEBUG:mcp_coder.llm.providers.claude.claude_code_cli:    Provider:  claude
DEBUG:mcp_coder.llm.providers.claude.claude_code_cli:    Method:    cli
DEBUG:mcp_coder.llm.providers.claude.claude_code_cli:    Command:   /usr/bin/claude
DEBUG:mcp_coder.llm.providers.claude.claude_code_cli:                 -p ""
DEBUG:mcp_coder.llm.providers.claude.claude_code_cli:                 --output-format json
DEBUG:mcp_coder.llm.providers.claude.claude_code_cli:                 --mcp-config .mcp.json
DEBUG:mcp_coder.llm.providers.claude.claude_code_cli:                 --strict-mcp-config
DEBUG:mcp_coder.llm.providers.claude.claude_code_cli:    Session:   None
DEBUG:mcp_coder.llm.providers.claude.claude_code_cli:    Prompt:    21 chars - Implement feature X
DEBUG:mcp_coder.llm.providers.claude.claude_code_cli:    cwd:       /home/user/project
DEBUG:mcp_coder.llm.providers.claude.claude_code_cli:    Timeout:   3600s
DEBUG:mcp_coder.llm.providers.claude.claude_code_cli:    env_vars:  {'MCP_CODER_PROJECT_DIR': '/home/user/project'}
DEBUG:mcp_coder.llm.providers.claude.claude_code_cli:    MCP config: .mcp.json
```

(Note: Each field on separate debug call, or combined into single multi-line debug call - implementation decision)
