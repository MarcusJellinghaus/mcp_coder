# Step 2: Auto-merge CodeQL wait and alert gate

## LLM prompt

> Read `pr_info/steps/summary.md` and this file, and GitHub issue #1342 §4, Decisions 9,
> 13-20 and Acceptance. Implement this step with TDD: write the tests first, then the code.
> Run `run_format_code`, pylint, mypy, ruff and pytest (`-n auto`, unit-test markers); all
> must pass. Produce exactly one commit. Do not edit `pr_info/TASK_TRACKER.md`.

## Precondition

`PullRequestManager.get_pr_feedback` in the installed mcp-workspace must return `alerts`,
`unavailable` and `skipped` keys (check with `get_library_source`). If it does not, write one
line to `pr_info/.blocked.txt` and stop.

## WHERE

- `src/mcp_coder/workflow_steps/merge.py`
- `src/mcp_coder/workflow_steps/constants.py`
- New: `tests/workflow_steps/test_merge_alerts.py`
- `tests/workflow_steps/test_merge.py` (fixture and two assertions)

## WHAT

```python
# constants.py
CODE_SCANNING_MAX_POLL_ATTEMPTS = 21  # 20 intervals of 15 s = ~5 minutes max wait

# merge.py
def _wait_for_code_scanning(project_dir: Path, pr_number: int, sha: str) -> str | None:
    """Return why the alert check failed, or None to go on and read alerts."""

def _alert_check_failed(reason: str) -> MergeOutcome:
    """Build the merge_failed outcome for a failed alert check."""

def _check_alert_gate(project_dir: Path, pr_number: int, sha: str) -> MergeOutcome | None:
    """Return the outcome that blocks the merge, or None to merge."""
```

## HOW

- Call site in `run_auto_merge`, after the head-SHA guard and before the "squash-merging"
  log line:

  ```python
  blocked = _check_alert_gate(project_dir, pr["number"], sha)
  if blocked is not None:
      return blocked
  ```

- New imports in `merge.py`: `time`, and from `mcp_coder.workflow_steps.constants`:
  `CI_EXPECTED_SHA_MAX_POLL_ATTEMPTS`, `CI_LOOKUP_FAILED_MAX_POLL_ATTEMPTS`,
  `CI_POLL_INTERVAL_SECONDS`, `CODE_SCANNING_MAX_POLL_ATTEMPTS`.
- Call `get_pr_feedback(pr_number)` with **no** `include_alerts` keyword. Do not use
  `PullRequestCache`.
- Mention the alert gate in the module docstring and the `run_auto_merge` docstring.
- `_alert_check_failed` logs a warning and returns `MergeOutcome("merge_failed",
  (("Stage", "Auto-merge alert check"), ("Error", reason)))`.

## ALGORITHM

`_wait_for_code_scanning`:

```
manager = CIResultsManager(project_dir); no_run = lookup_failed = 0
for each of CODE_SCANNING_MAX_POLL_ATTEMPTS polls of get_latest_ci_status("refs/pull/N/head"):
    if lookup_failed flag: count it; at CI_LOOKUP_FAILED_MAX_POLL_ATTEMPTS return a reason
    else reset that count, and:
        run commit_sha != sha: count no_run; at CI_EXPECTED_SHA_MAX_POLL_ATTEMPTS warn, return None
        run completed: return None on success, else a reason naming the conclusion
    sleep CI_POLL_INTERVAL_SECONDS
return "code-scanning run did not complete successfully in time"
```

`_check_alert_gate`:

```
try: reason = wait; if reason: return _alert_check_failed(reason); feedback = get_pr_feedback(n)
except Exception: re-raise if as_rate_limit(exc) or GithubException 401/403; else _alert_check_failed
if unavailable["alerts"] is a rate limit: log_rate_limit_stop; return MergeOutcome("pr_created")
if unavailable["alerts"] is anything else: return _alert_check_failed(exception_summary(exc))
if alerts: OUTPUT "Auto-merge: N open code-scanning alert(s) on PR #x — not merging"; return pr_created
if skipped["alerts"]: warn "alerts not checked (status N); ..." using getattr(exc, "status", None)
return None
```

Warning text for skipped: "alerts not checked (status N); the token may lack `Code scanning
alerts: Read`, or code scanning is not enabled".

## DATA

- `get_latest_ci_status` returns `{"run": {...}, "jobs": [...]}`, or `{"run": {}, "jobs": [],
  "lookup_failed": True}`. `run` has `status`, `conclusion` and `commit_sha`.
- A CodeQL run concluding `neutral` or `skipped` is reported as `in_progress`, so it reaches
  the loop limit and ends in the final reason string.
- `get_pr_feedback` returns `alerts: list`, `unavailable: dict[str, Exception]`, `skipped:
  dict[str, Exception]`. Only the `"alerts"` key of the two dicts is read.

## Tests (write first)

`test_merge.py`:

- Add `patch(f"{_MODULE}._check_alert_gate", return_value=None) as alert_gate` to the `mocks`
  fixture and an `alert_gate: MagicMock` field to `Mocks`.
- Assert the gate is called with `(_PROJECT, 7, _SHA)` on the `verified_sha` path, and with
  `_NEW_SHA` after the rebase retry in `test_rebase_then_merged`.
- Assert that when the gate returns an outcome, `run_auto_merge` returns it and
  `merge_pull_request` is not called.

`test_merge_alerts.py` has its own fixture patching `PullRequestManager`, `CIResultsManager`,
`get_latest_commit_sha`, `_poll_for_ci_completion` and `f"{_MODULE}.time.sleep"`. Use
parametrized `side_effect` sequences where possible.

Wait:

- Run in progress, then completed success → reads alerts.
- Completed non-success → `merge_failed`.
- In progress on all 21 polls → `merge_failed`.
- Run for an older SHA → ignored, counts as no run.
- No run on 8 polls → reads alerts, warning logged.
- `lookup_failed` on 3 consecutive polls → `merge_failed`.
- One `lookup_failed`, then success → continues.
- `lookup_failed` with an empty `run` is never treated as "no run".

Gate:

- Open alert → no merge, `pr_created`, OUTPUT line.
- `unavailable["alerts"]` non-rate-limit → no merge, `merge_failed`, comment fields present.
- `get_pr_feedback` raises `RuntimeError` → no merge, `merge_failed`.
- `get_latest_ci_status` raises a non-rate-limit error (e.g. `ValueError`) → `merge_failed`.
- `skipped["alerts"]` with status 403 → merges, warning names the status.
- No alerts → merges.
- `unavailable["alerts"]` rate limit → `pr_created`, rate-limit OUTPUT line, no merge.
- `unavailable["threads"]` alone → merges.
- `get_pr_feedback` is called with exactly `(pr_number)`.

Through real `run_auto_merge`:

- `get_latest_ci_status` raises raw 429, or a rate-limit `RetryError` → `pr_created`, not
  `merge_failed`.
- `get_pr_feedback` raises `GithubException` 401 → `merge_failed` from the outer handler.
- Open alert on the `verified_sha` path → no merge.
- Open alert after a rebase retry → no second merge.
