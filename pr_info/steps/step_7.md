# Step 7 — `create-plan` warns on an untrusted body

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_7.md`.
> Write the tests first, then the code. Run pylint, mypy and the fast pytest set (`-n auto`).
> Format, then make exactly one commit.

## WHERE

- `src/mcp_coder/workflows/create_plan/prerequisites.py` — `check_prerequisites`
- `tests/workflows/create_plan/test_prerequisites_trust.py` — **new**

`implement` and `create-pr` are unchanged.

## WHAT

No signature change. A new block in `check_prerequisites`, after the existing fetch `try`/`except` and before
`logger.info("All prerequisites passed")`.

## HOW

- `from mcp_coder.workflow_utils.issue_trust import evaluate_body_trust`
- Add `BodyTrustStatus` and `GitHubRateLimitError` to the existing `mcp_coder.mcp_workspace_github` import.
- Reuse the `issue_manager` and `issue_data` from the fetch block.

## ALGORITHM

```
try:
    trust = evaluate_body_trust(issue_manager, issue_data)
    if trust.status is BodyTrustStatus.UNTRUSTED:
        logger.warning("⚠ Issue #%d body is untrusted (%s) — continuing; plan input is not vetted", n, trust.reason)
    elif trust.status is BodyTrustStatus.LOOKUP_FAILED:
        logger.warning("⚠ Could not verify body trust for issue #%d (%s) — continuing", n, trust.reason)
except GitHubRateLimitError:
    logger.warning("⚠ GitHub rate limit while checking body trust for issue #%d — continuing", n)
```

## DATA

Return value unchanged: `(True, issue_data)` in all three new cases.

## Tests (`test_prerequisites_trust.py`)

Patch `prerequisites.IssueManager` and `prerequisites.evaluate_body_trust`.

- Trusted → `(True, issue)`, no warning.
- Untrusted → `(True, issue)`, one warning mentioning "untrusted".
- `LOOKUP_FAILED` → `(True, issue)`, a different warning ("Could not verify").
- `GitHubRateLimitError` → `(True, issue)`, a warning, no exception.
- Issue not found (`number == 0`) → no trust lookup.
