# Step 3 — `fix_ci` workflow module (the Jenkins-side fix loop)

See [summary.md](./summary.md) for full context. Depends on Step 1 (labels).
Independent of Step 2 (no shared code).

## WHERE

- `src/mcp_coder/workflows/fix_ci/__init__.py` (create)
- `src/mcp_coder/workflows/fix_ci/core.py` (create)
- `tests/workflows/fix_ci/__init__.py` (create, empty)
- `tests/workflows/fix_ci/test_core.py` (create)

## WHAT

```python
def run_fix_ci_workflow(
    project_dir: Path,
    provider: str,
    mcp_config: Optional[str] = None,
    settings_file: str | None = None,
    update_issue_labels: bool = False,
    post_issue_comments: bool = False,
) -> int:
    """Run the CI auto-fix loop for status-82:fixing-ci. Returns 0/1."""

def _fail(
    project_dir: Path,
    category_display: str,
    stage: str,
    message: str,
    *,
    update_issue_labels: bool,
    post_issue_comments: bool,
) -> int:
    """Deliberate fix_ci failure: comment (Category/Stage/Error) + status-84 label."""
```

`workflows/fix_ci/__init__.py` re-exports `run_fix_ci_workflow` (mirror
`workflows/fix_conflict/__init__.py`).

## HOW

Imports in `core.py`:
```python
from mcp_coder.llm.interface import LLMTimeoutError
from mcp_coder.llm.providers.claude.claude_code_cli import McpServersUnavailableError
from mcp_coder.mcp_workspace_git import get_current_branch_name
from mcp_coder.mcp_workspace_github import IssueManager
from mcp_coder.workflow_steps.ci import check_and_fix_ci
from mcp_coder.workflow_utils.failure_handling import (
    WorkflowFailure, handle_workflow_failure, llm_failure_reason, run_guarded,
)
from mcp_coder.workflow_utils.label_transitions import update_workflow_label
```
No `GuardOutcome`/custom `build_comment` import — `run_guarded`'s default
comment formatting is used as-is (no per-run "progress" state to render).

## ALGORITHM (`run_fix_ci_workflow`'s inner `body()`, passed to `run_guarded`)

```
branch = get_current_branch_name(project_dir)
if branch is None: return 1                     # nothing to check, no label churn
try:
    ci_ok = check_and_fix_ci(project_dir, branch, provider, mcp_config, settings_file)
except (LLMTimeoutError, McpServersUnavailableError) as exc:
    reason = llm_failure_reason(exc) or "general"
    category = {"timeout": "Llm Timeout", "mcp_unavailable": "Mcp Unavailable"}.get(reason, "General")
    return _fail(project_dir, category, "CI pipeline analysis", str(exc), ...)
if ci_ok:
    if update_issue_labels:
        update_workflow_label(IssueManager(project_dir), "fixing_ci", "pr_created")
    return 0
return _fail(project_dir, "Ci Fix Exhausted", "CI pipeline fix",
             "CI check failed after maximum fix attempts", ...)
```
`run_fix_ci_workflow` itself is just:
```python
def run_fix_ci_workflow(project_dir, provider, mcp_config=None, settings_file=None,
                         update_issue_labels=False, post_issue_comments=False) -> int:
    def body() -> int:
        ...  # algorithm above
    return run_guarded(
        body,
        project_dir=project_dir,
        from_label_id="fixing_ci",
        general_category="ci_fix_failed",
        comment_header="## ❌ CI Fix Crashed",
        update_issue_labels=update_issue_labels,
        post_issue_comments=post_issue_comments,
    )
```

`_fail()` body:
```
comment = (
    "## ❌ CI Fix Failed\n"
    f"**Category:** {category_display}\n"
    f"**Stage:** {stage}\n"
    f"**Error:** {message}"
)
handle_workflow_failure(
    WorkflowFailure(category="pr_ci_failed", stage=stage, message=message),
    comment, project_dir, from_label_id="fixing_ci",
    update_issue_labels=update_issue_labels, post_issue_comments=post_issue_comments,
)
return 1
```

## DATA

`run_fix_ci_workflow` returns `int` (`0` success, `1` any handled or netted
failure — mirrors every other `*/core.py` workflow's contract). No other
return values; all state changes are the label transition + optional
GitHub comment, both side effects of `handle_workflow_failure`/
`update_workflow_label`.

## Test-first steps

Write `tests/workflows/fix_ci/test_core.py` first (patch target prefix
`mcp_coder.workflows.fix_ci.core`), covering:

1. `test_ci_passes_transitions_to_pr_created` — `check_and_fix_ci` returns
   `True`, `update_issue_labels=True`; assert result `0` and
   `update_workflow_label` called with `("fixing_ci", "pr_created")`.
2. `test_ci_passes_no_label_update_when_disabled` — same but
   `update_issue_labels=False`; assert `update_workflow_label` not called.
3. `test_ci_exhausted_posts_comment_and_sets_label` — `check_and_fix_ci`
   returns `False`; patch `handle_workflow_failure`; assert result `1` and
   the call's `WorkflowFailure.category == "pr_ci_failed"` and the comment
   body contains `"Ci Fix Exhausted"`.
4. `test_llm_timeout_posts_comment_and_sets_label` — `check_and_fix_ci`
   raises `LLMTimeoutError`; assert comment contains `"Llm Timeout"` and
   category is still `"pr_ci_failed"`.
5. `test_mcp_unavailable_posts_comment_and_sets_label` — raises
   `McpServersUnavailableError`; assert comment contains `"Mcp Unavailable"`.
6. `test_no_current_branch_returns_one` — `get_current_branch_name` returns
   `None`; assert result `1`, `check_and_fix_ci` not called.
7. `test_unexpected_exception_netted_by_run_guarded` (mirrors
   `tests/workflows/create_plan/test_guard_net.py`) — `check_and_fix_ci`
   raises a plain `RuntimeError`; patch
   `mcp_coder.workflow_utils.failure_handling.handle_workflow_failure`;
   assert result `1` and the netted `WorkflowFailure.category ==
   "ci_fix_failed"` (the *general* crash category, distinct from the
   deliberate `pr_ci_failed` above).

Run — confirm all fail (module doesn't exist). Implement `core.py` and
`__init__.py`. Re-run — confirm green.

## Checks

`run_pytest_check`, `run_pylint_check`, `run_mypy_check` — all pass. Then
`run_format_code`, then commit.

## Commit

One commit: `feat(fix-ci): add the Jenkins-side CI auto-fix workflow`.

## LLM Prompt

> Implement Step 3 of the plan in `pr_info/steps/summary.md`. Read that
> summary first, then follow `pr_info/steps/step_3.md` exactly: write
> `tests/workflows/fix_ci/test_core.py` first (red), then create
> `src/mcp_coder/workflows/fix_ci/core.py` and `__init__.py` implementing
> `run_fix_ci_workflow` and `_fail` exactly as specified (green). Run
> pytest/pylint/mypy, format, and produce exactly one commit.
