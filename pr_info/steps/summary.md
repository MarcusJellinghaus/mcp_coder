# Feature: Auto-Rebase Feature Branch onto Parent Before Implement Workflow

## Overview

Add automatic rebase functionality to the `implement` workflow that keeps feature branches up-to-date with their parent branch before processing tasks. The rebase is **non-blocking** - if conflicts are detected, the rebase is aborted and the workflow continues normally.

## Architectural Changes

### Design Decisions

1. **Simple boolean return type**: `rebase_onto_branch()` returns `bool` instead of a complex result type. All status logging is handled internally - the caller only needs to know "did it work or not" (and even then, it continues regardless).

2. **Workflow-local detection logic**: Parent branch detection (`_get_rebase_target_branch()`) is a private function in `core.py` rather than exported from `git_operations`. This keeps workflow-specific logic (PR lookup, BASE_BRANCH file) close to where it's used.

3. **Never fail workflow**: All rebase-related errors are logged but never cause workflow failure. The workflow always continues.

### Component Responsibilities

| Component | Responsibility |
|-----------|----------------|
| `branches.py` | Low-level git rebase operation with conflict detection/abort |
| `core.py` | Parent branch detection logic and workflow integration |

## Parent Branch Detection Priority

1. **GitHub PR base branch** - If open PR exists for current branch, use its `base_branch`
2. **Explicit configuration** - Read `pr_info/BASE_BRANCH` file (single line)
3. **Default fallback** - Use `get_default_branch_name()` (main/master)

## Files to Modify

| File | Action | Description |
|------|--------|-------------|
| `src/mcp_coder/utils/git_operations/branches.py` | MODIFY | Add `rebase_onto_branch()` function |
| `src/mcp_coder/utils/git_operations/__init__.py` | MODIFY | Export `rebase_onto_branch` |
| `src/mcp_coder/workflows/implement/core.py` | MODIFY | Add `_get_rebase_target_branch()` and integrate rebase step |
| `tests/utils/git_operations/test_branches.py` | MODIFY | Add tests for `rebase_onto_branch()` |
| `tests/workflows/implement/test_core.py` | MODIFY | Add tests for `_get_rebase_target_branch()` |

## Behavior Summary

```
After prerequisite checks pass:
1. Detect parent branch (PR base → BASE_BRANCH file → default)
2. Fetch from origin
3. Attempt rebase onto origin/<parent>
4. On conflict: abort rebase, log warning, continue
5. On success: log info, continue
6. On error: log warning, continue
```

## Logging Specification

| Level | Message |
|-------|---------|
| INFO | "Rebasing onto origin/{branch}..." |
| INFO | "Successfully rebased onto origin/{branch}" |
| INFO | "Already up-to-date with origin/{branch}" |
| WARNING | "Skipping rebase: merge conflicts detected" |
| WARNING | "Skipping rebase: {error_message}" |
| DEBUG | "Parent branch detected from: {source}" |
| DEBUG | "Could not detect parent branch for rebase" |
