# Step 2 — Dirty-working-tree guard in `_attempt_rebase_and_push`

Read [summary.md](./summary.md) first. Independent of step 1 — may land in either order.

Shared hardening: a backstop for *any* stray uncommitted write, not just the round-log path
fixed by step 1 (including the unrelated-dirt case step 1 deliberately refuses to commit).
Turns git's generic `error: cannot rebase: You have unstaged changes` into a warning that names
the cause at the workflow layer.

## WHERE

- Source: `src/mcp_coder/workflow_steps/rebase.py` — `_attempt_rebase_and_push`, line 33.
- Test: `tests/workflow_steps/test_rebase.py` — a new class, e.g.
  `class TestDirtyWorkingTreeGuard`, placed before `class TestRebaseIntegration`.

## WHAT

No signature change:

```python
def _attempt_rebase_and_push(project_dir: Path) -> bool:
```

Two new imports in `rebase.py`, one extending the existing `mcp_workspace_git` shim import:

```python
from mcp_coder.constants import DEFAULT_IGNORED_BUILD_ARTIFACTS
from mcp_coder.mcp_workspace_git import (
    get_full_status,
    is_working_directory_clean,
    rebase_onto_branch,
)
```

One module-private helper plus four new tests:

```python
def _has_uncommitted_tracked_changes(project_dir: Path) -> bool: ...

def test_dirty_tree_skips_rebase(...) -> None:
def test_untracked_only_proceeds_to_rebase(...) -> None:
def test_clean_tree_proceeds_to_rebase(...) -> None:
def test_non_git_repo_proceeds_to_rebase(...) -> None:
```

## HOW

- Import through the local shim `mcp_coder.mcp_workspace_git`, never `mcp_workspace` directly —
  the module already does this for `rebase_onto_branch`.
- Place the guard at the **top of the function**, above `_get_rebase_target_branch`:
  `detect_base_branch` performs a remote fetch, and there is no point paying for it when the
  rebase cannot start.

### `ignore_files` — match the other control-flow call sites

Pass `ignore_files=DEFAULT_IGNORED_BUILD_ARTIFACTS`. Every other call site that uses this
function to *decide control flow* already does — `workflow_steps/prerequisites.py:34`
(`check_git_clean`, which gates this very workflow), `workflows/create_plan/core.py:492`,
`workflows/create_pr/core.py:566`, `cli/commands/set_status.py:264`. Omitting it would let this
guard block on a file (`uv.lock`) that the prerequisite check immediately upstream deliberately
tolerates.

### Untracked files — explicitly *not* a reason to skip

`is_working_directory_clean` counts untracked files as dirty
(`mcp_workspace/git_operations/repository_status.py:44` sums staged + modified + untracked), but
`git rebase` starts happily with untracked files present. Using its verdict directly would make
the guard skip a rebase that would have succeeded, converting a green run into a needs-human
handoff in the `review` lane — a regression, not hardening.

So the cheap `is_working_directory_clean` call stays as the fast path, and when it reports dirty
the decision is refined by `_has_uncommitted_tracked_changes`, which re-reads
`get_full_status(project_dir)` and skips only on **staged or modified** entries (after filtering
`DEFAULT_IGNORED_BUILD_ARTIFACTS`) — exactly the two categories git refuses on ("You have
unstaged changes" / "Your index contains uncommitted changes"). Deletions of tracked files
appear under `modified`, so they are covered. The second git read only happens on the rare
dirty path.

### Non-git-repo path

`is_working_directory_clean` **raises `ValueError`** when `project_dir` is not a git repository.
Catch it and treat the tree as clean, letting `rebase_onto_branch` report the non-repo case as
it does today. This preserves the function's documented "never fails workflow" contract **and**
keeps the eight existing tests in `test_rebase.py` passing untouched — the five in
`TestRebaseIntegration` run against `Path("/test")`, which is not a repository.

### Callers

Additive only: both callers (`workflows/implement/core.py:104`, `workflows/review/steps.py:105`)
already handle a `False` return exactly as they do today. Do not touch either caller.

Update the function docstring's `Returns:` to mention the dirty-tree case alongside the existing
"rebase skipped, failed, or no target detected", and say that untracked files alone do not count.

## ALGORITHM

```
try:
    clean = is_working_directory_clean(
        project_dir, ignore_files=DEFAULT_IGNORED_BUILD_ARTIFACTS
    )
except ValueError:
    clean = True            # not a git repo - let rebase_onto_branch report that
if not clean and _has_uncommitted_tracked_changes(project_dir):
    warn("Working tree has uncommitted changes - skipping rebase "
         "(likely a leftover uncommitted write)")
    return False
target = _get_rebase_target_branch(project_dir)   # unchanged from here down
```

```
_has_uncommitted_tracked_changes(project_dir):
    status = get_full_status(project_dir)         # {} for a non-repo
    ignored = set(DEFAULT_IGNORED_BUILD_ARTIFACTS)
    blocking = [f for f in status.get("staged", []) + status.get("modified", [])
                if f not in ignored]
    return bool(blocking)     # untracked files are NOT blocking: git rebase tolerates them
```

The warning is generic about the **cause**; it must not enumerate the dirty files. File-level
detail belongs to `mcp-workspace#295`'s hardening of `rebase_onto_branch`, so the two layers do
not duplicate the same logic. Use a plain hyphen, not an em dash, matching the existing log
strings in this module.

## DATA

- Returns `bool`, unchanged: `True` only on rebase-succeeded-and-pushed; `False` on
  staged/modified-dirty tree, no target, rebase failed, or push failed.
- No exception ever escapes.
- An untracked-only tree, and a tree dirty only in `DEFAULT_IGNORED_BUILD_ARTIFACTS`, both reach
  the rebase exactly as today.

## TDD

1. Write the four tests as direct unit calls to `_attempt_rebase_and_push` — lighter than the
   existing integration-style tests that drive `run_implement_workflow`.

   - `test_dirty_tree_skips_rebase`: patch `...is_working_directory_clean` → `False` and
     `...get_full_status` → `{"staged": [], "modified": ["src/foo.py"], "untracked": []}`.
     Assert the return is `False`, `rebase_onto_branch.assert_not_called()`,
     `push_changes.assert_not_called()`, and that a `logging.WARNING` record was emitted
     (`caplog`).
   - `test_untracked_only_proceeds_to_rebase`: `is_working_directory_clean` → `False` but
     `get_full_status` → `{"staged": [], "modified": [], "untracked": ["notes.txt"]}`. Assert
     `rebase_onto_branch` **was** called and the return is `True`. This is the regression guard:
     a tree git would have rebased must still be rebased.
   - `test_clean_tree_proceeds_to_rebase`: `is_working_directory_clean` → `True`, target
     `"main"`, rebase `True`, push `True`. Assert the return is `True` and `rebase_onto_branch`
     was called with `(project_dir, "main")`.
   - `test_non_git_repo_proceeds_to_rebase`: **do not patch `is_working_directory_clean`.** Pass
     pytest's `tmp_path` (a real directory that is not a git repository) so the real function
     raises `ValueError` and the swallow is genuinely exercised — this is what the "never fails
     workflow" contract rests on, and what keeps the eight existing tests green. Patch only
     `..._get_rebase_target_branch` → `"main"`, `...rebase_onto_branch` → `True` and
     `...push_changes` → `True`; assert the return is `True` and no exception escaped.

   Confirm `test_dirty_tree_skips_rebase` and `test_untracked_only_proceeds_to_rebase` fail
   before the source change.
2. Add the guard, the helper, the imports and the docstring line.
3. `tests/workflow_steps/test_rebase.py` currently holds **8** tests (3 in
   `TestGetRebaseTargetBranch`, 5 in `TestRebaseIntegration`), so confirm all **12** pass — the
   8 existing ones **must not need editing**. If any of them requires a change, stop and
   report: that means the `ValueError` swallow is not behaving as designed.

## Verification

```
mcp__mcp-tools-py__run_format_code
mcp__mcp-tools-py__run_pylint_check
mcp__mcp-tools-py__run_pytest_check(extra_args=["-n", "auto", "tests/workflow_steps/", "tests/workflows/review/", "tests/workflows/implement/"])
mcp__mcp-tools-py__run_mypy_check
mcp__mcp-tools-py__run_lint_imports_check
```

`run_lint_imports_check` matters here: the new imports must go through the
`mcp_coder.mcp_workspace_git` shim, and `workflow_steps/` sits in the middle tier of the
three-tier workflow architecture.

Then the full unit suite, then **one commit** for this step.

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_2.md`.
>
> Implement step 2 only, test-first. In `src/mcp_coder/workflow_steps/rebase.py`, add a guard
> clause at the top of `_attempt_rebase_and_push`: call
> `is_working_directory_clean(project_dir, ignore_files=DEFAULT_IGNORED_BUILD_ARTIFACTS)`
> (imported from the `mcp_coder.mcp_workspace_git` shim and `mcp_coder.constants`), and when it
> reports dirty refine the decision with a small `_has_uncommitted_tracked_changes` helper over
> `get_full_status`: skip the rebase only for staged or modified entries, never for
> untracked-only dirt, because `git rebase` tolerates untracked files and the guard must not
> skip a rebase that would have succeeded. On a genuine skip, log a warning naming the cause —
> not the individual files — and return `False`. `is_working_directory_clean` raises `ValueError`
> on a non-git-repo path: catch it and treat the tree as clean so the function keeps its
> "never fails workflow" contract.
>
> Add four direct unit tests to `tests/workflow_steps/test_rebase.py` (dirty tree skips and
> warns; untracked-only still rebases; clean tree rebases; and a non-git-repo path that does
> **not** patch `is_working_directory_clean`, so the `ValueError` swallow is really exercised),
> written before the source change. That file already has 8 tests, so it must end with 12
> passing and none of the existing 8 edited — if one needs editing, stop and report. Do not
> touch either caller (`workflows/implement/core.py`, `workflows/review/steps.py`). Run
> `run_format_code`, then pylint / pytest (`-n auto`) / mypy / lint-imports, and produce a
> single commit.
