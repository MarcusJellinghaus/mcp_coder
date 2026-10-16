# Step 3 — `_check_review_comments()`, `_check_ci()` bool change, priority chaining

See `pr_info/steps/summary.md` for full context. This is the main behavior
step: it wires detection into the existing `status-10` poll with the exact
conflict → CI → comments priority.

## LLM prompt

> Read `pr_info/steps/summary.md` for context, then implement
> `pr_info/steps/step_3.md` exactly as written. Follow TDD: extend
> `tests/workflows/vscodeclaude/test_session_launch_review_comments.py` (added
> in step 2) with the tests below first, confirm they fail, then implement.
> Produce exactly one commit for this step.

## WHERE

- `src/mcp_coder/workflows/vscodeclaude/session_launch.py`:
  - change `_check_ci()`'s return annotation
  - add `_check_review_comments()`
  - edit `process_eligible_issues()`'s per-issue status-10 branch and its
    pre-loop setup
- `tests/workflows/vscodeclaude/test_session_launch_review_comments.py`:
  extend with mocked-manager tests, mirroring the existing style in
  `tests/workflows/vscodeclaude/test_session_launch_process_issues.py`
  (`TestProcessEligibleIssuesMergeConflictDetection`/`...CIDetection`).

## Precondition check

Before writing any code, confirm `PullRequestManager.get_pr_feedback`,
`PRFeedback`'s `unresolved_threads`/`changes_requested`/`conversation_comments`
keys exist on the installed `mcp_workspace` package (mcp-workspace#308/#310 —
already landed per the issue, but the installed version in this environment
may differ). If `get_pr_feedback` is missing or its return dict lacks any of
those three keys, write one line to `pr_info/.blocked.txt` and stop.

## WHAT

```python
def _check_ci(
    issue: IssueData,
    ci_manager: CIResultsManager,
    branch_manager: IssueBranchManager,
    issue_manager: IssueManager,
    repo_owner: str,
    repo_name: str,
) -> bool:
    """... (unchanged body; only the return type and two `return` statements change)"""


def _check_review_comments(
    issue: IssueData,
    branch_manager: IssueBranchManager,
    issue_manager: IssueManager,
    repo_owner: str,
    repo_name: str,
    review_label_name: str,
    created_label_name: str,
) -> bool:
    """Escalate a status-10 PR to status-91 on new review feedback."""
```

## HOW

- `_check_ci()`: keep the existing body; add `return True` right after the
  successful `update_workflow_label(...)` call, and `return False` at every
  other exit path (including the `except` branch, which currently just logs).
- `_check_review_comments()`: same construction pattern as
  `_check_merge_conflict()` — `branch_manager.get_branch_with_pr_fallback(...)`
  then `_build_pr_manager(f"https://github.com/{repo_owner}/{repo_name}")`
  then `pr_manager.find_pull_request_by_head(branch)` to get the PR number.
  Wrapped in the same `try/except Exception` → log warning → `return False`
  pattern as its two siblings (never raises).
- `process_eligible_issues()`:
  - Before the per-issue loop (next to where `issue_manager`/`branch_manager`/
    `ci_manager` are built), resolve the two label names once:
    ```python
    label_lookups = build_label_lookups(
        load_labels_config(get_labels_config_path(None))
    )
    review_label_name = label_lookups["id_to_name"]["pr_review_comments"]
    created_label_name = label_lookups["id_to_name"]["pr_created"]
    ```
    New imports: `build_label_lookups`, `get_labels_config_path`,
    `load_labels_config` from `mcp_coder.config.label_config`.
  - Replace the existing
    ```python
    escalated = _check_merge_conflict(...)
    if not escalated:
        _check_ci(...)
    ```
    with:
    ```python
    _check_merge_conflict(
        issue, branch_manager, issue_manager, repo_owner, repo_name_str
    ) or _check_ci(
        issue, ci_manager, branch_manager, issue_manager, repo_owner, repo_name_str
    ) or _check_review_comments(
        issue,
        branch_manager,
        issue_manager,
        repo_owner,
        repo_name_str,
        review_label_name,
        created_label_name,
    )
    ```
    `or` short-circuits left-to-right, so each check only runs if every
    earlier one returned `False` — identical gating to the current nested
    `if`, one line instead of four.

## ALGORITHM (`_check_review_comments` body)

```
branch = branch_manager.get_branch_with_pr_fallback(issue.number, owner, repo)
if branch is None: return False
prs = _build_pr_manager(url).find_pull_request_by_head(branch)
if not prs: return False
feedback = pr_manager.get_pr_feedback(prs[0]["number"])
if feedback.unresolved_threads or feedback.changes_requested:
    triggered = True
else:
    events = issue_manager.get_issue_events(issue.number, IssueEventType.LABELED)
    watermark = _review_comments_watermark(events, review_label_name, created_label_name)
    triggered = any comment where watermark is None or comment.created_at > watermark
if triggered:
    update_workflow_label(issue_manager, "pr_created", "pr_review_comments",
                           validated_issue_number=issue.number)
    return True
return False
```

## DATA

- `feedback: PRFeedback` — accessed by key (`feedback["unresolved_threads"]`,
  `feedback["changes_requested"]`, `feedback["conversation_comments"]`); no new
  import needed since it's consumed structurally, not type-annotated locally.
- `_check_ci` / `_check_review_comments` both return `bool`: `True` iff this
  call escalated the issue.
- `process_eligible_issues()`'s per-issue expression itself returns nothing
  used by the caller — same as today, the three checks are fire-and-forget
  side effects (label transitions) within the loop.

## Tests (write first, in the extended test file)

Mirror the structure already used for merge-conflict/CI detection
(`_make_pr_issue`, `_setup_common_mocks`, mocked `labels_config`):

- `_check_ci` returns `True` when it transitions the label, `False` otherwise
  (success/pending/exception cases) — pure return-value assertions on calls
  that previously only checked `transition_issue_label` side effects.
- `_check_review_comments`:
  - unresolved thread present → escalates to `status-91`, returns `True`.
  - `changes_requested` non-empty (no threads) → escalates.
  - only `alerts` present, nothing else → does **not** escalate.
  - conversation comment present, no prior `status-91` `LABELED` event in the
    mocked `get_issue_events` return → escalates (first-ever arrival).
  - conversation comment's `created_at` before the computed watermark → does
    **not** escalate.
  - conversation comment's `created_at` after the computed watermark →
    escalates.
  - no branch / no PR found → returns `False`, never calls `get_pr_feedback`.
  - `get_pr_feedback` or `get_issue_events` raising → swallowed, returns
    `False`.
- Priority chaining in `process_eligible_issues()`:
  - merge-conflict escalation → neither `_check_ci` nor
    `_check_review_comments` is invoked that poll (extend the existing
    `test_merge_conflict_escalation_skips_ci_check_same_poll` pattern to also
    assert `get_pr_feedback`/review-comments mocks are untouched).
  - CI escalation → `_check_review_comments`'s underlying calls are not made.

## Quality checks

Run `mcp__mcp-tools-py__run_pytest_check` (fast unit markers),
`mcp__mcp-tools-py__run_pylint_check`, `mcp__mcp-tools-py__run_mypy_check`. All
must pass before committing.
