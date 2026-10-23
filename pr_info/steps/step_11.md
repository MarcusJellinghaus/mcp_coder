# Step 11 — Resume path: an open PR for the branch skips phase A

## LLM prompt
> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_11.md` exactly.
> Write `tests/workflows/create_pr/test_resume.py` first, then the code.
> Run pylint, pytest (fast unit set, `-n auto`) and mypy; all must pass. Format the code and make exactly one commit.

## WHERE
- `src/mcp_coder/workflows/create_pr/core.py`
- New `tests/workflows/create_pr/test_resume.py`

## WHAT
```python
def _find_open_pr(project_dir: Path) -> PullRequestData | None:
    """Open PR whose head is the current branch, or None (also on lookup error)."""

def _resume_cleanup(project_dir: Path) -> tuple[str, str] | None:
    """On resume: if pr_info/ exists, require a clean tree, then _cleanup_commit_push.

    Returns:
        None on success or nothing to do, else (stage, message).
    """
```

## ALGORITHM
Before the phase A guard, in `run_create_pr_workflow`:
```
existing_pr = _find_open_pr(project_dir)
if existing_pr and update_issue_labels and cached_issue_number is None:
    cached_issue_number = _resolve_issue_from_pr(project_dir, existing_pr["number"])
```
At the top of `phase_a()`:
```
if existing_pr:
    log OUTPUT "PR #N already exists - resuming at post-creation checks"
    failure = _resume_cleanup(project_dir)
    if failure: _handle_create_pr_failure(stage, message, ..., issue_number=cached_issue_number); return 1
    return 0
```
`_resume_cleanup`:
```
if not (project_dir / "pr_info").exists(): return None
if not check_git_clean(project_dir): return ("resume_cleanup", "Working tree is not clean")
return _cleanup_commit_push(project_dir)
```

## HOW
- `_find_open_pr`: `get_current_branch_name`; `None` → return None. `PullRequestManager(project_dir).find_pull_request_by_head(branch)`
  (returns only open PRs, `[]` on error); wrap in `try/except Exception` → warning + None, so a lookup failure falls back
  to the normal phase A.
- It runs outside both guards, so it must never raise.
- `_resume_cleanup` runs inside the phase A guard: failure or crash → `pr_creating_failed`; a re-run retries the cleanup.
- Full prerequisites are not re-run on resume.

## Tests (write first)
- Open PR, no `pr_info/` → `check_prerequisites`, `generate_pr_summary`, `create_pull_request` not called;
  `run_post_creation` called; final label applied; exit 0.
- Open PR, `pr_info/` present (use `tmp_path`), clean tree → `_cleanup_commit_push` called, then phase B.
- Open PR, `pr_info/` present, `check_git_clean` False → `_handle_create_pr_failure` with
  `stage="resume_cleanup"`, exit 1, phase B not called.
- Open PR, `_cleanup_commit_push` returns `("push", "rejected")` → failure handler with stage `push`, exit 1.
- Open PR, linkage `None`, `_resolve_issue_from_pr` → 5: the 09f failure handler, the phase A guard's `issue_number`,
  and the final phase B label all use 5.
- Crash in `_resume_cleanup` → category `pr_creating_failed` with issue 5.
- `find_pull_request_by_head` raises → normal phase A runs.
- No open PR → phase A unchanged (existing tests).

## DATA
See signatures. `PullRequestData` from `mcp_coder.mcp_workspace_github` (already imported).
