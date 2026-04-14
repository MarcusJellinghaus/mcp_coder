# Issue #759: Reorder cleanup before push and PR creation

## Summary

Reorder the `create-pr` workflow in `run_create_pr_workflow()` so that repository cleanup happens **before** pushing and PR creation. This ensures the PR diff is clean from the start.

**Current order:** Prerequisites → Generate summary → Push → Create PR → Cleanup → Push cleanup
**New order:** Prerequisites → Generate summary → **Cleanup** → Push → Create PR

## Architectural / Design Changes

This is a **reorder-only change** within a single function (`run_create_pr_workflow` in `core.py`). No new modules, classes, or functions are introduced. No interfaces change.

Key design implications of the reorder:

1. **Single push instead of two**: The current flow pushes once before PR creation, then again after cleanup. The new flow does cleanup first, so a single push covers both feature commits and the cleanup commit.

2. **Cleanup failure is now pre-PR**: Since cleanup moves before PR creation, the cleanup error handler no longer has access to `pr_url`/`pr_number` (the PR doesn't exist yet). The `_handle_create_pr_failure` calls for cleanup stage drop these kwargs.

3. **Step 5 consolidates PR creation + fallback + labels**: The closing-issues-references fallback and label update move into step 5 alongside PR creation, since they all require the PR to exist.

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/workflows/create_pr/core.py` | Reorder steps 3-5 in `run_create_pr_workflow()`, update step log messages, change commit message, simplify cleanup error handler |
| `tests/workflows/create_pr/test_workflow.py` | Update test expectations for new step order (push count, call order) |
| `tests/workflows/create_pr/test_failure_handling.py` | Update cleanup failure tests (no `pr_url`/`pr_number`/`is_cleanup_failure`, remove second push test) |

No files created or deleted.

## Steps Overview

| Step | Description |
|------|-------------|
| 1 | Update tests for new workflow order (`test_workflow.py` + `test_failure_handling.py`) and reorder `run_create_pr_workflow()` in `core.py` |
