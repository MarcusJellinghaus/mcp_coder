# Step 2 — Coordinator gate

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_2.md`.
> Write the tests first, then the code. Run pylint, mypy and the fast pytest set (`-n auto`).
> Format, then make exactly one commit.

## WHERE

- `src/mcp_coder/cli/commands/coordinator/commands.py` — `execute_coordinator_run`
- `tests/cli/commands/coordinator/conftest.py` — **new**, autouse "trusted" fixture
- `tests/cli/commands/coordinator/test_commands_trust_gate.py` — **new**

## WHAT

No new public function. Inside `execute_coordinator_run`, per repo:

- `skipped: list[tuple[int, BodyTrustResult]] = []`
- the gate, placed after the "has no workflow label" `continue` and before `workflow_config = ...` / the dispatch `try`
- a `try/finally` around the `for issue in eligible_issues:` loop that logs the summary
- the message `"Successfully processed all issues in …"` reworded to `"Finished processing eligible issues in {repo_name}"`

## HOW

- `from ....workflow_utils.issue_trust import evaluate_body_trust`
- `BodyTrust` / `BodyTrustResult` come from the existing `....mcp_workspace_github` import.
- The gate sits **outside** the dispatch `try`. A `GitHubRateLimitError` from it leaves the loop, the `finally` logs
  the summary, and the existing outer `except GitHubRateLimitError` logs the stop and returns 0.
  Issues already dispatched stay dispatched.
- "Found N eligible issues" and "No eligible issues" stay before the gate, unchanged.

## ALGORITHM

```
skipped = []
try:
    for issue in eligible_issues:
        ...label check (unchanged)...
        result = evaluate_body_trust(issue_manager, issue)
        if result.status is not BodyTrust.TRUSTED:
            logger.debug("Issue #%d skipped: body %s (%s)", n, result.status.value, result.reason)
            skipped.append((n, result)); continue
        ...dispatch (unchanged)...
finally:
    if skipped:
        logger.info("Skipped %d issue(s) in %s with untrusted body: %s", len(skipped), repo_name,
                    ", ".join(f"#{n} ({r.status.value}: {r.reason})" for n, r in skipped))
```

## DATA

INFO line example:
`Skipped 2 issue(s) in mcp_coder with untrusted body: #12 (untrusted: author not trusted), #15 (lookup_failed: ConnectionError)`

## conftest.py

An autouse fixture patches `mcp_coder.cli.commands.coordinator.commands.evaluate_body_trust` to return
`BodyTrustResult(status=BodyTrust.TRUSTED, reason="")`. It keeps the existing tests that patch
`commands.IssueManager` green. New tests override it with their own `patch`.

## Tests (`test_commands_trust_gate.py`)

Follow the setup in `test_commands.py` (patches for `IssueManager`, `get_cached_eligible_issues`,
`dispatch_workflow`, Jenkins, config).

- Trusted → dispatched. Untrusted → not dispatched, no label update, no comment.
- `LOOKUP_FAILED` → not dispatched.
- INFO summary names the skipped numbers, the reasons and the count. With nothing skipped: no summary record (`caplog`).
- Issue without a workflow label → no trust lookup (call count equals the actionable issues).
- Rate limit mid-loop: issue 1 untrusted (skipped), issue 2 trusted (dispatched), issue 3's trust lookup raises
  `GitHubRateLimitError`. Then issue 2 stays dispatched, issue 3 is not dispatched, the return code is 0, and the
  `finally` summary is logged and names `#1`.
- Early `return 1` (dispatch failure) after a skipped issue → summary still logged.
- Fallback path: `get_cached_eligible_issues` raises a non-rate-limit error → `get_eligible_issues` result is gated too.
