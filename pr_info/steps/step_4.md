# Step 4 — no-retry classified exit in `_wait_for_new_ci_run`

Part of issue #1183. Read `pr_info/steps/summary.md` first. Depends on Step 1
(`_classify_ci_exception`).

## Precondition

`_wait_for_new_ci_run` in `src/mcp_coder/workflow_steps/ci.py` must still
catch exceptions with `logger.warning(...)` + `continue` (i.e. still retries
on error, up to `CI_NEW_RUN_MAX_POLL_ATTEMPTS`). If it no longer does, write
one line to `pr_info/.blocked.txt` describing what it does instead and stop.

## Goal

`_wait_for_new_ci_run` currently retries a raised exception up to 6 times —
the one place in this file that still retries a raised exception, which
contradicts "never retry a raised exception" (rate-limit safety). Change it
to exit immediately on any raised exception, logging the same kind of
classified INFO line as the poll, and returning `(None, False)` directly
(not by falling out of the loop — falling out would log the misleading
"No new CI run detected after 30s" warning line). `lookup_failed` is
deliberately **not** handled here: an empty/lookup-failed run just continues
the existing bounded 6-attempt loop unchanged.

## TDD order

1. Add the tests below to `tests/workflow_steps/test_ci.py` first (new
   module-level tests for `_wait_for_new_ci_run` — nothing currently tests
   this function at all).
2. Change the `except Exception` branch until they pass.

## WHERE

`src/mcp_coder/workflow_steps/ci.py`, inside `_wait_for_new_ci_run`:

```python
try:
    new_status = ci_manager.get_latest_ci_status(branch)
except Exception as e:
    logger.warning(f"API error checking for new CI run: {e}")
    continue
```

## WHAT

No new function signature; `_wait_for_new_ci_run`'s own signature
(`(ci_manager, branch, previous_run_ids) -> tuple[Optional[CIStatusData],
bool]`) is unchanged.

## HOW

Reuse `_classify_ci_exception` from Step 1 (same module, no new import
needed beyond what Step 1 already added). Change the log level from
`warning` to `info` to match the poll's `CI_API_ERROR` line and keep the
same prefix for grep-ability.

## ALGORITHM

```
try:
    new_status = ci_manager.get_latest_ci_status(branch)
except Exception as e:
    logger.info(
        f"CI_API_ERROR: Could not retrieve CI status while waiting for a "
        f"new run - skipping CI check ({_classify_ci_exception(e)})"
    )
    return None, False   # direct return, not `break` - skips the misleading
                         # "No new CI run detected after 30s" warning below
```

Everything else in the function (the `new_run_ids` comparison, the
`time.sleep`, the final `logger.warning("No new CI run detected after
30s")` + `return None, False` on timeout) is untouched.

## DATA

Return type unchanged: `tuple[Optional[CIStatusData], bool]`. The contract
the caller relies on (`check_and_fix_ci`'s `if not new_run_detected: return
True`) is preserved — an exception now reaches that same `(None, False)`
shape, just sooner.

## Tests to add

`tests/workflow_steps/test_ci.py`, new class
`TestWaitForNewCiRunNoRetryOnException` (import `_wait_for_new_ci_run` at
the top of the file alongside the existing `_poll_for_ci_completion`
import):

- `test_raised_exception_exits_immediately_no_retry` —
  `mock_ci_manager.get_latest_ci_status.side_effect = GithubException(status=403,
  headers={"Retry-After": "5"})`; call `_wait_for_new_ci_run(mock_ci_manager,
  "main", previous_run_ids=set())` with `time.sleep` patched; assert result
  is `(None, False)`, `get_latest_ci_status` called exactly once (not up to
  6 times), and `caplog` contains `"rate limit"`.
- `test_raised_generic_exception_also_exits_immediately` — same shape with
  `ValueError("boom")`; assert `(None, False)`, one call, `"unexpected
  error"` in `caplog`, and the function does NOT log "No new CI run detected
  after 30s" (that warning text must be absent — proves the direct `return`
  was taken, not a fall-through).
- `test_timeout_without_exception_still_warns_as_before` (regression guard)
  — `get_latest_ci_status` always returns an empty/no-new-run status (e.g.
  `{"run": {"run_ids": []}, "jobs": []}`) for all
  `CI_NEW_RUN_MAX_POLL_ATTEMPTS` calls; assert the existing "No new CI run
  detected after 30s" warning IS logged and the result is `(None, False)` —
  proving the no-exception timeout path is unchanged.

## Commit

One commit: the three tests above + the `_wait_for_new_ci_run` change,
passing pylint/pytest/mypy.

## LLM prompt

> Implement Step 4 of `pr_info/steps/summary.md` (issue #1183) exactly as
> described in `pr_info/steps/step_4.md`. Add the three tests first (they
> must fail against today's retry-on-exception code), then change
> `_wait_for_new_ci_run`'s `except Exception` branch to classify via
> `_classify_ci_exception` and `return None, False` directly instead of
> `continue`. Do not touch the non-exception timeout path or
> `check_and_fix_ci`'s call site. Run pylint/pytest/mypy; all must pass.
> Make exactly one commit.
