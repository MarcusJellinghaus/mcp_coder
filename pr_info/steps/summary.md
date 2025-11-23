# Issue #165: Enhanced Debug Logging for LLM Calls

## Problem

Current debug logging is minimal and doesn't show execution context (env vars, cwd, command details) or response metadata.

## Solution

Add comprehensive DEBUG-level logging for LLM calls:
- **Request logging**: Show what we're sending (prompt, env, command, etc.)
- **Response logging**: Show what we got back (duration, tokens, cost)
- **Error logging**: Show what failed and why

## Implementation

Create `src/mcp_coder/llm/providers/claude/logging_utils.py` with 3 helpers:
1. `log_llm_request()` - Log before execution
2. `log_llm_response()` - Log after success
3. `log_llm_error()` - Log on failure

Use these helpers in:
- `claude_code_cli.py` - CLI execution
- `claude_code_api.py` - API execution

## Changes

| File | Change |
|------|--------|
| `src/mcp_coder/llm/providers/claude/logging_utils.py` | **Create** - 3 logging helpers (~80 lines) |
| `src/mcp_coder/llm/providers/claude/claude_code_cli.py` | Add logging calls (~20 lines) |
| `src/mcp_coder/llm/providers/claude/claude_code_api.py` | Add logging calls (~20 lines) |
| `tests/llm/providers/claude/test_logging_utils.py` | **Create** - Unit tests (~60 lines) |
| `tests/llm/providers/claude/test_claude_code_cli.py` | Add logging tests (~20 lines) |
| `tests/llm/providers/claude/test_claude_code_api.py` | Add logging tests (~20 lines) |

**Total**: ~220 lines

## Design Decisions

1. **New module** - Separate `logging_utils.py` keeps logging code organized
2. **DEBUG level only** - No production impact
3. **Log at provider boundary** - All callers benefit automatically
4. **Log full env_vars** - DEBUG logs are private/trusted
5. **250 char prompt preview** - Balance detail vs log volume
6. **Test content only** - Verify fields exist, not formatting

## Benefits

- ✅ Easy troubleshooting (see full context)
- ✅ No breaking changes
- ✅ Clean separation (logging isolated)
- ✅ Low risk (~220 lines)
