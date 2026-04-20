# Issue #803: Fix merge-base heuristic selecting unrelated branches as parent

## Problem

`detect_parent_branch_via_merge_base` measures distance in the **wrong direction**: `merge_base → candidate_HEAD`. This rewards stale/dormant branches (few commits since divergence) and penalizes active branches like `main` (many commits). Result: unrelated feature branches get selected as parent, causing wrong rebases and wrong PR base branches.

## Fix

Reverse the distance measurement to `merge_base → current_HEAD`. The true parent has the most recent merge-base with the current branch, meaning fewest commits between merge-base and current HEAD.

## Design Changes

**No architectural changes.** This is a single-function algorithm fix in `parent_branch_detection.py`:

1. **Reverse distance direction** — Change `iter_commits(merge_base..candidate_HEAD)` to `iter_commits(merge_base..current_HEAD)` in both local and remote branch loops
2. **Remove early exits** — Delete `if distance == 0: return` blocks (multiple candidates can tie at distance=0 with new metric)
3. **Add tiebreaker** — Sort by `(distance, 0 if default_branch else 1)` so the default branch wins on equal distance
4. **New import** — `get_default_branch_name` from `.branch_queries` (sibling module, no new dependency)

The function signature, return type, threshold constant (20), and all callers remain unchanged.

## Files

| Action | Path |
|--------|------|
| **Modified** | `src/mcp_coder/utils/git_operations/parent_branch_detection.py` |
| **Created** | `tests/utils/git_operations/__init__.py` |
| **Created** | `tests/utils/git_operations/test_parent_branch_detection.py` |

## Steps

| Step | Description |
|------|-------------|
| 1 | Create test file with tests for the corrected algorithm (TDD: tests fail against current code) |
| 2 | Fix the algorithm in `parent_branch_detection.py` (tests pass) |
