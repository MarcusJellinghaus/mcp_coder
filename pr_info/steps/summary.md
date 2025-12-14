# Issue #193: Fix update_workflow_label to Remove All Workflow Labels

## Problem Statement

When `IssueManager.update_workflow_label()` transitions from one label to another, it only removes the specific `from_label`. If a different workflow label is present on the issue, it remains, resulting in multiple workflow labels.

**Production Example (Issue #192):**
- Issue had label `status-05:plan-ready`
- Called `update_workflow_label("implementing", "code_review")`
- Expected: Only `status-07:code-review`
- Actual: Both `status-05:plan-ready` AND `status-07:code-review`

## Root Cause

In `src/mcp_coder/utils/github_operations/issue_manager.py`, line ~372:

```python
new_labels = (current_labels - {from_label_name}) | {to_label_name}
```

This only removes the expected `from_label`. When a different workflow label is present, the subtraction removes nothing.

## Solution

Remove **all workflow labels** using `label_lookups["all_names"]` before adding the target label:

```python
new_labels = (current_labels - label_lookups["all_names"]) | {to_label_name}
```

## Files to Modify

| File | Change |
|------|--------|
| `src/.../issue_manager.py` | Fix line ~372, add INFO log |
| `tests/.../test_issue_manager_label_update.py` | Update test + add new test |

## Implementation Steps

| Step | Description |
|------|-------------|
| 1 | Add tests for "wrong workflow label" scenario (TDD) |
| 2 | Fix `update_workflow_label()` logic + add INFO log |

## Success Criteria

1. Transitioning labels removes ALL workflow labels, not just the expected source
2. Non-workflow labels (e.g., `bug`, `enhancement`) are preserved
3. INFO log when source label is not present
4. All existing tests pass
