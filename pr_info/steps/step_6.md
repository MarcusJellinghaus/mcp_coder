# Step 6 — Retrofit `fix_conflict/core.py` with `run_guarded()`

See [summary.md](./summary.md) for full context. Independent of Steps 2–5;
only depends on Step 1 (the `merge_conflict_failed` label already exists —
it does, from #1212).

## WHERE

- `src/mcp_coder/workflows/fix_conflict/core.py` (modify)
- `tests/workflows/fix_conflict/test_core.py` (modify)

## WHAT

No signature change to `run_fix_conflict_workflow(project_dir: Path) -> int`.
Internally, its current body becomes the `body()` closure passed to
`run_guarded`.

## HOW

Add the import:
```python
from mcp_coder.workflow_utils.failure_handling import run_guarded
```
Wrap the existing `try/except` body (everything currently inside
`run_fix_conflict_workflow`) in a nested `def body() -> int:` function with
the exact same contents, **except** the outer `except Exception as exc:
logger.error(...); return 1` is removed — that's now `run_guarded`'s job.
`run_fix_conflict_workflow` becomes:
```python
def run_fix_conflict_workflow(project_dir: Path) -> int:
    def body() -> int:
        branch = get_current_branch_name(project_dir)
        if branch is None:
            logger.error("Could not determine current branch")
            return 1
        rebased = _attempt_rebase_and_push(project_dir)
        logger.info("Rebase attempt result: %s", rebased)
        state = _poll_mergeable_state(project_dir, branch)
        if state == "dirty":
            update_workflow_label(IssueManager(project_dir), "fixing_merge_conflict", "pr_merge_conflict")
        elif state not in (None, "unknown"):
            update_workflow_label(IssueManager(project_dir), "fixing_merge_conflict", "pr_created")
        else:
            logger.info("mergeable_state still unknown after poll cap - leaving at status-72 for next coordinator poll")
        return 0

    return run_guarded(
        body,
        project_dir=project_dir,
        from_label_id="fixing_merge_conflict",
        general_category="merge_conflict_failed",
        comment_header="## ❌ Fix Conflict Crashed",
        update_issue_labels=True,
        post_issue_comments=True,
    )
```
`update_issue_labels=True`/`post_issue_comments=True` are hardcoded (not
parameters) because `run_fix_conflict_workflow` takes only `project_dir` —
this Jenkins-dispatched workflow always wants both, same as its handled
outcomes already unconditionally call `update_workflow_label`.

## ALGORITHM

No change to the rebase/poll/label-transition logic itself — see the
existing `_poll_mergeable_state` and the three branches above, copied
verbatim into `body()`.

## DATA

Return value unchanged: `0` on any handled outcome, `1` on a netted crash
(now via `run_guarded`, previously via the bare `except`).

## Test-first steps

In `tests/workflows/fix_conflict/test_core.py`:
1. Update `test_unexpected_exception_is_caught_and_returns_1`: additionally
   patch `mcp_coder.workflow_utils.failure_handling.handle_workflow_failure`
   and assert it was called once with a `WorkflowFailure.category ==
   "merge_conflict_failed"` (mirrors
   `tests/workflows/create_plan/test_guard_net.py`'s
   `test_unexpected_exception_netted_to_planning_failed`).
2. Add `test_system_exit_is_netted_and_reraised` — patch
   `get_current_branch_name` with `side_effect=SystemExit(1)`; assert
   `pytest.raises(SystemExit)` around the call, and that
   `handle_workflow_failure` was called once with category
   `"merge_conflict_failed"`.
3. Confirm the four already-passing outcome tests
   (`test_dirty_on_first_poll_...`, `test_clean_transitions_...`,
   `test_unknown_for_all_attempts_...`, `test_no_open_pr_found_...`,
   `test_no_current_branch_returns_1_without_rebase`) still pass unchanged
   — they exercise `body()`'s clean-return paths, which `run_guarded` passes
   through untouched.

Run — confirm the two new/changed tests fail first (red, since
`handle_workflow_failure` isn't invoked yet on a crash). Apply the `core.py`
change above. Re-run the whole file — confirm green.

## Checks

`run_pytest_check`, `run_pylint_check`, `run_mypy_check` — all pass. Then
`run_format_code`, then commit.

## Commit

One commit: `fix(fix-conflict): net crashes with run_guarded and post a comment`.

## LLM Prompt

> Implement Step 6 of the plan in `pr_info/steps/summary.md`. Read that
> summary first, then follow `pr_info/steps/step_6.md` exactly: update
> `tests/workflows/fix_conflict/test_core.py` first (red: the crash case
> should now expect a `handle_workflow_failure` call), then wrap
> `run_fix_conflict_workflow`'s body in `run_guarded()` in
> `src/mcp_coder/workflows/fix_conflict/core.py` exactly as specified
> (green), without changing its handled-outcome behavior. Run
> pytest/pylint/mypy, format, and produce exactly one commit.
