# Step 13 — `workflows/rebase.py` rebase/conflict loop onto upstream primitives

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_13.md`. Implement step 13 only,
> tests first. Run pylint, pytest (fast unit set, `-n auto`, plus `-m git_integration` for
> `tests/workflows/rebase/test_git_helpers.py`) and mypy until all pass, run the formatter,
> and make one commit: `refactor(rebase): drive rebase loop via mcp_workspace_git primitives`.

## Precondition

Step 12 is committed. The new test `TestStageAllInRebase` (below) confirms
`stage_all_changes` stages LLM-resolved unmerged files so `rebase_continue` completes. If it
cannot pass with upstream `stage_all_changes`, write one line to `pr_info/.blocked.txt` and stop.

## WHERE

- `src/mcp_coder/mcp_workspace_git.py` — export `RebaseResult` (`.core`), `rebase_start`, `rebase_continue`, `rebase_skip` (`.rebase`); `get_conflict_blob_info`, `read_conflict_stage`, `resolve_take_theirs_or_remove` (`.conflicts`); `has_staged_changes` (`.repository_status`)
- `src/mcp_coder/workflows/rebase.py`
- `tests/workflows/rebase/test_workflow.py`, `test_git_helpers.py`, `test_llm_steps.py`

## WHAT — removals

`_GitResult`, `_run_git`, `_conflicted_files`, `_binary_conflict`, `_resolve_pr_info_conflict`
(inlined), the `execute_command` import.

## WHAT — helpers (names kept)

```python
def _show_stage(project_dir: Path, stage: int, file: str) -> str | None:
    result = read_conflict_stage(project_dir, stage, file)
    return result["content"] if result["success"] else None

def _stage_all_and_continue(project_dir: Path) -> RebaseResult:
    stage_all_changes(project_dir)       # errors surface via the continue / re-check
    return rebase_continue(project_dir)  # upstream sets GIT_EDITOR=true
```

`RebaseResult` is the one result type exported from the shim (`.core`), because
`_stage_all_and_continue` and the loop variable need an annotation under `mypy --strict`.

## WHAT — fix loop

`commit_all_changes(f"fix: resolve regressions from rebase onto origin/{base}", project_dir)`
replaces `add -A` + `commit -m` (result ignored as today; "no changes" is `success=True, commit_hash=None`).

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

The loop reads `result["status"]` instead of the interim `is_rebase_in_progress` check from
step 12. `list_unmerged_paths` is not needed: `get_conflict_blob_info` gives paths (sorted)
and binary-ness in one call and fails closed with `success=False`.

## Tests (write first)

`test_workflow.py` — replace the remaining argv-keyed `_run_git` mock with patches of the shim
names in `mcp_coder.workflows.rebase` (`rebase_start`, `rebase_continue`, `rebase_skip`,
`get_conflict_blob_info`, `has_staged_changes`, `stage_all_changes`, `commit_all_changes`,
`resolve_take_theirs_or_remove`, `read_conflict_stage`). Cover:

- `stopped_on_conflict` → continue → `completed`; `error` status → exit 1; empty stop + no staged → `rebase_skip`; empty stop + staged → exit 1; binary entry → exit 1; blob-info failure → exit 1; `pr_info/` file resolved via `resolve_take_theirs_or_remove`.
- fix loop calls `commit_all_changes` with the regression message.

`test_git_helpers.py` (real git) — delete `TestRunGit`, `TestConflictedFiles`, `TestShowStage`
(or reduce to one `_show_stage` absent-side case), `TestResolvePrInfoConflict`,
`TestBinaryConflict`; keep `TestHasConflictMarkers` and the `_start_conflicted_rebase` fixture
(replace its `_run_git` setup calls with shim calls). Add:

- `TestStageAllInRebase`: at a conflict stop, write resolved content, `stage_all_changes` → `True`, `get_conflict_blob_info` has no entries, `rebase_continue` → `completed`.
- `commit_all_changes` on a clean tree → `success=True, commit_hash=None`.

`test_llm_steps.py` — update any patch of `_run_git` / `_show_stage` internals.

## DATA

- `RebaseResult["status"]`: `completed | stopped_on_conflict | error`.
- Exit codes `0 / 1 / 2` unchanged.
