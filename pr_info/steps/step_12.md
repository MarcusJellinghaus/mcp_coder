# Step 12 — `workflows/rebase.py` onto upstream rebase primitives

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_12.md`. Implement step 12 only,
> tests first. Run pylint, pytest (fast unit set, `-n auto`, plus `-m git_integration` for
> `tests/workflows/rebase/test_git_helpers.py`) and mypy until all pass, run the formatter,
> and make one commit: `refactor(rebase): drive rebase via mcp_workspace_git primitives`.

## Precondition

The new test `TestStageAllInRebase` (below) confirms `stage_all_changes` stages LLM-resolved
unmerged files so `rebase_continue` completes. If it cannot pass with upstream
`stage_all_changes`, write one line to `pr_info/.blocked.txt` and stop.

## WHERE

- `src/mcp_coder/mcp_workspace_git.py` — export `RebaseResult` (`.core`), `rebase_start`, `rebase_continue`, `rebase_skip`, `rebase_abort`, `reset_hard`, `is_rebase_in_progress` (`.rebase`); `get_conflict_blob_info`, `read_conflict_stage`, `resolve_take_theirs_or_remove`, `list_tree` (`.conflicts`); `has_staged_changes`, `get_working_tree_status` (`.repository_status`, latter already exported in step 9); `get_remote_url` (`.remotes`)
- `src/mcp_coder/workflows/rebase.py`
- `tests/workflows/rebase/test_workflow.py`, `test_guards.py`, `test_git_helpers.py`, `test_llm_steps.py`

## WHAT — removals

`_GitResult`, `_run_git`, `_is_rebase_in_progress` (`.git/rebase-*` probe), `_conflicted_files`,
`_binary_conflict`, `_resolve_pr_info_conflict` (inlined), the `.git/MERGE_HEAD` check, the
`is_working_directory_clean` and `execute_command` imports.

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

def _show_stage(project_dir: Path, stage: int, file: str) -> str | None:
    result = read_conflict_stage(project_dir, stage, file)
    return result["content"] if result["success"] else None

def _stage_all_and_continue(project_dir: Path) -> RebaseResult:
    stage_all_changes(project_dir)       # errors surface via the continue / re-check
    return rebase_continue(project_dir)  # upstream sets GIT_EDITOR=true
```

`RebaseResult` is the one result type this step exports from the shim (`.core`), because
`_stage_all_and_continue` and the loop variable need an annotation under `mypy --strict`.

## WHAT — call-site changes

- `_rebase_success_shape`: `is_rebase_in_progress(...)` (raises → outer `except`), then `_is_clean`, then sha compare.
- `_preflight`: `if not _is_clean(...)` → `"Working tree not clean"`; `if is_rebase_in_progress(...)` → `"Repository is mid-rebase/merge"` (message kept); `if get_remote_url(project_dir) is None` → `"Remote 'origin' not found"`.
- `_check_pr_info_absent_on_base`:
  ```python
  listing = list_tree(project_dir, f"origin/{base_branch}", "pr_info")
  if not listing["success"]:
      return f"Could not list pr_info/ on origin/{base_branch}: {listing['error']}"
  return f"pr_info/ present on origin/{base_branch}" if listing["entries"] else None
  ```
- Fix loop: `commit_all_changes(f"fix: resolve regressions from rebase onto origin/{base}", project_dir)` replaces `add -A` + `commit -m` (result ignored as today; "no changes" is `success=True, commit_hash=None`).
- Every "pre-rebase state restored" message uses the phrase returned by `_reset_hard`.
- `except Exception`: `if _rebase_in_progress_or_none(...) is False: phrase = _reset_hard(...)`; include the phrase in `"Aborted: ..."` when a reset ran.
- `finally`: `if _rebase_in_progress_or_none(project_dir): _abort_rebase(project_dir)` (None/False → skip).

## ALGORITHM — conflict loop

```
result = rebase_start(dir, f"origin/{base}")
while result["status"] != "completed":
    if result["status"] == "error": log "Aborted: git rebase failed unexpectedly: <stderr or error>"; return 1
    info = get_conflict_blob_info(dir); if not info["success"]: log "Aborted: could not read conflicts: <error>"; return 1
    files = [e["path"] for e in info["entries"]]
    if not files: if not has_staged_changes(dir): result = rebase_skip(dir); continue  else abort "stopped without conflicted files"
    binary = first e["path"] with e["is_binary"] -> abort; then repeat-count, pr_info via resolve_take_theirs_or_remove(...)["success"], LLM, markers (unchanged)
    result = _stage_all_and_continue(dir)
```

`list_unmerged_paths` is not needed: `get_conflict_blob_info` gives paths (sorted) and
binary-ness in one call and fails closed with `success=False`.

## Tests (write first)

`test_workflow.py` / `test_guards.py` — replace the argv-keyed `_run_git` mock with patches of
the shim names in `mcp_coder.workflows.rebase` (`rebase_start`, `rebase_continue`,
`rebase_skip`, `get_conflict_blob_info`, `has_staged_changes`, `is_rebase_in_progress`,
`reset_hard`, `rebase_abort`, `list_tree`, `get_remote_url`, `get_working_tree_status`,
`stage_all_changes`, `commit_all_changes`, `resolve_take_theirs_or_remove`, `read_conflict_stage`). Cover:

- preflight: status `success=False` → `"Working tree not clean"`; rebase in progress; `get_remote_url` `None`.
- `list_tree` `success=False` → preflight error (exit 2); entries present → refused; empty → passes.
- loop: `stopped_on_conflict` → continue → `completed`; `error` status → exit 1; empty stop + no staged → `rebase_skip`; empty stop + staged → exit 1; binary entry → exit 1; blob-info failure → exit 1; `pr_info/` file resolved via `resolve_take_theirs_or_remove`.
- `reset_hard` failure → message contains "FAILED"; logged at error level.
- `except Exception` with `is_rebase_in_progress` raising → exit code still 1, no reset, no abort.
- `finally` aborts only when `is_rebase_in_progress` is `True`.
- `_rebase_success_shape` false when status `success=False`.

`test_git_helpers.py` (real git) — delete `TestRunGit`, `TestIsRebaseInProgress`,
`TestConflictedFiles`, `TestShowStage` (or reduce to one `_show_stage` absent-side case),
`TestResolvePrInfoConflict`, `TestBinaryConflict`; adapt `TestAbortRebase` / `TestResetHard`
to the new return contract; keep `TestRebaseSuccessShape`, `TestHasConflictMarkers` and the
`_start_conflicted_rebase` fixture (replace its `_run_git` setup calls with shim calls). Add:

- `TestStageAllInRebase`: at a conflict stop, write resolved content, `stage_all_changes` → `True`, `get_conflict_blob_info` has no entries, `rebase_continue` → `completed`.
- `commit_all_changes` on a clean tree → `success=True, commit_hash=None`.

`test_llm_steps.py` — update any patch of `_run_git` / `_show_stage` internals.

## DATA

- `RebaseResult["status"]`: `completed | stopped_on_conflict | error`.
- Exit codes `0 / 1 / 2` unchanged.
