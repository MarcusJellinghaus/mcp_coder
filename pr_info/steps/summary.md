# Issue #283: Commit Message File Mechanism

## Summary

Implement a reliable mechanism for the implementation workflow to capture and use commit messages prepared during implementation tasks. The LLM will write the commit message to a designated file (`pr_info/.commit_message.txt`), which `commit_changes()` will read and use instead of generating a new message via LLM.

## Problem Being Solved

1. **Ambiguous instructions**: Current prompt says "prepare commit message" without specifying where
2. **Wasted LLM call**: `commit_changes()` ignores any prepared message and generates a new one
3. **Unwanted file creation**: LLM may create arbitrary files when no location is specified

## Architectural / Design Changes

### No New Modules or Classes

This implementation follows KISS - no new abstractions, just targeted changes to existing code:

1. **Prompt Update**: Single line change specifying the file location
2. **File-based Communication**: Using `pr_info/.commit_message.txt` as a transient message passing mechanism between the LLM implementation task and the commit operation
3. **Defensive Cleanup**: File cleanup at iteration start prevents stale data from previous failed runs

### Data Flow (New)

```
┌─────────────────────┐     ┌──────────────────────────────┐     ┌─────────────────┐
│ LLM Implementation  │────▶│ pr_info/.commit_message.txt  │────▶│ commit_changes()│
│ Task                │     │ (transient file)             │     │                 │
└─────────────────────┘     └──────────────────────────────┘     └─────────────────┘
                                        │
                                        ▼ (deleted before git add)
                                   [not committed]
```

### Fallback Behavior

If the file doesn't exist or is empty, the existing LLM-generated commit message behavior is preserved (no breaking change).

## Files to Modify

| File | Change Type | Description |
|------|-------------|-------------|
| `src/mcp_coder/prompts/prompts.md` | Edit | Update prompt wording (~1 line) |
| `src/mcp_coder/workflows/implement/task_processing.py` | Edit | Add constant, cleanup, and file reading logic (~25 lines) |
| `tests/workflows/implement/test_task_processing.py` | Edit | Add tests for new functionality (~60 lines) |
| `.github/workflows/ci.yml` | Edit | Add forbidden file check (~5 lines) |

## Decisions

See [Decisions.md](Decisions.md) for discussion outcomes on:
- Cleanup function placement (at very start of `process_single_task()`)
- Invalid content handling (trust LLM, use `parse_llm_commit_response()` as-is)
- Test coverage scope (no extra test for deletion timing)

## Key Design Decisions

1. **File location**: `pr_info/.commit_message.txt` (dot prefix = transient/technical file)
2. **Format**: Plain text, UTF-8 encoding
3. **Deletion timing**: Before `git add` to prevent accidental commit
4. **Error handling**: Log commit message on failure so it's not lost
5. **Reuse existing parser**: Use `parse_llm_commit_response()` for header/body separation

## Implementation Steps Overview

1. **Step 1**: Update `prompts.md` - Add file location instruction
2. **Step 2**: Update `task_processing.py` - Add constant, cleanup, and commit message file handling (with tests)
3. **Step 3**: Update `ci.yml` - Add forbidden file check
