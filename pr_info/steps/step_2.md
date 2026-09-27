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

One new import in `rebase.py`, extending the existing `mcp_workspace_git` shim import:

```python
from mcp_coder.mcp_workspace_git import get_full_status, rebase_onto_branch
```

One module-private helper plus four new tests:

```python
def _has_uncommitted_tracked_changes(project_dir: Path) -> bool: ...

def test_dirty_tree_skips_rebase(...) -> None:
def test_ignored_artifact_alone_still_skips_rebase(...) -> None:
def test_untracked_only_proceeds_to_rebase(...) -> None:
def test_clean_tree_proceeds_to_rebase(...) -> None:
```

## HOW

- Import through the local shim `mcp_coder.mcp_workspace_git`, never `mcp_workspace` directly —
  the module already does this for `rebase_onto_branch`.
- Place the guard at the **top of the function**, above `_get_rebase_target_branch`:
  `detect_base_branch` performs a remote fetch, and there is no point paying for it when the
  rebase cannot start.

### The guard models git's precondition exactly — one status read, no ignore list

The dirt classes the guard names are **staged and modified tracked entries, and nothing else**.
That is exactly what `git rebase` refuses on ("You have unstaged changes" / "Your index contains
uncommitted changes"). Two consequences, both deliberate:

- **Untracked files never count.** `git rebase` starts happily with untracked files present, so
  treating them as blocking would skip a rebase that would have succeeded, converting a green run
  into a needs-human handoff in the `review` lane — a regression, not hardening.
- **`DEFAULT_IGNORED_BUILD_ARTIFACTS` is *not* filtered here.** git has no notion of that list: a
  modified `uv.lock` makes `git rebase` refuse like any other tracked modification. Filtering it
  out would leave the tripwire silent on a tree git rejects, and the run would still end on git's
  raw stderr — the failure this step exists to eliminate. That the prerequisite check upstream
  (`workflow_steps/prerequisites.py:34`) tolerates `uv.lock` is a different question — "may we
  start work" — and has no bearing on "will git start the rebase". Naming it is not a regression:
  git refuses that tree today too, so `_attempt_rebase_and_push` already returns `False` for it;
  only the log message improves.

Step 1's `only=` guard *does* filter the list, and for the complementary reason: it is deciding
what may be swept into a round-log commit, not what git will refuse. The two uses are consistent
because they answer different questions (see summary.md).

### One call, not two

`is_working_directory_clean` is deliberately **not** used. It is not a cheap pre-filter: it calls
`get_full_status` internally (`mcp_workspace/git_operations/repository_status.py`), so a two-tier
`is_working_directory_clean(...) and _has_uncommitted_tracked_changes(...)` shape costs one full
status read on a clean tree and *two* on a dirty one, where the helper alone always costs one. It
is also logically redundant: any tree with a blocking staged/modified entry is necessarily
unclean, so the first call can never veto the helper's verdict.

Dropping it also removes the `except ValueError` branch it would have needed.
`get_full_status` **never raises** — it returns `{"staged": [], "modified": [], "untracked": []}`
for a non-git-repo and swallows unexpected errors into the same empty result — so the guard is
non-blocking on a non-repo path for free, and `_attempt_rebase_and_push` keeps its documented
"never fails workflow" contract without a try/except. This is also what keeps the eight existing
tests in `test_rebase.py` passing untouched: the five in `TestRebaseIntegration` run against
`Path("/test")`, which is not a repository, so the real `get_full_status` reports nothing pending
and they reach `rebase_onto_branch` exactly as today.

### Callers

Additive only: both callers (`workflows/implement/core.py:104`, `workflows/review/steps.py:105`)
already handle a `False` return exactly as they do today. Do not touch either caller.

Update the function docstring's `Returns:` to mention the dirty-tree case alongside the existing
"rebase skipped, failed, or no target detected", and say that untracked files alone do not count.

## ALGORITHM

```
if _has_uncommitted_tracked_changes(project_dir):
    warn("Working tree has uncommitted changes - skipping rebase "
         "(likely a leftover uncommitted write)")
    return False
target = _get_rebase_target_branch(project_dir)   # unchanged from here down
```

```
_has_uncommitted_tracked_changes(project_dir):
    # Never raises; returns {"staged": [], "modified": [], "untracked": []}
    # for a non-git-repo, so a non-repo path is simply not blocking.
    status = get_full_status(project_dir)
    return bool(status["staged"] + status["modified"])
    # untracked files are NOT blocking: git rebase tolerates them.
    # DEFAULT_IGNORED_BUILD_ARTIFACTS is NOT filtered: git refuses on a
    # modified uv.lock like any other tracked modification.
```

Index `status["staged"]`/`status["modified"]` directly: `get_full_status` always returns all three
keys, including on its non-repo and error paths. Deletions of tracked files appear under
`modified`, so they are covered.

The warning is generic about the **cause**; it must not enumerate the dirty files. File-level
detail belongs to `mcp-workspace#295`'s hardening of `rebase_onto_branch`, so the two layers do
not duplicate the same logic. Use a plain hyphen, not an em dash, matching the existing log
strings in this module.

## DATA

- Returns `bool`, unchanged: `True` only on rebase-succeeded-and-pushed; `False` on
  staged/modified-dirty tree, no target, rebase failed, or push failed.
- No exception ever escapes; `get_full_status` never raises, so no try/except is added.
- An untracked-only tree reaches the rebase exactly as today.
- A tree dirty only in `DEFAULT_IGNORED_BUILD_ARTIFACTS` (a modified `uv.lock`) is **blocking**:
  git refuses it, so the guard names it rather than letting git fail first. The return value is
  `False` either way — only the log message changes.
- A non-git-repo path is not blocking: `get_full_status` reports nothing pending, and
  `rebase_onto_branch` reports the non-repo case as it does today.

## TDD

1. Write the four tests as direct unit calls to `_attempt_rebase_and_push` — lighter than the
   existing integration-style tests that drive `run_implement_workflow`.

   All four patch `...get_full_status` only — `is_working_directory_clean` is not used, so there
   is nothing else to patch on the guard side.

   - `test_dirty_tree_skips_rebase`: `...get_full_status` →
     `{"staged": [], "modified": ["src/foo.py"], "untracked": []}`. Assert the return is `False`,
     `rebase_onto_branch.assert_not_called()`, `push_changes.assert_not_called()`, and that a
     `logging.WARNING` record was emitted (`caplog`).
   - `test_ignored_artifact_alone_still_skips_rebase`: `...get_full_status` →
     `{"staged": [], "modified": ["uv.lock"], "untracked": []}`. Assert the return is `False`,
     `rebase_onto_branch.assert_not_called()` and a `logging.WARNING`. This pins the explicit
     decision that `DEFAULT_IGNORED_BUILD_ARTIFACTS` is **not** filtered here: git refuses a
     modified `uv.lock`, so the guard must name it rather than stay silent.
   - `test_untracked_only_proceeds_to_rebase`: `...get_full_status` →
     `{"staged": [], "modified": [], "untracked": ["notes.txt"]}`. Assert `rebase_onto_branch`
     **was** called and the return is `True`. This is the regression guard: a tree git would have
     rebased must still be rebased.
   - `test_clean_tree_proceeds_to_rebase`: `...get_full_status` →
     `{"staged": [], "modified": [], "untracked": []}`, target `"main"`, rebase `True`, push
     `True`. Assert the return is `True` and `rebase_onto_branch` was called with
     `(project_dir, "main")`.

   Confirm `test_dirty_tree_skips_rebase`, `test_ignored_artifact_alone_still_skips_rebase` and
   `test_untracked_only_proceeds_to_rebase` fail before the source change.
2. Add the guard, the helper, the import and the docstring line.
3. `tests/workflow_steps/test_rebase.py` currently holds **8** tests (3 in
   `TestGetRebaseTargetBranch`, 5 in `TestRebaseIntegration`), so confirm all **12** pass — the
   8 existing ones **must not need editing**. If any of them requires a change, stop and report:
   that means the unpatched `get_full_status` is not reporting `Path("/test")` as a non-repo with
   nothing pending, which is what the non-blocking-on-non-repo behaviour rests on.

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

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_2.md`.
>
> Implement step 2 only, test-first. In `src/mcp_coder/workflow_steps/rebase.py`, add a guard
> clause at the top of `_attempt_rebase_and_push` built on a small
> `_has_uncommitted_tracked_changes` helper over `get_full_status` (imported from the
> `mcp_coder.mcp_workspace_git` shim): the helper returns `True` when `status["staged"]` or
> `status["modified"]` is non-empty, and the guard then logs a warning naming the cause — not the
> individual files — and returns `False`.
>
> Do **not** use `is_working_directory_clean`: it calls `get_full_status` internally, so it is not
> a cheap pre-filter, and a tree with a blocking staged/modified entry is unclean by definition, so
> it could never veto the helper. Do **not** filter `DEFAULT_IGNORED_BUILD_ARTIFACTS` either: git
> refuses a modified `uv.lock` like any other tracked modification, so the guard must name it.
> Untracked entries are never blocking, because `git rebase` tolerates them and the guard must not
> skip a rebase that would have succeeded. No try/except is needed — `get_full_status` never raises
> and returns empty lists for a non-git-repo — so the function keeps its "never fails workflow"
> contract as written.
>
> Add four direct unit tests to `tests/workflow_steps/test_rebase.py` (dirty tree skips and warns;
> a modified `uv.lock` alone also skips and warns; untracked-only still rebases; clean tree
> rebases), written before the source change. That file already has 8 tests, so it must end with
> 12 passing and none of the existing 8 edited — if one needs editing, stop and report. Do not
> touch either caller (`workflows/implement/core.py`, `workflows/review/steps.py`). Run
> `run_format_code`, then pylint / pytest (`-n auto`) / mypy / lint-imports, and produce a
> single commit.
