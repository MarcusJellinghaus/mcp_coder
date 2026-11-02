# Step 12 — Renormalize a line-ending-only dirty tree

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_12.md` only.
> Check the precondition first. Write the tests first, then the implementation.
> Run pylint, pytest (fast unit set, `-n auto`, plus the `git_integration` marker
> for the new tests), mypy and lint-imports until they pass, run
> `run_format_code`, and make exactly one commit.

## Precondition

The installed `mcp_workspace` must provide the two helpers from
MarcusJellinghaus/mcp-workspace#373 (renormalize paths; CR-at-EOL-only staged-diff
check) in `mcp_workspace.git_operations`. Look them up with `search_library_files`
(scope `mcp_workspace`). If either cannot be imported, write one line to
`pr_info/.blocked.txt` and stop — do **not** add the shim re-export (the shim imports
at module top; a missing name breaks every mcp-coder import).

## WHERE

- `src/mcp_coder/mcp_workspace_git.py` — re-export both helpers (+ `__all__`)
- `src/mcp_coder/workflow_steps/rebase.py`
- New test: `tests/workflow_steps/test_rebase_line_endings.py`
  (`tests/workflow_steps/test_rebase.py` is near the line limit)

## WHAT

```python
def _clear_line_ending_dirt(project_dir: Path, files: list[str]) -> bool:
    """Renormalize ``files``; commit if anything is staged. All-or-nothing.

    Returns:
        True when the tree no longer blocks the rebase; False (paths unstaged
        again) when any file has a real change, is deleted, or git fails.
    """
```

## HOW

- In `_attempt_rebase_and_push`, before the `dirty_tree` return:
  `if dirty and _clear_line_ending_dirt(project_dir, dirty): dirty = _uncommitted_tracked_files(project_dir)`;
  the existing `if dirty:` → `dirty_tree` follows unchanged.
- The commit reaches origin on every `ok` path already: `rebase_onto_branch` returns
  True when up to date and the force-with-lease push follows.
- Use `commit_paths`, `has_staged_changes`, `unstage_paths` from the shim.
- Update the function docstring (line-ending-only dirt is cleared).

## ALGORITHM

```
if any(not (project_dir / f).exists() for f in files): return False   # deletion = real change
if not renormalize(project_dir, files): unstage(files); return False
if not cr_only(project_dir, files): unstage(files); return False
if not has_staged_changes(project_dir): return True                   # stat-only dirt
ok = commit_paths("chore: renormalize line endings", [project_dir / f for f in files], project_dir)["success"]
if not ok: unstage(files)
return ok
```

`unstage(files)` = `unstage_paths([project_dir / f for f in files], project_dir)`
(also unstages anything staged before — accepted).

## DATA

`bool`; `_attempt_rebase_and_push` still returns `RebaseOutcome`.

## Tests (`@pytest.mark.git_integration`, real repo with a bare origin)

Setup: `core.autocrlf=false` in the test repo; commit `doc.md` with CRLF **before**
adding `.gitattributes` (`*.md text`); commit `.gitattributes`; rewrite / touch
`doc.md` so the stat cache doesn't hide it; assert it shows as modified.

- Line-ending-only → `_attempt_rebase_and_push` returns `ok`, a renormalize commit
  exists, tree clean, origin has the commit.
- Same plus a real content change in `doc.md` → `dirty_tree`, nothing staged, no new commit.
- A deleted tracked file → `dirty_tree`.
- Stat-only dirt (no-commit branch): call `_clear_line_ending_dirt` directly on a
  tracked, already-normalized `.md` file (its renormalize stages nothing; if git
  stages it anyway, mock `has_staged_changes` to False) → returns True, HEAD SHA
  unchanged (no commit created). Not via `_attempt_rebase_and_push`: git status
  re-checks a touched clean file and reports nothing dirty, so the helper is never reached.
