# Step 2 — wire the classifier into `_poll_for_ci_completion`'s exception branch

Part of issue #1183. Read `pr_info/steps/summary.md` first. Depends on Step 1
(`_classify_ci_exception` must already exist and be tested).

## Precondition

`_poll_for_ci_completion`'s `except Exception as e:` branch (the one that
currently does `logger.info(f"CI_API_ERROR: ... ({e})")` and
`return None, True`) must still look like that in
`src/mcp_coder/workflow_steps/ci.py`. If it has materially changed shape
(e.g. the exception handling moved to a different function), write one line
to `pr_info/.blocked.txt` describing what changed and stop.

## Goal

Replace the raw `{e}` interpolation in that one existing log line with
`_classify_ci_exception(e)`, so a raised rate-limit/auth error gets a
specific, actionable INFO line instead of the bare exception repr. **No
control-flow change** — it already exits immediately with `(None, True)` and
never retries; this step only changes what gets logged.

## TDD order

1. Add the tests below to `tests/workflow_steps/test_ci.py` first (they will
   fail against today's `{e}`-only log line, since they assert on the
   classified wording).
2. Change the one log line to use `_classify_ci_exception(e)` until they pass.

## WHERE

`src/mcp_coder/workflow_steps/ci.py`, inside `_poll_for_ci_completion`:

```python
try:
    ci_status = ci_manager.get_latest_ci_status(branch)
except Exception as e:
    logger.info(
        f"CI_API_ERROR: Could not retrieve CI status - skipping CI check ({e})"
    )
    return None, True  # Graceful exit on API errors
```

## WHAT

No new function. One-line change: `({e})` → `({_classify_ci_exception(e)})`.

## HOW

`_classify_ci_exception` is already imported-by-locality (same module, Step
1). Just call it in the f-string in place of `e`.

## ALGORITHM

Not applicable — single substitution, no new branching.

## DATA

No new data structures; the return tuple `(None, True)` is unchanged.

## Tests to add

`tests/workflow_steps/test_ci.py`, new class
`TestPollExceptionClassification` (or add to an existing class covering
`_poll_for_ci_completion`):

- `test_rate_limit_exception_exits_immediately_with_classified_line` —
  `mock_ci_manager.get_latest_ci_status.side_effect =
  GithubException(status=403, headers={"Retry-After": "10"})`; assert
  `_poll_for_ci_completion(...)` returns `(None, True)`, that
  `get_latest_ci_status` was called exactly once (no retry), and that
  `caplog` contains `"rate limit"`.
- `test_auth_exception_exits_immediately_with_classified_line` — same shape
  with `GithubException(status=401)`; assert one call, `(None, True)`, and
  `"auth/permission"` in `caplog`.
- `test_non_github_exception_still_exits_immediately` — `ValueError("boom")`
  as the side effect; assert `(None, True)`, one call, `"unexpected error"`
  and `"boom"` in `caplog`, and NOT `"auth/permission"`.

All three use `patch("mcp_coder.workflow_steps.ci.time.sleep")` like the
existing tests in this file, even though no sleep should occur on this path
(it documents that no retry/backoff happens).

## Commit

One commit: the three tests above + the one-line wiring change, passing
pylint/pytest/mypy.

## LLM prompt

> Implement Step 2 of `pr_info/steps/summary.md` (issue #1183) exactly as
> described in `pr_info/steps/step_2.md`. Add the three tests first (they
> should fail against the current raw-exception log line), then change
> `_poll_for_ci_completion`'s existing `except Exception` log line to use
> `_classify_ci_exception(e)` from Step 1. Do not alter the
> `return None, True` control flow — only the log message. Run
> pylint/pytest/mypy; all must pass. Make exactly one commit.
