# Step 2 — fix_conflict workflow core: rebase + poll + label transition

Reference: `pr_info/steps/summary.md`. Depends on Step 1 (labels.json
entries `fixing_merge_conflict`, `pr_merge_conflict`, `pr_created` must
exist). This step adds the Jenkins-side execution logic as a plain Python
function — no CLI, no coordinator wiring yet.

## Precondition check

Read `src/mcp_coder/workflow_steps/rebase.py` and confirm
`_attempt_rebase_and_push(project_dir: Path) -> bool` still exists with that
signature. Read `src/mcp_coder/workflow_utils/label_transitions.py` and
confirm `update_workflow_label(issue_manager, from_label_id, to_label_id,
branch_name=None, validated_issue_number=None) -> bool` still exists with
that signature. Read `src/mcp_coder/mcp_workspace_github.py` and confirm it
still re-exports `PullRequestManager`, `PullRequestData`, and `IssueManager`.
If any of these do not hold, write one line to `pr_info/.blocked.txt` and
stop.

## WHERE

- `src/mcp_coder/workflows/fix_conflict/__init__.py` (new)
- `src/mcp_coder/workflows/fix_conflict/core.py` (new)
- `tests/workflows/fix_conflict/__init__.py` (new)
- `tests/workflows/fix_conflict/test_core.py` (new)

## WHAT

```python
# src/mcp_coder/workflows/fix_conflict/core.py

_POLL_ATTEMPTS = 6
_POLL_INTERVAL_SECONDS = 5

def run_fix_conflict_workflow(project_dir: Path) -> int:
    """Rebase the current branch and resolve the merge-conflict escalation.

    Returns:
        0 on any handled outcome (resolved clean, resolved still conflicting,
        or still unknown after the poll cap). 1 only on an unexpected
        exception - the Jenkins shell template's watchdog line is the
        actual safety net for a silent crash, this is just the reported
        exit code.
    """
```

Private helpers inside the same module:

```python
def _poll_mergeable_state(project_dir: Path, branch_name: str) -> Optional[str]:
    """Poll find_pull_request_by_head up to _POLL_ATTEMPTS times for a
    settled mergeable_state, sleeping _POLL_INTERVAL_SECONDS between tries.

    Returns:
        The last observed mergeable_state (may be "unknown" or None if the
        PR disappeared) after the loop ends.
    """
```

`src/mcp_coder/workflows/fix_conflict/__init__.py` re-exports
`run_fix_conflict_workflow`, mirroring `workflows/create_pr/__init__.py`.

## HOW

- Imports: `from mcp_coder.mcp_workspace_git import get_current_branch_name`,
  `from mcp_coder.mcp_workspace_github import IssueManager, PullRequestManager`,
  `from mcp_coder.workflow_steps.rebase import _attempt_rebase_and_push`,
  `from mcp_coder.workflow_utils.label_transitions import update_workflow_label`.
- `PullRequestManager(project_dir)` — plain constructor call. This module
  runs inside the Jenkins job's own checkout, so no `repo_url` bypass is
  needed here (that bypass is only for Step 5's checkout-less detection).
- No `run_guarded`/`GuardOutcome` — single `try/except Exception` around
  the whole body of `run_fix_conflict_workflow`, logging and returning `1`.

## ALGORITHM

```
branch = get_current_branch_name(project_dir); if None: log error, return 1
_attempt_rebase_and_push(project_dir)  # best-effort; log its bool, don't branch on it
state = _poll_mergeable_state(project_dir, branch)
if state == "dirty":
    update_workflow_label(IssueManager(project_dir), "fixing_merge_conflict", "pr_merge_conflict")
elif state not in (None, "unknown"):
    update_workflow_label(IssueManager(project_dir), "fixing_merge_conflict", "pr_created")
else:
    log "still unknown after poll cap - leaving at status-72 for next coordinator poll"
return 0
```

`_poll_mergeable_state`:

```
state = None
for attempt in range(_POLL_ATTEMPTS):
    prs = PullRequestManager(project_dir).find_pull_request_by_head(branch_name)
    state = prs[0]["mergeable_state"] if prs else None
    if state not in (None, "unknown"):
        return state
    if attempt < _POLL_ATTEMPTS - 1:
        time.sleep(_POLL_INTERVAL_SECONDS)
return state
```

## DATA

- Return type: `int` (0 or 1), matching `create-pr`'s simple exit-code
  contract (not `rebase`'s three-way 0/1/2 — that distinction isn't needed
  here).
- `_poll_mergeable_state` returns `Optional[str]`: one of GitHub's
  `mergeable_state` values, or `None` if no open PR was found for the
  branch on the final attempt.

## TDD order

1. Write `tests/workflows/fix_conflict/test_core.py` first, mocking
   `get_current_branch_name`, `_attempt_rebase_and_push`,
   `PullRequestManager`, `IssueManager`, `update_workflow_label`, and
   `time.sleep` (so tests don't actually sleep). Cover:
   - `mergeable_state` resolves to `"dirty"` on first poll →
     `update_workflow_label` called with `to_label_id="pr_merge_conflict"`,
     returns 0.
   - resolves to `"clean"` → called with `to_label_id="pr_created"`,
     returns 0.
   - stays `"unknown"` for all 6 attempts → `update_workflow_label` never
     called, `time.sleep` called 5 times, returns 0.
   - `find_pull_request_by_head` returns `[]` throughout → treated like
     `None`/unresolved, no label update, returns 0.
   - `get_current_branch_name` returns `None` → returns 1, no rebase
     attempted.
   - an unexpected exception anywhere in the body → caught, logged,
     returns 1.
   Run the suite — it must fail (module doesn't exist yet).
2. Implement `core.py` and `__init__.py` to make the tests pass.

## Checks before commit

pylint, pytest (fast unit marker set), mypy,
`mcp__mcp-tools-py__run_format_code`. All must pass.

## Commit message

```
feat(fix_conflict): add mechanical rebase workflow core
```

## LLM prompt for this step

> Read `pr_info/steps/summary.md` for the overall design, then implement
> `pr_info/steps/step_2.md` exactly as written. Follow TDD: write
> `tests/workflows/fix_conflict/test_core.py` first and confirm it fails,
> then add `src/mcp_coder/workflows/fix_conflict/core.py` and `__init__.py`
> to make it pass. If this step's "Precondition check" section fails,
> write one line to `pr_info/.blocked.txt` and stop. Otherwise make one
> commit containing the new test file and the new module, after
> formatters/pylint/pytest/mypy all pass.
