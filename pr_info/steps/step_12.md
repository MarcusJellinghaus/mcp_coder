# Step 12 — `workflows/rebase.py` guards and helpers onto upstream primitives

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_12.md`. Implement step 12 only,
> tests first. Run pylint, pytest (fast unit set, `-n auto`, plus `-m git_integration` for
> `tests/workflows/rebase/test_git_helpers.py`) and mypy until all pass, run the formatter,
> and make one commit: `refactor(rebase): guards and restore helpers via mcp_workspace_git`.

## Scope

Everything in `workflows/rebase.py` **except** the rebase/conflict loop and the fix-loop
`add -A` / `commit -m`: those stay on `_run_git` until step 13.

## WHERE

- `src/mcp_coder/mcp_workspace_git.py` — export `rebase_abort`, `reset_hard`, `is_rebase_in_progress` (`.rebase`); `list_tree` (`.conflicts`); `get_remote_url` (`.remotes`). `get_working_tree_status` is already exported (step 9).
- `src/mcp_coder/workflows/rebase.py`
- `tests/workflows/rebase/test_workflow.py`, `test_guards.py`, `test_git_helpers.py`

## WHAT — removals

`_is_rebase_in_progress` (`.git/rebase-*` probe), the `.git/MERGE_HEAD` check, the
`is_working_directory_clean` import. `_run_git` / `_GitResult` stay (step 13 removes them).

## WHAT — helpers (names kept where they exist)

```python
def _is_clean(project_dir: Path) -> bool:
    """Fail-closed clean check: a git failure is never clean."""
    status = get_working_tree_status(project_dir)
    return status["success"] and status["clean"]

def _rebase_in_progress_or_none(project_dir: Path) -> bool | None:
    """Best-effort for except/finally sites: None (logged) if it cannot be determined."""
    try:
        return is_rebase_in_progress(project_dir)
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.error("Could not determine rebase state: %s", exc)
        return None

def _abort_rebase(project_dir: Path) -> None:
    result = rebase_abort(project_dir)
    if not result["success"]:
        logger.error("git rebase --abort failed: %s", result["stderr"] or result["error"])

def _reset_hard(project_dir: Path, sha: str) -> str:
    """Restore pre-rebase state; return the phrase for the user-visible abort message."""
    result = reset_hard(project_dir, sha)
    if result["success"]:
        return "pre-rebase state restored"
    logger.error("git reset --hard %s failed: %s", sha, result["stderr"] or result["error"])
    return f"restoring pre-rebase state FAILED ({result['error']})"
```

## WHAT — call-site changes

- `_rebase_success_shape`: `is_rebase_in_progress(...)` wrapped in `try`; a raise is logged
  at error level and returns `False` (not propagated to the outer `except`, whose reset is
  skipped when rebase state is unknown), so the existing call site runs `_reset_hard`. Then
  `_is_clean`, then sha compare.
- `_preflight`: `if not _is_clean(...)` → `"Working tree not clean"`; `if is_rebase_in_progress(...)` → `"Repository is mid-rebase/merge"` (message kept); `if get_remote_url(project_dir) is None` → `"Remote 'origin' not found"`.
- `_check_pr_info_absent_on_base`:
  ```python
  listing = list_tree(project_dir, f"origin/{base_branch}", "pr_info")
  if not listing["success"]:
      return f"Could not list pr_info/ on origin/{base_branch}: {listing['error']}"
  return f"pr_info/ present on origin/{base_branch}" if listing["entries"] else None
  ```
- Every "pre-rebase state restored" message uses the phrase returned by `_reset_hard`
  (call `_reset_hard` before logging the message).
- `except Exception`: `if _rebase_in_progress_or_none(...) is False: phrase = _reset_hard(...)`; include the phrase in `"Aborted: ..."` when a reset ran.
- `finally`: `if _rebase_in_progress_or_none(project_dir): _abort_rebase(project_dir)` (None/False → skip).
- Conflict loop (interim, until step 13): the `if not _is_rebase_in_progress(...)` check becomes
  `if not is_rebase_in_progress(...)` (a raise goes to the outer `except`).

## Tests (write first)

`test_workflow.py` / `test_guards.py` — patch the new shim names in `mcp_coder.workflows.rebase`
(`is_rebase_in_progress`, `reset_hard`, `rebase_abort`, `list_tree`, `get_remote_url`,
`get_working_tree_status`); replace the `_is_rebase_in_progress` and
`is_working_directory_clean` monkeypatches; drop the `_run_git` queue entries for
`remote get-url`, `ls-tree`, `reset --hard` and `rebase --abort` (the loop entries stay). Cover:

- preflight: status `success=False` → `"Working tree not clean"`; rebase in progress; `get_remote_url` `None`.
- `list_tree` `success=False` → preflight error (exit 2); entries present → refused; empty → passes.
- `reset_hard` failure → message contains "FAILED"; logged at error level.
- `except Exception` with `is_rebase_in_progress` raising → exit code still 1, no reset, no abort.
- `finally` aborts only when `is_rebase_in_progress` is `True`.
- `_rebase_success_shape` false when status `success=False`.
- completed rebase, then `is_rebase_in_progress` raises inside `_rebase_success_shape` →
  returns `False`, `_reset_hard` called with `pre_sha`, exit code 1.

`test_git_helpers.py` (real git) — delete `TestIsRebaseInProgress`; adapt `TestAbortRebase` /
`TestResetHard` to the new contract (`_reset_hard` returns the phrase); keep
`TestRebaseSuccessShape`. `_start_conflicted_rebase` keeps its `_run_git` setup for now.

## DATA

- `_reset_hard` → `str` phrase. Exit codes `0 / 1 / 2` unchanged.
