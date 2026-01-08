# Issue #259: Clean up `pr_info/.conversations` in create_pr workflow

## Problem Statement

The `create_pr` CLI command cleans up `pr_info/steps/`, truncates `TASK_TRACKER.md`, and clears profiler output, but does NOT delete `pr_info/.conversations/`. This causes CI failures because `.github/workflows/ci.yml` explicitly forbids `pr_info/.conversations/` from being present in pull requests.

## Solution Overview

Add deletion of `pr_info/.conversations/` directory inline within the existing `cleanup_repository()` function, following the KISS principle. No new functions needed - just extend the existing cleanup logic.

## Architectural / Design Changes

**No architectural changes required.** This is a minor enhancement to existing functionality:

- **Pattern**: Inline code addition following existing `shutil.rmtree()` usage pattern
- **Location**: `cleanup_repository()` function in `src/mcp_coder/workflows/create_pr/core.py`
- **Approach**: Direct deletion with try/except error handling (same pattern as profiler cleanup)

## Files to Modify

| File | Change Type | Description |
|------|-------------|-------------|
| `src/mcp_coder/workflows/create_pr/core.py` | MODIFY | Add `.conversations` deletion in `cleanup_repository()`, update commit message |
| `tests/workflows/create_pr/test_repository.py` | MODIFY | Add integration test for `.conversations` cleanup |

## Implementation Steps

1. **Step 1**: Add test for `.conversations` directory cleanup (TDD)
2. **Step 2**: Implement `.conversations` deletion and update commit message

## Acceptance Criteria

- [ ] `pr_info/.conversations/` is deleted during `create_pr` workflow
- [ ] Cleanup changes are committed and pushed with appropriate message
- [ ] CI passes (no forbidden folders present)
- [ ] Tests added for the new cleanup functionality
