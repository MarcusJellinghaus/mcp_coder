# Implementation Guide - Enhanced LLM Debug Logging (#165)

## Quick Summary

Add DEBUG-level logging to Claude Code provider entry points to show execution context (env vars, cwd, command, prompt preview) and response metadata. **Zero refactoring, minimal changes (~100 LOC), low risk.**

## Implementation Order

1. **Step 1**: Create logging helper function (reusable)
2. **Step 2**: Add CLI request logging
3. **Step 3**: Add API request and response logging

## What Gets Modified

| File | Lines Added | Purpose |
|------|-------------|---------|
| `src/mcp_coder/llm/providers/claude/claude_code_cli.py` | ~50 | Add `_log_llm_request_debug()` helper + logging call in `ask_claude_code_cli()` |
| `src/mcp_coder/llm/providers/claude/claude_code_api.py` | ~50 | Add logging call in `ask_claude_code_api()` + `_log_api_response_debug()` helper |
| `tests/llm/providers/claude/test_claude_code_cli.py` | ~40 | Tests for CLI logging |
| `tests/llm/providers/claude/test_claude_code_api.py` | ~60 | Tests for API logging |

**Total**: ~200 lines added, 0 lines deleted, 0 files moved.

## No Changes Needed To

- ✅ `src/mcp_coder/llm/interface.py` (ask_llm, prompt_llm)
- ✅ `src/mcp_coder/workflows/implement/task_processing.py`
- ✅ `src/mcp_coder/utils/commit_operations.py`
- ✅ Any other files

## Key Design Decisions

### 1. Logging at Provider Boundary
- Log in `ask_claude_code_cli()` and `ask_claude_code_api()` 
- This is where execution actually happens
- All callers automatically benefit from this logging

### 2. Reusable Helper Function
- Single `_log_llm_request_debug()` function handles both CLI and API request logging
- Avoids code duplication between CLI and API modules
- Easy to maintain consistent format

### 3. DEBUG Level Only
- Won't affect production users
- Users running with `--log-level DEBUG` see full context
- No performance impact at default INFO level

### 4. No Architectural Changes
- No moving functions between modules
- No centralizing capture logic
- No refactoring existing code
- Minimizes risk and complexity

## Testing Strategy

### Unit Tests (per step)
Each step includes unit tests that:
1. Mock the underlying functions (CLI subprocess, API detailed call)
2. Capture DEBUG logs using pytest caplog
3. Verify log format and content

### Integration Tests (optional, for step 3)
Can verify end-to-end API logging with real Claude API (if needed).

### Test Markers
Tests should use appropriate pytest markers:
- `claude_cli_integration` for CLI tests (if they execute actual CLI)
- `claude_api_integration` for API tests (if they call real API)

## Code Quality

Run after each step:
```bash
mcp__code-checker__run_pylint_check
mcp__code-checker__run_pytest_check
mcp__code-checker__run_mypy_check
```

Or all three:
```bash
mcp__code-checker__run_all_checks
```

## Implementation Checklist

### Step 1 - Logging Helper Function
- [ ] Add `_log_llm_request_debug()` function to `claude_code_cli.py`
- [ ] Format log output with proper indentation and alignment
- [ ] Handle None values gracefully (show "None" not blank)
- [ ] Support both CLI and API parameters
- [ ] Add unit test for logging format
- [ ] Run code quality checks

### Step 2 - CLI Request Logging
- [ ] Add logging call in `ask_claude_code_cli()` after command build
- [ ] Pass all parameters to logging helper
- [ ] Remove old brief debug line if superseded
- [ ] Add test for CLI request logging
- [ ] Add test for [new] vs [resuming] session indicator
- [ ] Run code quality checks

### Step 3 - API Request and Response Logging
- [ ] Add request logging call before detailed API call
- [ ] Import logging helper from CLI module
- [ ] Add response logging helper function
- [ ] Add response logging call after response creation
- [ ] Add tests for API request logging
- [ ] Add tests for API response metadata logging
- [ ] Add test for [new] vs [resuming] session indicator
- [ ] Run code quality checks

## Logging Format Reference

### CLI Execution

```
Claude CLI execution [new]:
    Provider:  claude
    Method:    cli
    Command:   /usr/local/bin/claude
                 -p ""
                 --output-format json
                 --mcp-config .mcp.json
                 --strict-mcp-config
    Session:   None
    Prompt:    245 chars - First line of prompt...
    cwd:       /home/user/project
    Timeout:   3600s
    env_vars:  {'MCP_CODER_PROJECT_DIR': '/home/user/project', 'PYTHONUNBUFFERED': '1'}
    MCP config: .mcp.json
```

### API Execution (Request)

```
Claude API execution [resuming]:
    Provider:  claude
    Method:    api
    Session:   abc123def456
    Prompt:    89 chars - What is the meaning of life?
    cwd:       /home/user/project
    Timeout:   30s
    env_vars:  {'MCP_CODER_PROJECT_DIR': '/home/user/project'}
```

### API Response Metadata

```
    Response:
                 duration_ms: 2801
                 duration_api_ms: 2500
                 cost_usd: 0.058779
                 usage: {'input_tokens': 4, 'output_tokens': 5}
                 result: success
                 num_turns: 1
                 is_error: False
```

## Verification

After completing all steps, verify:

1. **Logging appears at DEBUG level**
   ```bash
   python -c "
   import logging
   logging.basicConfig(level=logging.DEBUG)
   # Run LLM call and check console output
   "
   ```

2. **All fields present in logs**
   - Provider, Method, Session, Command (CLI only), Prompt, cwd, Timeout, env_vars, MCP config
   - Response metadata for API (duration, cost, usage)

3. **Proper formatting**
   - Header with session status: "[new]" or "[resuming]"
   - Consistent indentation (4 spaces for fields, additional for nested)
   - Prompt preview: count + first 250 chars + ellipsis if truncated
   - Command: first arg on same line, rest indented further
   - Env vars: full Python dict representation

4. **Works for both methods**
   - CLI execution logs command and parameters
   - API execution logs request and response metadata

5. **Tests pass**
   ```bash
   mcp__code-checker__run_pytest_check(
       extra_args=["-n", "auto", "-m", 
       "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration"]
   )
   ```

## Troubleshooting

### Logs not appearing
- Check log level is set to DEBUG
- Verify logging module configured correctly
- Ensure logger.debug() calls are present in code

### Incorrect format
- Check indentation matches specification (4 spaces, 17 spaces for nested)
- Verify prompt preview includes ellipsis when > 250 chars
- Check session indicator shows [new] or [resuming]

### Tests failing
- Mock all subprocess calls (execute_subprocess, ask_claude_code_api_detailed_sync)
- Use caplog to capture DEBUG logs
- Verify log records at DEBUG level

## Related Files (No Changes Needed)

These files are called by the modified functions but don't need changes:
- `src/mcp_coder/llm/interface.py` - ask_llm, prompt_llm (callers)
- `src/mcp_coder/llm/providers/claude/claude_code_interface.py` - routing
- `src/mcp_coder/utils/subprocess_runner.py` - execution
- `src/mcp_coder/llm/env.py` - environment preparation
- All test utilities and fixtures

## Success Criteria

- ✅ DEBUG logging shows comprehensive context at provider boundary
- ✅ Logs include env vars, cwd, command (CLI), prompt preview, timeout
- ✅ API logs include response metadata (duration, cost, usage)
- ✅ Session status clearly indicated ([new] or [resuming])
- ✅ Zero refactoring of other modules
- ✅ No breaking changes to public APIs
- ✅ All code quality checks pass
- ✅ Tests verify logging format and content
