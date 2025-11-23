# Issue #165: Enhanced Debug Logging for LLM Calls - Implementation Plan

## Overview

This implementation adds comprehensive DEBUG-level logging to Claude Code provider functions to make troubleshooting easier. The approach follows the **KISS principle** with minimal changes and zero architectural refactoring.

## Documents in This Directory

| Document | Purpose |
|----------|---------|
| `summary.md` | High-level overview, problem statement, solution approach, files to modify |
| `step_1.md` | Create reusable logging helper function |
| `step_2.md` | Add CLI request logging to `ask_claude_code_cli()` |
| `step_3.md` | Add API request and response logging to `ask_claude_code_api()` |
| `IMPLEMENTATION_GUIDE.md` | Step-by-step checklist, testing strategy, verification steps |
| `README.md` | This file |

## Quick Facts

- **Files Modified**: 2 (both in `src/mcp_coder/llm/providers/claude/`)
- **Files Created**: 0
- **Files Deleted**: 0
- **Lines Added**: ~200 (half code, half tests)
- **Architectural Changes**: None
- **Breaking Changes**: None
- **Risk Level**: Low
- **Complexity**: Low (logging only, no execution changes)

## The Approach

### Old Way (Not Implemented)
- Move `_call_llm_with_comprehensive_capture()` function to central location
- Refactor multiple callers to use centralized function
- Change architecture to have single point of LLM execution
- Higher risk, more code changes, potential for regressions

### Our Way ✓ (KISS Principle)
- Add logging directly in provider entry points
- Two functions: `ask_claude_code_cli()` and `ask_claude_code_api()`
- Create one reusable logging helper
- All callers automatically benefit (no caller changes needed)
- Lower risk, minimal code, clear and simple

## What Gets Logged

### Request Details (Before Execution)
- **Provider**: 'claude'
- **Method**: 'cli' or 'api'
- **Session Status**: [new] or [resuming]
- **Command**: Full CLI command with arguments (CLI only)
- **Prompt Preview**: First 250 chars with character count
- **Working Directory**: Where Claude subprocess executes
- **Timeout**: Request timeout in seconds
- **Environment Variables**: Full dict of env vars
- **MCP Config**: Path to MCP configuration file

### Response Details (After Execution, API Only)
- **Duration**: Total duration and API duration in milliseconds
- **Cost**: USD cost of the request
- **Usage**: Input/output token counts
- **Result**: Success/error status
- **Turns**: Number of conversation turns
- **Error Flag**: Whether response was an error

## Architecture Diagram

```
Current Implementation:

    ask_llm() ──┐
               │
    prompt_llm() ──┤──→ ask_claude_code_cli() ──→ [LOGGING] ──→ execute_subprocess()
               │                                    (NEW)
    generate_commit_message_with_llm() ──┤
                                        │
                                        └──→ ask_claude_code_api() ──→ [LOGGING] ──→ ask_claude_code_api_detailed_sync()
                                                                        (NEW)

All callers benefit from enhanced logging with ZERO changes to caller code.
```

## Implementation Flow

```
Step 1: Create Helper
  ↓
  └─→ Define _log_llm_request_debug() in claude_code_cli.py
      - Formats request details
      - Handles CLI and API parameters
      - Outputs aligned, multi-line debug logs
  
Step 2: Add CLI Logging
  ↓
  └─→ Call helper in ask_claude_code_cli()
      - Before subprocess execution
      - Shows [new] or [resuming]
      - Tests verify format
  
Step 3: Add API Logging
  ↓
  └─→ Call helper + new response helper in ask_claude_code_api()
      - Request logging (same as CLI)
      - Response metadata logging (API-specific)
      - Tests verify both request and response

Run code quality checks after each step.
```

## Testing Approach

Each step includes unit tests that:
1. Mock underlying functions to avoid real API/CLI calls
2. Capture DEBUG logs using pytest `caplog` fixture
3. Assert on log content and format
4. Verify [new] vs [resuming] session indicators
5. Check prompt preview truncation with ellipsis

**No integration tests needed** - We're just adding logging, not changing execution logic.

## Key Files

### Before (Current)
```
src/mcp_coder/llm/providers/claude/
├── claude_code_cli.py          (has ask_claude_code_cli())
├── claude_code_api.py          (has ask_claude_code_api())
└── [other files unchanged]
```

### After (Step 1-3 Complete)
```
src/mcp_coder/llm/providers/claude/
├── claude_code_cli.py          (+ _log_llm_request_debug() helper)
│                               (+ logging call in ask_claude_code_cli())
├── claude_code_api.py          (+ logging call in ask_claude_code_api())
│                               (+ _log_api_response_debug() helper)
└── [other files unchanged]
```

## Example Output

When running with `--log-level DEBUG`:

```
DEBUG:mcp_coder.llm.providers.claude.claude_code_cli:Claude CLI execution [new]:
DEBUG:mcp_coder.llm.providers.claude.claude_code_cli:    Provider:  claude
DEBUG:mcp_coder.llm.providers.claude.claude_code_cli:    Method:    cli
DEBUG:mcp_coder.llm.providers.claude.claude_code_cli:    Command:   /usr/bin/claude
DEBUG:mcp_coder.llm.providers.claude.claude_code_cli:                 -p ""
DEBUG:mcp_coder.llm.providers.claude.claude_code_cli:                 --output-format json
DEBUG:mcp_coder.llm.providers.claude.claude_code_cli:    Session:   None
DEBUG:mcp_coder.llm.providers.claude.claude_code_cli:    Prompt:    21 chars - Implement feature X
DEBUG:mcp_coder.llm.providers.claude.claude_code_cli:    cwd:       /home/user/project
DEBUG:mcp_coder.llm.providers.claude.claude_code_cli:    Timeout:   3600s
DEBUG:mcp_coder.llm.providers.claude.claude_code_cli:    env_vars:  {'MCP_CODER_PROJECT_DIR': '/home/user/project', ...}
```

## Start Here

1. Read `summary.md` for context and problem statement
2. Read `IMPLEMENTATION_GUIDE.md` for checklist and testing strategy
3. Implement `step_1.md` - Create logging helper
4. Implement `step_2.md` - Add CLI logging
5. Implement `step_3.md` - Add API logging
6. Run code quality checks
7. Verify logging appears at DEBUG level

## Files Modified Summary

| File | Type | Scope |
|------|------|-------|
| `src/mcp_coder/llm/providers/claude/claude_code_cli.py` | Source | Add helper function + logging call |
| `src/mcp_coder/llm/providers/claude/claude_code_api.py` | Source | Add logging call + response helper |
| `tests/llm/providers/claude/test_claude_code_cli.py` | Tests | Add logging format tests |
| `tests/llm/providers/claude/test_claude_code_api.py` | Tests | Add request/response logging tests |

**Note**: All other files remain unchanged. No refactoring of interface.py, task_processing.py, or other modules needed.

## Success Definition

Implementation is successful when:

- ✅ All three steps completed
- ✅ Logging appears at DEBUG level for both CLI and API
- ✅ All fields present and properly formatted
- ✅ Session status shows [new] or [resuming] correctly
- ✅ Prompt preview truncates at 250 chars with ellipsis
- ✅ Command arguments properly indented (CLI)
- ✅ Response metadata logged (API)
- ✅ All code quality checks pass
- ✅ All tests pass
- ✅ No breaking changes to existing APIs
- ✅ No changes to other modules

## Questions or Issues?

Refer to the specific step document for:
- **Step 1**: Implementation details for logging helper
- **Step 2**: Integration points for CLI logging
- **Step 3**: Integration points for API logging
- **IMPLEMENTATION_GUIDE**: Testing strategy and verification

Each step document includes:
- WHERE: File locations and function names
- WHAT: Function signatures and what to add
- HOW: Pseudocode and algorithms
- DATA: Input parameters and return values
- TESTING: Unit test approach and examples
- SUCCESS CRITERIA: How to verify it's working
