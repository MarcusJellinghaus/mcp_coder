# Step 3 — `workflow_steps/merge.py`: `run_auto_merge` (+ `MergeResult` re-export)

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement **only** `pr_info/steps/step_3.md`.
> Follow TDD: write `tests/workflow_steps/test_merge.py` first (table-driven, all
> collaborators patched at `mcp_coder.workflow_steps.merge.*`), then the module.
> The module is not called by any command yet. Run format, pylint, mypy, lint-imports,
> pytest (fast unit set, `-n auto`) and make them pass. Produce exactly one commit.

## Precondition

Use `get_library_source("mcp_workspace.github_operations.PullRequestManager.merge_pull_request")`.
If it does not exist, or `mcp_workspace.github_operations` does not export `MergeResult`,
write one line to `pr_info/.blocked.txt` and stop.

## WHERE

- `src/mcp_coder/mcp_workspace_github.py` — import and add `"MergeResult"` to `__all__` (PR section)
- `tests/test_mcp_workspace_github_smoke.py` — `__all__` length +1
- New `src/mcp_coder/workflow_steps/merge.py`
- New `tests/workflow_steps/test_merge.py`

## WHAT

```python
@dataclass(frozen=True)
class MergeOutcome:
    """Final label of an auto-merge attempt plus comment fields for 74 / 99f."""
    label_id: str
    comment_fields: tuple[CommentField, ...] = ()

def is_real_green(ci_status: CIStatusData | None, ci_ok: bool, expected_sha: str | None) -> bool: ...
def resolve_merge_issue_number(project_dir: Path, branch: str) -> int | None: ...
def run_auto_merge(project_dir: Path, branch: str, *, verified_sha: str | None = None) -> MergeOutcome: ...
```

Imports: `PullRequestManager`, `CIResultsManager`, `CIStatusData`, `GithubException`,
`IssueBranchManager`, `MergeResult` from `mcp_coder.mcp_workspace_github`;
`get_latest_commit_sha`, `extract_issue_number_from_branch` from `mcp_coder.mcp_workspace_git`;
`_poll_for_ci_completion` from `workflow_steps.ci`; `_attempt_rebase_and_push`,
`_poll_mergeable_state`, `_reset_hard` from `workflow_steps.rebase`;
`is_branch_linked_to_issue` from `workflow_utils.branch_linkage`;
`as_rate_limit`, `log_rate_limit_stop` from `workflow_utils.rate_limit`;
`CommentField`, `exception_summary` from `workflow_utils.failure_handling`.
Never import `github` / `requests` or `mcp_coder.workflows`.

## ALGORITHM

`is_real_green`: `ci_status is not None and ci_ok and expected_sha is not None and ci_status.get("run", {}).get("commit_sha") == expected_sha`.

`resolve_merge_issue_number`:
```
number = extract_issue_number_from_branch(branch); if None → warn, return None
try: linked = is_branch_linked_to_issue(IssueBranchManager(project_dir=project_dir), number, branch)
except Exception: linked = None          # lookup failed
if linked is False → warn "label write skipped", return None
return number                             # True or None (lookup failed)
```

`run_auto_merge` (whole body inside one `try`):
```
prs = PullRequestManager(project_dir).find_pull_request_by_head(branch)
if len(prs) != 1 or not prs[0]["head_sha"]: warn; return MergeOutcome("pr_created")
pr = prs[0]; sha = verified_sha
for attempt in (1, 2):
    if sha is None:                                   # Step 1
        sha = get_latest_commit_sha(project_dir)
        status, ok = _poll_for_ci_completion(CIResultsManager(project_dir), branch, expected_sha=sha)
        if status is not None and not ok: return MergeOutcome("failing_ci")
        if not is_real_green(status, ok, sha): warn "soft pass"; return MergeOutcome("pr_created")
    if _pr_head_sha(project_dir, branch) != sha: warn "head mismatch"; return MergeOutcome("pr_created")
    result = PullRequestManager(project_dir).merge_pull_request(pr["number"], "squash", sha=sha,
                 commit_title=f"{pr['title']} (#{pr['number']})")      # Step 2
    if result["outcome"] == "merged": return MergeOutcome("merged")
    if result["outcome"] == "error" and result["status"] == 429: warn; return MergeOutcome("pr_created")
    if result["outcome"] == "error" or result["status"] == 409 or attempt == 2:
        return _failed(result)
    state = _poll_mergeable_state(project_dir, branch)
    if state not in ("dirty", "behind"): return _failed(result, state)
    before = get_latest_commit_sha(project_dir)                          # Step 3
    rebase = _attempt_rebase_and_push(project_dir)
    if rebase.reason == "conflict": return MergeOutcome("pr_merge_conflict", _conflict_fields(rebase))
    if not rebase.ok:
        if rebase.reason == "push_failed" and before: _reset_hard(project_dir, before)
        return _failed(result, state, rebase)
    sha = None                                        # re-poll CI on the new HEAD
except Exception as exc:
    if (rl := as_rate_limit(exc)) is not None: log_rate_limit_stop(rl); return MergeOutcome("pr_created")
    if isinstance(exc, GithubException) and exc.status in (401, 403):
        return MergeOutcome("merge_failed", (("Stage", "Auto-merge"), ("Error", exception_summary(exc))))
    raise
```

Private helpers: `_pr_head_sha(project_dir, branch) -> str | None` (re-reads
`find_pull_request_by_head`, returns the single PR's `head_sha` or `None`);
`_failed(result, state=None, rebase=None) -> MergeOutcome` builds `merge_failed` with fields;
`_conflict_fields(rebase)`.

## DATA — comment fields

- `merge_failed`: `("Stage", "Auto-merge")`, `("Error", result["message"])`,
  `("Merge outcome", result["outcome"])`, `("HTTP status", str(status) or None)`,
  `("Mergeable state", state)`; with a failed rebase also `("Reason", rebase.reason)`,
  `("Base", rebase.base_branch)`. `None` values are dropped later by `build_failure_comment`.
- `pr_merge_conflict`: `("Stage", "Auto-merge rebase")`, `("Reason", "conflict")`,
  `("Base", rebase.base_branch)`, `("Likely conflicting files", ", ".join(rebase.files) or None)`.
- Log every decision at `OUTPUT` (warnings via `logger.warning`).

## Tests (`tests/workflow_steps/test_merge.py`)

Parametrized table covering every row of the issue's Step 0–3 tables:
no PR / two PRs / no `head_sha` → `pr_created`, no merge; red → `failing_ci`; soft pass
`(None, True)` and green with other/None `commit_sha` → `pr_created`; head mismatch →
`pr_created`; merged → `merged`; 409 → `merge_failed`; refused + `blocked` → `merge_failed`
with `Mergeable state`; error 429 → `pr_created`; error 500 → `merge_failed`;
refused + `dirty` → rebase ok → re-poll → merged; retry refused → `merge_failed` (no second
rebase); rebase conflict → `pr_merge_conflict` with files; `push_failed` → `_reset_hard`
called, `merge_failed` with `Reason`; raises rate limit → `pr_created`; raises
`GithubException(401)` → `merge_failed`; raises `ValueError` → propagates.
Also: `verified_sha` given → `_poll_for_ci_completion` not called;
`merge_pull_request` called with `sha=` and `commit_title="<title> (#N)"`;
`is_real_green` and `resolve_merge_issue_number` (True / None / raised / False / no number).

## Done when

The module and tests pass, lint-imports passes, the shim smoke test passes.
