# Issue #189: Implement Workflow Failure Handling and Error UX

## Problem

When the implement workflow fails, the issue stays stuck at `status-06:implementing` with no indication of failure. Error details are buried in logs, uncommitted changes are invisible, and the post-error task tracker display is confusing.

## Design Changes

### New data structures (`constants.py`)

- **`FailureCategory` enum**: Three values that map 1:1 to label `internal_id` values in `labels.json`:
  - `GENERAL = "implementing_failed"` — catch-all for formatting, commit, mypy, generic LLM errors
  - `CI_FIX_EXHAUSTED = "ci_fix_needed"` — after 3 CI fix attempts fail
  - `LLM_TIMEOUT = "llm_timeout"` — `TimeoutExpired` from LLM calls
- **`WorkflowFailure` frozen dataclass**: `category`, `stage`, `message`, `tasks_completed`, `tasks_total`

### Centralized failure handler (`core.py`)

- **`_handle_workflow_failure(failure, project_dir)`** — single function that:
  1. Sets failure label via `IssueManager.update_workflow_label(from_label_id="implementing", to_label_id=failure.category.value)`
  2. Posts structured GitHub comment (markdown with headings: category, stage, error, progress, uncommitted changes)
  3. Gets uncommitted changes via `git diff --stat` (inline gitpython call)
  4. Logs a prominent failure banner

### Workflow changes (`core.py`)

- **`update_labels` parameter removed** — labels always transition. Success → `code_review`, failure → appropriate failure label
- **Prerequisite failures** (`check_git_clean`, `check_main_branch`) return early without touching labels — workflow never started
- **Post-error `log_progress_summary` removed** — progress info is in the failure banner instead

### Task processing changes (`task_processing.py`)

- `process_single_task()` returns `"timeout"` (instead of `"error"`) when `TimeoutExpired` is caught — enables `core.py` to pick the right `FailureCategory`

### CLI changes

- `--update-labels` CLI argument removed from `parsers.py` and `commands/implement.py`

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/workflows/implement/constants.py` | Add `FailureCategory` enum + `WorkflowFailure` dataclass |
| `src/mcp_coder/workflows/implement/task_processing.py` | Catch `TimeoutExpired` explicitly, return `"timeout"` |
| `src/mcp_coder/workflows/implement/core.py` | Add `_handle_workflow_failure()`, wire into all error paths, remove `update_labels`, always transition labels, remove post-error progress display |
| `src/mcp_coder/workflows/implement/__init__.py` | Export `WorkflowFailure`, `FailureCategory` |
| `src/mcp_coder/cli/parsers.py` | Remove `--update-labels` from implement parser |
| `src/mcp_coder/cli/commands/implement.py` | Remove `update_labels` extraction and passing |
| `tests/workflows/implement/test_core.py` | Tests for failure handler, label transitions, removed `update_labels` |
| `tests/workflows/implement/test_task_processing.py` | Test `TimeoutExpired` → `"timeout"` return |
| `tests/cli/commands/test_implement.py` | Remove `update_labels` references from tests |

## Architecture Notes

- `FailureCategory.value` **is** the label `internal_id` — no mapping table needed, direct pass-through to `update_workflow_label()`
- `_handle_workflow_failure()` is a private module function, not a method — it's workflow-specific, not reusable across workflows
- `IssueManager` is instantiated inside `_handle_workflow_failure()` (same pattern as the existing success path)
- `git diff --stat` uses gitpython's `repo.git.diff("--stat")` — no new helper function needed
- Issue number extraction from branch is handled internally by `update_workflow_label()` — no extra logic needed
