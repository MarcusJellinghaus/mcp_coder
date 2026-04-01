# Summary: Dedicated Failure Label for Task Tracker Preparation

**Issue:** #677

## Problem

When task tracker preparation fails during `implement`, the issue gets the generic `status-06f:implementing-failed` label — the same label used for actual implementation failures. This makes it impossible to distinguish "task tracker prep failed" from "code implementation failed" by looking at the GitHub issue.

## Solution

Add a dedicated failure label `status-06f-prep:task-tracker-prep-failed` and corresponding `FailureCategory` enum member so task tracker prep failures are distinguishable from general implementation failures.

## Architectural / Design Changes

**No architectural changes.** This is a small, additive change that extends an existing pattern:

- The `FailureCategory` enum in `constants.py` already maps 1:1 to failure label IDs in `labels.json`. We add one new member.
- The `_handle_workflow_failure` function in `core.py` already resolves labels via `failure.category.value` — no plumbing changes needed.
- The label config validation tests already parametrize over error status IDs — we add one entry.

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/config/labels.json` | Add `task_tracker_prep_failed` label entry |
| `src/mcp_coder/workflows/implement/constants.py` | Add `TASK_TRACKER_PREP_FAILED` enum member |
| `src/mcp_coder/workflows/implement/core.py` | Change task tracker prep failure from `FailureCategory.GENERAL` to `FailureCategory.TASK_TRACKER_PREP_FAILED` |
| `tests/workflows/implement/test_constants.py` | Add assertion for new enum member |
| `tests/workflows/test_label_config.py` | Add `task_tracker_prep_failed` to `ERROR_STATUS_IDS` |

## Commits

- **Step 1:** Add label + enum member + tests (TDD: tests first, then production code)
- **Step 2:** Wire up the new failure category in `core.py`
