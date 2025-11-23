# Issue #165: Enhanced Debug Logging for LLM Calls

## Summary

Add comprehensive DEBUG-level logging to Claude Code provider functions to show execution context and response details. This enables easier troubleshooting without architectural changes.

## Problem

Current debug logging is minimal:
```
2025-11-02 15:19:32,412 - mcp_coder.llm.providers.claude.claude_code_cli - DEBUG - Executing CLI command with stdin (prompt_len=10525, session_id=None)
```

Users need to see environment variables, working directory, full command arguments, and response metadata when debugging.

## Solution

**Simplified Approach (KISS Principle)**: Add enhanced logging directly in the two provider entry points instead of refactoring architecture:

1. **`ask_claude_code_cli()`** - Log request details before CLI execution
2. **`ask_claude_code_api()`** - Log request details and response metadata after API call

## Design Changes

**Zero architectural refactoring** - adds logging only at provider boundaries:
- No moving functions
- No centralizing capture logic  
- No caller changes
- Minimal code additions (~50-100 lines total)

### Logging Format

All logs at **DEBUG level only**. Multiline format with aligned fields:

```
Claude CLI execution [new]:
    Provider:  claude
    Method:    cli
    Command:   claude.EXE
                 -p ""
                 --output-format json
    Session:   None
    Prompt:    10525 chars - First 250 characters of prompt...
    cwd:       C:\project
    Timeout:   3600s
    env_vars:  {'MCP_CODER_PROJECT_DIR': '/project', ...}
```

For API with response:
```
Claude API execution [resuming]:
    Provider:  claude
    Method:    api
    Session:   abc123def456
    ...
    Response:
                 duration_ms: 2801
                 cost_usd: 0.058779
                 usage: {'input_tokens': 4, 'output_tokens': 5}
```

## Files Changed

| File | Change | Reason |
|------|--------|--------|
| `src/mcp_coder/llm/providers/claude/claude_code_cli.py` | Add request logging in `ask_claude_code_cli()` | Log before execution |
| `src/mcp_coder/llm/providers/claude/claude_code_api.py` | Add request+response logging in `ask_claude_code_api()` | Log before and after execution |

**No files deleted, no files moved, no refactoring of other modules.**

## Test Strategy

- Unit tests mock logging to verify output format
- Integration tests capture DEBUG logs to verify completeness
- Verify both CLI and API methods log correctly
- Verify new vs resuming sessions show correct indicators

## Benefits

- ✅ Minimal changes (low risk)
- ✅ All logging at provider boundary (single point of logging effect)
- ✅ No breaking changes
- ✅ Easy to understand (logging next to execution)
- ✅ Achieves all issue requirements

## Implementation Steps

See `step_1.md` through `step_3.md` for detailed implementation.
