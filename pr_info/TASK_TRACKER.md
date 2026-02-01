# Task Tracker: Stream Logging Enhancement

## Status Overview

| Step | Description | Status | Notes |
|------|-------------|--------|-------|
| 0 | Stream-JSON output implementation | ✅ Complete | Committed: 6256668 |
| 1 | Refactor test file (CI compliance) | ✅ Complete | Split into 3 files |
| 2 | Add branch_name to LLM call sites | 🔲 Pending | Depends on Step 1 |

## Current State

**Branch:** `fix_stream_log`
**Last Commit:** `6256668` - feat(logging): add stream-json output with session logging

## Step 0: Stream-JSON Implementation ✅

### Completed Tasks
- [x] Switch to `--output-format stream-json` with `--verbose`
- [x] Add NDJSON stream logging to `logs/claude-sessions/`
- [x] Implement stream parsing functions
- [x] Add `branch_name` parameter to CLI functions
- [x] Add cost/usage tracking from result messages
- [x] Create integration tests
- [x] Update existing tests for new output format
- [x] Commit and push changes

### Files Modified
- `src/mcp_coder/llm/interface.py`
- `src/mcp_coder/llm/providers/claude/claude_code_cli.py`
- `src/mcp_coder/llm/providers/claude/claude_code_interface.py`
- `tests/llm/providers/claude/test_claude_cli_stream_integration.py` (new)
- `tests/llm/providers/claude/test_claude_code_cli.py`
- `tests/llm/providers/claude/test_claude_code_interface.py`
- `tests/llm/providers/claude/test_llm_sessions.py`
- `tests/llm/test_interface.py`
- `tests/unit/llm/providers/claude/test_claude_mcp_config.py`

## Step 1: Refactor Test File ✅

### Tasks
- [x] Create `test_claude_cli_stream_parsing.py` with stream-related tests (293 lines)
- [x] Create `test_claude_cli_wrappers.py` with IO/logging tests (269 lines)
- [x] Update `test_claude_code_cli.py` to remove moved classes (368 lines)
- [x] Verify all tests pass (1599 tests passed)
- [x] Verify file sizes under 750 lines
- [ ] Commit changes

### Files to Create/Modify
- `tests/llm/providers/claude/test_claude_cli_stream_parsing.py` (new)
- `tests/llm/providers/claude/test_claude_cli_wrappers.py` (new)
- `tests/llm/providers/claude/test_claude_code_cli.py` (reduce)

### Result
All test files now under 750 lines. CI file size check passes.

## Step 2: Add Branch Name to LLM Calls 🔲

### Tasks
- [ ] Add `get_branch_name_for_logging()` utility function
- [ ] Add tests for utility function
- [ ] Update `workflows/implement/core.py` (4 call sites)
- [ ] Update `workflows/implement/task_processing.py` (2 call sites)
- [ ] Update `workflows/create_plan.py` (3 call sites)
- [ ] Update `workflows/create_pr/core.py` (1 call site)
- [ ] Update `workflow_utils/commit_operations.py` (1 call site)
- [ ] Update `cli/commands/prompt.py` (2 call sites)
- [ ] Verify all tests pass
- [ ] Commit changes

### Files to Modify
- `src/mcp_coder/utils/git_utils.py` (add function)
- `tests/utils/test_git_utils.py` (add tests)
- 6 workflow/CLI files (13 call sites total)

## Dependencies

```
Step 0 (Complete)
    │
    ▼
Step 1 (Required for CI)
    │
    ▼
Step 2 (Feature completion)
```

## Notes

- Step 1 is blocking - CI will fail until test file is split
- Step 2 can be done incrementally (file by file) if needed
- All steps should maintain backward compatibility
