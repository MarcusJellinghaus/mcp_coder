# Step 4 — Low-level git helpers

Goal: the small deterministic git operations Python needs that are not exposed by
the `mcp_workspace_git` shim: raw-git runner, mid-rebase detection, abort, hard
reset, and the "success shape" check. One commit.

## WHERE
- MODIFY `src/mcp_coder/workflows/rebase.py` (add functions below).
- CREATE `tests/workflows/rebase/test_git_helpers.py` (git-backed;
  mark `@pytest.mark.git_integration`).

## WHAT
```python
def _run_git(project_dir: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run `git <args>` in project_dir (list form, no shell, check=False)."""

def _is_rebase_in_progress(project_dir: Path) -> bool:
    """True if .git/rebase-merge or .git/rebase-apply exists."""

def _abort_rebase(project_dir: Path) -> None:
    """Best-effort `git rebase --abort` (no raise)."""

def _reset_hard(project_dir: Path, sha: str) -> None:
    """`git reset --hard <sha>` to restore pre-rebase state."""

def _rebase_success_shape(project_dir: Path, pre_sha: str) -> bool:
    """True iff HEAD moved off pre_sha, tree is clean, and not mid-rebase."""
```

## HOW
- `import subprocess` (list args, no `shell`; add `# nosec`-style justification if
  bandit flags B603/B607 — mirror existing subprocess usage in the repo).
- `_rebase_success_shape` uses `get_latest_commit_sha` and
  `is_working_directory_clean` from `mcp_coder.mcp_workspace_git`, plus
  `_is_rebase_in_progress`.
- `_is_rebase_in_progress` reads the filesystem (`project_dir/".git"/...`), no
  subprocess.

## ALGORITHM
```
_is_rebase_in_progress:
  g = project_dir/".git"
  return (g/"rebase-merge").exists() or (g/"rebase-apply").exists()

_rebase_success_shape:
  if _is_rebase_in_progress(project_dir): return False
  if not is_working_directory_clean(project_dir): return False
  return get_latest_commit_sha(project_dir) != pre_sha
```

## DATA
- `_run_git` → `subprocess.CompletedProcess[str]` (`.returncode`, `.stdout`, `.stderr`).
- Others → `bool` / `None`.

## TESTS (write first) — `git_integration`
`test_git_helpers.py` using a temp git repo fixture:
1. `_is_rebase_in_progress` False on a clean repo; simulate by creating
   `.git/rebase-merge/` dir → True.
2. `_rebase_success_shape`: False when HEAD == pre_sha; after a new commit and
   clean tree → True; with a dirty tree → False.
3. `_reset_hard` returns HEAD to a captured sha after a new commit.
4. `_abort_rebase` does not raise when no rebase is in progress.
5. `_run_git(repo, "rev-parse", "HEAD")` returns `returncode == 0`.

## LLM PROMPT
> Read `pr_info/steps/summary.md` and `pr_info/steps/step_4.md`. Implement Step 4
> (TDD). First write `tests/workflows/rebase/test_git_helpers.py`
> (`@pytest.mark.git_integration`, temp-repo fixture) covering `_run_git`,
> `_is_rebase_in_progress`, `_abort_rebase`, `_reset_hard`, and
> `_rebase_success_shape` per this step. Then add those functions to
> `src/mcp_coder/workflows/rebase.py`, reusing `get_latest_commit_sha` and
> `is_working_directory_clean` from `mcp_coder.mcp_workspace_git`. Use
> `subprocess.run` with list args (no shell). Run pylint, pytest
> (include the git_integration marker for this file), mypy, and bandit; fix
> everything. Exactly one commit.
