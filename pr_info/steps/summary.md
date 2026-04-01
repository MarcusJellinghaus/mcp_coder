# Issue #337: Create-pr workflow failure handling

## Summary

Enhance the create-pr workflow so that when any step fails, the issue transitions
from `status-09:pr-creating` to `status-09f:pr-creating-failed` and a GitHub
comment is posted with failure details (stage, error, elapsed time, PR link if
available).

## Architectural / Design Changes

### 1. New shared module: `workflow_utils/failure_handling.py`

Extracts failure handling logic currently embedded in `implement/core.py` into a
reusable module. Both implement and create-pr workflows will use it.

**What moves to the shared module:**
- `_get_diff_stat()` → `get_diff_stat()`
- `_format_elapsed_time()` → `format_elapsed_time()`
- New `WorkflowFailure` dataclass (flat, no inheritance — replaces implement's version)
- New `handle_workflow_failure()` function (generalized from implement's `_handle_workflow_failure`)

**Design decision — flat dataclass, no inheritance:**
The issue proposes `WorkflowFailure` base + `CreatePrFailure` + `ImplementFailure`
subclasses. We simplify to a single flat `WorkflowFailure` with only the shared
fields (`category`, `stage`, `message`, `elapsed_time`). Workflow-specific context
(PR url, task progress, build url) is handled by each workflow's own comment
formatter, which passes the formatted string to the shared handler. This avoids
a class hierarchy for what is essentially just different comment formats.

**Shared handler signature:**
```python
def handle_workflow_failure(
    failure: WorkflowFailure,
    comment_body: str,
    project_dir: Path,
    from_label_id: str,
    update_labels: bool = False,
    issue_number: int | None = None,
) -> None
```

The caller builds the comment (workflow-specific), passes it in. The handler does
three things: log banner, set label (respects `update_labels`), post comment
(always attempted, regardless of `update_labels`).

### 2. `create_pull_request()` return type change

Changes from `bool` to `PullRequestData | None`. Returns the `PullRequestData` dict (which
has `number` and `url` fields) on success, `None` on failure. This enables
cleanup-stage failure comments to include a link to the already-created PR.

### 3. Pre-PR push becomes fatal

The `git_push()` call before PR creation currently logs a warning and continues.
Changed to `return 1` with failure handling (new failure point #3, stage `push`).
A failed push means the PR would be created against stale remote state.

### 4. Safety net pattern in create-pr

`reached_terminal_state` flag + `finally` block added to `run_create_pr_workflow()`,
consistent with implement workflow. No SIGTERM handler (shorter workflow).

### 5. Implement workflow refactored

`implement/core.py` updated to import from `workflow_utils/failure_handling`
instead of defining its own private functions. `FailureCategory` enum stays in
`implement/constants.py` (it's implement-specific). The implement-specific
`_format_failure_comment()` stays in `implement/core.py`.

## Files Created or Modified

| File | Action | Description |
|------|--------|-------------|
| `src/mcp_coder/workflow_utils/failure_handling.py` | **CREATE** | Shared `WorkflowFailure`, `handle_workflow_failure()`, `get_diff_stat()`, `format_elapsed_time()` |
| `src/mcp_coder/workflow_utils/__init__.py` | MODIFY | Export new failure handling symbols |
| `src/mcp_coder/workflows/implement/constants.py` | MODIFY | Remove `WorkflowFailure` (use shared), keep `FailureCategory` |
| `src/mcp_coder/workflows/implement/core.py` | MODIFY | Import shared utilities, remove moved functions, adapt call sites |
| `src/mcp_coder/workflows/create_pr/core.py` | MODIFY | Change `create_pull_request()` return, add failure handling to all paths, safety net |
| `tests/workflow_utils/test_failure_handling.py` | **CREATE** | Tests for shared failure handling module |
| `tests/workflows/create_pr/test_workflow.py` | MODIFY | Update tests for new return type + failure handling |
| `tests/workflows/create_pr/test_failure_handling.py` | **CREATE** | Tests for create-pr specific failure paths |
| `tests/workflows/implement/test_core.py` | MODIFY | Update if any imports changed |

## Failure Points Map (create-pr)

| # | Failure Point | Stage | Has PR info? |
|---|--------------|-------|--------------|
| 1 | `check_prerequisites()` returns False | `prerequisites` | No |
| 2 | `generate_pr_summary()` raises | `summary_generation` | No |
| 3 | `git_push()` fails before PR creation | `push` | No |
| 4 | `create_pull_request()` returns None | `pr_creation` | No |
| 5 | `cleanup_repository()` returns False | `cleanup` | Yes |
| 6 | Commit of cleanup changes fails | `cleanup` | Yes |
| 7 | Push of cleanup changes fails | `cleanup` | Yes |

All failures set label `pr_creating_failed` (single category, unlike implement's three).
