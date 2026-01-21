# Summary: commit_all_changes returns success when no changes to commit

## Issue Reference
**Issue #123**: commit_all_changes: return success when no changes to commit

## Problem Statement
When `commit_all_changes()` is called and there are no changes to commit, it currently:
- Logs ERROR: "No staged files to commit"
- Logs ERROR: "Staging succeeded but commit failed: No staged files to commit"
- Returns `success=False`

This causes confusing error messages for what is actually normal behavior (e.g., cleanup had nothing to clean).

## Solution Overview
Add a pre-check in `commit_all_changes()` using `get_full_status()` to detect if there are any changes before attempting to stage/commit. If no changes exist, return success early with `commit_hash=None`.

## Architectural / Design Changes

### Design Decision
- **Pre-check pattern**: Check for changes BEFORE attempting git operations, rather than catching failures after the fact
- **Scope boundary**: Only modify `commit_all_changes()` - keep `commit_staged_files()` strict (it should still fail if called with nothing staged)
- **Return semantics**: `success=True` with `commit_hash=None` indicates "operation completed successfully, but no commit was needed"

### No Architectural Changes
This is a behavioral fix within an existing function. No new modules, classes, or architectural patterns are introduced.

## Files to Modify

| File | Change Type | Description |
|------|-------------|-------------|
| `src/mcp_coder/utils/git_operations/commits.py` | Modify | Add pre-check for changes before staging/commit |
| `tests/utils/git_operations/test_commits.py` | Modify | Add test for "no changes" scenario |

## Implementation Steps

| Step | Description | TDD |
|------|-------------|-----|
| 1 | Add test and implement pre-check in `commit_all_changes()` | Yes |

## Acceptance Criteria
- [x] `commit_all_changes()` returns `success=True` when no changes exist
- [x] Logs at INFO level: "No changes to commit"
- [x] `commit_hash` is `None` when no commit was created
- [x] Existing callers continue to work correctly
- [x] Unit tests updated for new behavior
