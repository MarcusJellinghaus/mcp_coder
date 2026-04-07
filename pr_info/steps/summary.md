# Summary: Bounded Retry + Checkbox-Tick Reminder for Zero-Change Task Loop

**Issue:** #711  
**Related:** #710 (root cause analysis)

## Problem

When the LLM completes a task without making file changes, `process_single_task` returns `(True, "completed")` but never ticks the checkbox in `TASK_TRACKER.md`. The main loop in `core.py` then calls `get_next_task()` and gets the **same task back**, causing an infinite loop.

## Solution

Bounded retry (max 3 LLM calls per task) with an on-retry dynamic prompt reminding the LLM to tick the checkbox. After 3 consecutive zero-change attempts, fail hard with a distinct failure category for diagnosability.

## Architectural / Design Changes

1. **New return contract for `process_single_task`**: Zero file changes now returns `(False, "no_changes")` instead of `(True, "completed")`. This is a breaking internal contract change — the function no longer lies about success when nothing happened.

2. **New orchestration layer**: `process_task_with_retry()` wraps `process_single_task` with retry logic. This follows the existing pattern where `check_and_fix_mypy` already has its own retry loop. `core.py` calls the wrapper instead of the inner function directly.

3. **New failure category**: `FailureCategory.NO_CHANGES_AFTER_RETRIES` added to the enum (with matching label in `labels.json`). This enables distinct failure routing, issue labeling, and analytics — consistent with existing categories like `CI_FIX_EXHAUSTED` and `LLM_TIMEOUT`.

4. **Prompt layering**: Static prompt strengthened for all calls; dynamic reminder appended only on retry attempts (attempt > 1). This avoids prompt bloat in the common case.

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/prompts/prompts.md` | Strengthen RULES section with checkbox-ticking emphasis |
| `src/mcp_coder/workflows/implement/constants.py` | Add `NO_CHANGES_AFTER_RETRIES` to `FailureCategory` enum; add `MAX_NO_CHANGE_RETRIES` constant |
| `src/mcp_coder/config/labels.json` | Add `no_changes_after_retries` label entry |
| `src/mcp_coder/workflows/implement/task_processing.py` | Add `attempt` param to `process_single_task`; change zero-changes return; add `process_task_with_retry()` wrapper |
| `src/mcp_coder/workflows/implement/core.py` | Call `process_task_with_retry` instead of `process_single_task`; route new failure reason |
| `tests/workflows/implement/test_constants.py` | Add assertion for new enum value |
| `tests/workflows/implement/test_task_processing.py` | Update no-changes test; add retry wrapper tests |
| `tests/workflows/implement/test_core.py` | Add reason routing test for `no_changes_after_retries` |
| `tests/workflows/test_label_config.py` | Add new label ID to `ERROR_STATUS_IDS` list |

## Files NOT Modified

- `src/mcp_coder/workflows/implement/__init__.py` — `process_task_with_retry` is internal plumbing, only called by `core.py` via relative import. No export needed.
- `src/mcp_coder/workflows/implement/prerequisites.py` — Unaffected.
- Finalisation workflow — Uses its own prompt and does not call `process_single_task`.
