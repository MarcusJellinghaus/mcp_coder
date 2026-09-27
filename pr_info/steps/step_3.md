# Step 3 — Dirty-working-tree guard in `_attempt_rebase_and_push`

Read [summary.md](./summary.md) first. Independent of steps 1 and 2 — may land in any order.

Shared hardening: a backstop for *any* stray uncommitted write, not just the round-log path
fixed by step 2. Turns git's generic `error: cannot rebase: You have unstaged changes` into a
warning that names the cause at the workflow layer.

## WHERE

- Source: `src/mcp_coder/workflow_steps/rebase.py` — `_attempt_rebase_and_push`, line 33.
- Test: `tests/workflow_steps/test_rebase.py` — a new class, e.g.
  `class TestDirtyWorkingTreeGuard`, placed before `class TestRebaseIntegration`.

## WHAT

No signature change:

```python
def _attempt_rebase_and_push(project_dir: Path) -> bool:
```

New import in `rebase.py`, extending the existing `mcp_workspace_git` shim import:

```python
from mcp_coder.mcp_workspace_git import is_working_directory_clean, rebase_onto_branch
```

Two new tests:

```python
def test_dirty_tree_skips_rebase(...) -> None:
def test_clean_tree_proceeds_to_rebase(...) -> None:
```

## HOW

- Import through the local shim `mcp_coder.mcp_workspace_git`, never `mcp_workspace` directly —
  the module already does this for `rebase_onto_branch`.
- Place the guard at the **top of the function**, above `_get_rebase_target_branch`:
  `detect_base_branch` performs a remote fetch, and there is no point paying for it when the
  rebase cannot start.
- `is_working_directory_clean` **raises `ValueError`** when `project_dir` is not a git
  repository. Catch it and treat the tree as clean, letting `rebase_onto_branch` report the
  non-repo case as it does today. This preserves the function's documented "never fails
  workflow" contract **and** keeps the five existing tests in `test_rebase.py` passing
  untouched — they run against `Path("/test")`, which is not a repository.
- Additive only: both callers (`workflows/implement/core.py:104`,
  `workflows/review/steps.py:105`) already handle a `False` return exactly as they do today.
  Do not touch either caller.
- Update the function docstring's `Returns:` to mention the dirty-tree case alongside the
  existing "rebase skipped, failed, or no target detected".

## ALGORITHM

```
try:
    clean = is_working_directory_clean(project_dir)
except ValueError:
    clean = True            # not a git repo - let rebase_onto_branch report that
if not clean:
    warn("Working tree is dirty - skipping rebase (likely a leftover uncommitted write)")
    return False
target = _get_rebase_target_branch(project_dir)   # unchanged from here down
```

The warning is generic about the **cause**; it must not enumerate the dirty files. File-level
detail belongs to `mcp-workspace#295`'s hardening of `rebase_onto_branch`, so the two layers do
not duplicate the same logic. Use a plain hyphen, not an em dash, matching the existing log
strings in this module.

## DATA

- Returns `bool`, unchanged: `True` only on rebase-succeeded-and-pushed; `False` on
  dirty tree, no target, rebase failed, or push failed.
- No exception ever escapes.

## TDD

1. Write both tests as direct unit calls to `_attempt_rebase_and_push` — lighter than the
   existing integration-style tests that drive `run_implement_workflow`. Patch
   `mcp_coder.workflow_steps.rebase.is_working_directory_clean`, `..._get_rebase_target_branch`,
   `...rebase_onto_branch` and `...push_changes`.

   - `test_dirty_tree_skips_rebase`: `is_working_directory_clean` → `False`. Assert the return
     is `False`, `rebase_onto_branch.assert_not_called()`, `push_changes.assert_not_called()`,
     and a `logging.WARNING` record was emitted (use `caplog`).
   - `test_clean_tree_proceeds_to_rebase`: `is_working_directory_clean` → `True`, target
     `"main"`, rebase `True`, push `True`. Assert the return is `True` and
     `rebase_onto_branch` was called with `(project_dir, "main")` — this is the path the five
     existing tests do *not* cover, since they reach the rebase through the `ValueError`
     swallow.

   Confirm `test_dirty_tree_skips_rebase` fails before the source change.
2. Add the guard, the import and the docstring line.
3. Confirm all seven tests in the file pass — the five existing ones **must not need editing**.
   If any of them requires a change, stop and report: that means the `ValueError` swallow is
   not behaving as designed.

## Verification

```
mcp__mcp-tools-py__run_format_code
mcp__mcp-tools-py__run_pylint_check
mcp__mcp-tools-py__run_pytest_check(extra_args=["-n", "auto", "tests/workflow_steps/", "tests/workflows/review/", "tests/workflows/implement/"])
mcp__mcp-tools-py__run_mypy_check
mcp__mcp-tools-py__run_lint_imports_check
```

`run_lint_imports_check` matters here: the new import must go through the
`mcp_coder.mcp_workspace_git` shim, and `workflow_steps/` sits in the middle tier of the
three-tier workflow architecture.

Then the full unit suite, then **one commit** for this step.

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_3.md`.
>
> Implement step 3 only, test-first. In `src/mcp_coder/workflow_steps/rebase.py`, add a guard
> clause at the top of `_attempt_rebase_and_push`: call `is_working_directory_clean(project_dir)`
> (imported from the `mcp_coder.mcp_workspace_git` shim, extending the existing import line),
> and when the tree is dirty log a warning naming the cause — not the individual files — and
> return `False` without attempting the rebase. `is_working_directory_clean` raises `ValueError`
> on a non-git-repo path: catch it and treat the tree as clean so the function keeps its
> "never fails workflow" contract.
>
> Add two direct unit tests to `tests/workflow_steps/test_rebase.py` (dirty tree skips the
> rebase and warns; clean tree reaches the rebase), written before the source change. Do not
> edit the five existing tests in that file — the `ValueError` swallow is what keeps them
> passing; if one needs editing, stop and report. Do not touch either caller
> (`workflows/implement/core.py`, `workflows/review/steps.py`). Run `run_format_code`, then
> pylint / pytest (`-n auto`) / mypy / lint-imports, and produce a single commit.
