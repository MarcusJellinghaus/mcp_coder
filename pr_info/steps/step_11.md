# Step 11 — Resume path: an open PR for the branch skips phase A

## LLM prompt
> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_11.md` exactly.
> Write the tests first, then the code.
> Run pylint, pytest (fast unit set, `-n auto`) and mypy; all must pass. Format the code and make exactly one commit.

## WHERE
- `src/mcp_coder/workflows/create_pr/pre_creation.py` (created in step 7) — `_find_open_pr`, `_resume_cleanup`
- `src/mcp_coder/workflows/create_pr/core.py` — wiring only (keeps `core.py` under the 750-line CI gate)
- `tests/workflows/create_pr/test_pre_creation.py` — helper unit tests
- New `tests/workflows/create_pr/test_resume.py` — workflow-level resume tests

## WHAT
```python
# pre_creation.py
def _find_open_pr(project_dir: Path) -> PullRequestData | None:
    """Open PR whose head is the current branch, or None (also on lookup error)."""

def _resume_cleanup(
    project_dir: Path,
    cleanup_commit_push: Callable[[Path], tuple[str, str] | None],
) -> tuple[str, str] | None:
    """On resume: if pr_info/ exists, require a clean tree, then run cleanup_commit_push.

    Returns:
        None on success or nothing to do, else (stage, message).
    """
```
`cleanup_commit_push` is passed in (core passes `_cleanup_commit_push`) because `_cleanup_commit_push` stays in
`core.py` (step 8) and `pre_creation.py` must not import `core.py` (import cycle).

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
    failure = _resume_cleanup(project_dir, _cleanup_commit_push)
    if failure: _handle_create_pr_failure(stage, message, ..., issue_number=cached_issue_number); return 1
    return 0
```
`_resume_cleanup`:
```
if not (project_dir / "pr_info").exists(): return None
if not check_git_clean(project_dir): return ("resume_cleanup", "Working tree is not clean")
return cleanup_commit_push(project_dir)
```

## HOW
- `pre_creation.py` imports: `PullRequestManager`, `PullRequestData` (`mcp_coder.mcp_workspace_github`),
  `check_git_clean` (`mcp_coder.workflow_steps.prerequisites`), `get_current_branch_name` (already imported in step 7).
- `core.py`: `from mcp_coder.workflows.create_pr.pre_creation import _find_open_pr, _rebase_if_needed, _resume_cleanup`.
- `_find_open_pr`: `get_current_branch_name`; `None` → return None. `PullRequestManager(project_dir).find_pull_request_by_head(branch)`
  (returns only open PRs, `[]` on error); wrap in `try/except Exception` → warning + None, so a lookup failure falls back
  to the normal phase A.
- It runs outside both guards, so it must never raise.
- `_resume_cleanup` runs inside the phase A guard: failure or crash → `pr_creating_failed`; a re-run retries the cleanup.
- Full prerequisites are not re-run on resume.
- Run `check_file_size(max_lines=750)`; `core.py` must stay under it.

## Tests (write first)
`test_pre_creation.py` — patch `PullRequestManager`, `get_current_branch_name`, `check_git_clean` at
`mcp_coder.workflows.create_pr.pre_creation.*`; pass a `MagicMock` as `cleanup_commit_push`:
- `_find_open_pr`: PR list `[pr]` → `pr`; `[]` → None; branch `None` → None, no manager call;
  `find_pull_request_by_head` raises → None + warning.
- `_resume_cleanup`: no `pr_info/` (`tmp_path`) → None, callable not called; `pr_info/` present + clean → callable's
  return value; `pr_info/` present + `check_git_clean` False → `("resume_cleanup", ...)`, callable not called.

`test_resume.py` — patch `_find_open_pr`, `_cleanup_commit_push`, `_resolve_issue_from_pr`, `run_post_creation`,
`update_workflow_label`, `IssueManager`, `_handle_create_pr_failure` at `mcp_coder.workflows.create_pr.core.*`
(the names bound in core), and `check_git_clean` at `mcp_coder.workflows.create_pr.pre_creation.check_git_clean`:
- Open PR, no `pr_info/` → `check_prerequisites`, `generate_pr_summary`, `create_pull_request` not called;
  `run_post_creation` called; final label applied; exit 0.
- Open PR, `pr_info/` present (use `tmp_path`), clean tree → `core._cleanup_commit_push` called, then phase B.
- Open PR, `pr_info/` present, `check_git_clean` False → `_handle_create_pr_failure` with
  `stage="resume_cleanup"`, exit 1, phase B not called.
- Open PR, `_cleanup_commit_push` returns `("push", "rejected")` → failure handler with stage `push`, exit 1.
- Open PR, linkage `None`, `_resolve_issue_from_pr` → 5: the 09f failure handler, the phase A guard's `issue_number`,
  and the final phase B label all use 5.
- Crash in `_cleanup_commit_push` on the resume path → category `pr_creating_failed` with issue 5.
- `_find_open_pr` returns None → normal phase A runs (existing tests cover the unchanged path).

## DATA
See signatures.
