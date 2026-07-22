# Step 5 — Guards (pre-flight, base-branch, pr_info-on-base)

Goal: the three deterministic guards that gate the LLM session. Each returns an
error message string (→ exit `2`) or `None`/resolved value. One commit.

## WHERE
- MODIFY `src/mcp_coder/workflows/rebase.py` (add functions below).
- CREATE `tests/workflows/rebase/test_guards.py` (`@pytest.mark.git_integration`).

## WHAT
```python
def _preflight(project_dir: Path) -> str | None:
    """None if OK, else an error message. Checks: clean tree, not mid-rebase/merge,
    not on main/master, origin remote exists."""

def _resolve_base_branch(
    project_dir: Path, base_branch_arg: str | None
) -> tuple[str | None, str | None]:
    """Return (base_branch, error). Explicit arg wins; else auto-detect and accept
    only main/master, otherwise error requesting --base-branch."""

def _check_pr_info_absent_on_base(project_dir: Path, base_branch: str) -> str | None:
    """None if pr_info/ is absent on origin/<base>, else an error message."""
```

## HOW
- Reuse `is_working_directory_clean`, `get_current_branch_name`,
  `detect_base_branch` (`mcp_coder.workflow_utils.base_branch`), plus Step 4's
  `_is_rebase_in_progress` and `_run_git`.
- `_preflight` "not mid-merge": also check `(.git/MERGE_HEAD).exists()`.
- `_preflight` "origin exists": `_run_git(project_dir, "remote", "get-url", "origin").returncode == 0`.
- `_check_pr_info_absent_on_base`: `_run_git(project_dir, "ls-tree",
  f"origin/{base_branch}", "pr_info")` — non-empty stdout ⇒ present ⇒ error.

## ALGORITHM
```
_resolve_base_branch:
  if base_branch_arg: return (base_branch_arg, None)
  detected = detect_base_branch(project_dir)
  if detected is None: return (None, "Could not detect base branch; pass --base-branch")
  if detected in {"main","master"}: return (detected, None)
  return (None, f"Non-standard base '{detected}'; pass --base-branch to confirm")

_preflight:
  if not clean: return "Working tree not clean"
  if _is_rebase_in_progress or MERGE_HEAD: return "Repository is mid-rebase/merge"
  if current_branch in {"main","master"}: return "Refusing to rebase main/master"
  if origin missing: return "Remote 'origin' not found"
  return None
```

## DATA
- `_preflight`, `_check_pr_info_absent_on_base` → `str | None`.
- `_resolve_base_branch` → `tuple[str | None, str | None]`.

## TESTS (write first) — `git_integration`
`test_guards.py`:
- `_resolve_base_branch`: explicit arg returned verbatim; detected `main` accepted;
  a non-standard detected branch → error mentioning `--base-branch`; `None`
  detection → error.
- `_preflight`: clean feature-branch repo with origin → `None`; dirty tree →
  message; on `main` → message; missing origin → message.
- `_check_pr_info_absent_on_base`: base without `pr_info/` → `None`; base with a
  committed `pr_info/` file → error. (Use a fixture with a local `origin` remote.)

## LLM PROMPT
> Read `pr_info/steps/summary.md` and `pr_info/steps/step_5.md`. Implement Step 5
> (TDD). First write `tests/workflows/rebase/test_guards.py`
> (`@pytest.mark.git_integration`) covering `_preflight`, `_resolve_base_branch`,
> and `_check_pr_info_absent_on_base` per this step. Then add those functions to
> `src/mcp_coder/workflows/rebase.py`, reusing `detect_base_branch`,
> `is_working_directory_clean`, `get_current_branch_name`, and the Step 4 helpers.
> Run pylint, pytest (with git_integration for this file), mypy, bandit; fix
> everything. Exactly one commit.
