# Issue #388: Git Merge-Base Detection for PR Creation

## Problem Summary

When creating a PR for a feature branch based on another feature branch (not `main`), the diff is miscalculated because `get_parent_branch_name()` always returns `main`/`master`, ignoring the actual parent branch.

**Example:** `main` → `feature-A` → `feature-B`
- **Expected:** PR diff shows only `feature-B` changes (vs `feature-A`)
- **Actual:** PR diff shows ALL changes from both branches (vs `main`)

## Solution Overview

Implement git merge-base detection as the **primary** method in `detect_base_branch()`, replacing the flawed `get_parent_branch_name()` function entirely.

## Architectural Changes

### 1. Detection Priority (NEW)
```
1. Git merge-base (PRIMARY) - Detect actual parent from git history
2. GitHub PR base branch    - If PR already exists for current branch  
3. GitHub Issue section     - Explicit `### Base Branch` in issue body
4. Default branch           - main/master fallback
5. Return None              - If all detection fails
```

### 2. Return Type Change
- **Before:** `detect_base_branch()` returns `str` (with `"unknown"` fallback)
- **After:** `detect_base_branch()` returns `Optional[str]` (`None` on failure)

### 3. Function Removal
- **Remove:** `get_parent_branch_name()` from `readers.py` and all re-exports
- **Rationale:** Function was a thin wrapper that always returned `main`/`master`

### 4. Simplified `diffs.py`
- **Remove:** Auto-detection logic from `get_branch_diff()`
- **Change:** If `base_branch` is `None`, return empty string with error log
- **Rationale:** Avoids cross-layer dependency (utils → workflow_utils)

## Files to Modify

| File | Action | Description |
|------|--------|-------------|
| `src/mcp_coder/workflow_utils/base_branch.py` | MODIFY | Add merge-base detection, change return type |
| `src/mcp_coder/utils/git_operations/readers.py` | MODIFY | Remove `get_parent_branch_name()` |
| `src/mcp_coder/utils/git_operations/__init__.py` | MODIFY | Remove re-export |
| `src/mcp_coder/utils/__init__.py` | MODIFY | Remove re-export |
| `src/mcp_coder/utils/git_operations/diffs.py` | MODIFY | Remove auto-detection, require explicit base_branch |
| `src/mcp_coder/workflows/create_pr/core.py` | MODIFY | Use `detect_base_branch()`, handle `None` |
| `src/mcp_coder/workflows/implement/core.py` | MODIFY | Update `None` check (was `"unknown"`) |
| `tests/workflow_utils/test_base_branch.py` | MODIFY | Add merge-base tests, update for `None` |
| `tests/utils/git_operations/test_readers.py` | MODIFY | Remove `get_parent_branch_name` tests |
| `tests/utils/git_operations/test_diffs.py` | MODIFY | Update for explicit base_branch requirement |
| `tests/workflows/create_pr/test_*.py` | MODIFY | Update mocks |
| `tests/workflows/implement/test_core.py` | MODIFY | Update `None` check |

## Key Constants

```python
# Maximum commits between merge-base and candidate branch HEAD
# Higher = more permissive but risk wrong branch selection
# Lower = may miss valid parents that moved forward
MERGE_BASE_DISTANCE_THRESHOLD = 20
```

## Algorithm: `_detect_from_git_merge_base()`

```python
def _detect_from_git_merge_base(project_dir: Path, current_branch: str) -> Optional[str]:
    # 1. Get all local branches (excluding current)
    # 2. Get all remote branches (origin/*, excluding current and HEAD)
    # 3. For each candidate:
    #    - Find merge_base with current branch
    #    - Calculate distance = commits from merge_base to candidate HEAD
    #    - If distance <= THRESHOLD, add to passing candidates
    # 4. Return candidate with smallest distance, or None
```

## Test Scenarios (from issue)

1. **Branch from feature branch** - `feature-A` distance=0, `main` distance=15 → returns `feature-A`
2. **Parent moved forward** - `feature-A` distance=5, `main` distance=25 → returns `feature-A`  
3. **Parent moved too far** - `feature-A` distance=25 → falls through to PR/Issue/Default
4. **Multiple candidates** - `feature-A` distance=3, `develop` distance=8 → returns `feature-A`
5. **Simple case** - `main` distance=0 → returns `main`
6. **Remote only** - Local deleted, `origin/feature-A` distance=2 → returns `feature-A`

## Implementation Steps

1. **Step 1:** Add merge-base detection to `base_branch.py` with tests
2. **Step 2:** Remove `get_parent_branch_name()` and update exports  
3. **Step 3:** Update `diffs.py` to remove auto-detection
4. **Step 4:** Update `create_pr/core.py` to use `detect_base_branch()`
5. **Step 5:** Update `implement/core.py` for `None` handling
