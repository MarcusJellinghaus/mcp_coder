# Step 3 — bounded `lookup_failed` retry budget in `_poll_for_ci_completion`

Part of issue #1183. Read `pr_info/steps/summary.md` first, especially the
"correctness detail" paragraph about why `lookup_failed` cannot be nested
inside the existing `len(run_info) == 0` check.

## Precondition

`_poll_for_ci_completion`'s existing "waiting, bounded by a sub-budget"
branch (the `if len(run_info) == 0 or is_other_commit:` block, with
`other_commit_attempts` / `CI_EXPECTED_SHA_MAX_POLL_ATTEMPTS`) must still be
present in `src/mcp_coder/workflow_steps/ci.py` in roughly its current shape.
If it has been restructured so this description no longer matches, write one
line to `pr_info/.blocked.txt` describing the mismatch and stop.

## Goal

A `run` dict carrying `lookup_failed=True` (added by a swallowed GitHub
lookup failure, per mcp-workspace#318) must not be read as "still waiting
indefinitely" or as "no run / stale commit" — it gets its **own** small,
bounded retry budget (3 consecutive attempts, normal 15s cadence, no extra
API load), separate from `CI_MAX_POLL_ATTEMPTS` and from
`other_commit_attempts`. On older `mcp_workspace` installs where the key
never appears, `.get("lookup_failed")` is always falsy and behaviour is
byte-for-byte unchanged — this must hold whether or not the key is present.

## TDD order

1. Add the new constant's test coverage implicitly via the behavioral tests
   below (no standalone test for a bare constant).
2. Add all tests listed below to `tests/workflow_steps/test_ci.py` first —
   they fail against today's code (no `lookup_failed` handling exists).
3. Add `CI_LOOKUP_FAILED_MAX_POLL_ATTEMPTS` to `constants.py`, then modify
   `_poll_for_ci_completion` until all new and existing tests pass.

## WHERE

- `src/mcp_coder/workflow_steps/constants.py` — add, right after
  `CI_EXPECTED_SHA_MAX_POLL_ATTEMPTS`:
  ```python
  # A burst of swallowed GitHub lookup failures (5xx, network, repo-lookup
  # failure - see mcp-workspace#318's `lookup_failed` flag) is a different
  # failure mode from CI legitimately taking a while, so it gets its own
  # small budget rather than sharing CI_MAX_POLL_ATTEMPTS. Normal 15s
  # cadence - no extra API load versus today's poll.
  CI_LOOKUP_FAILED_MAX_POLL_ATTEMPTS = 3  # Max 3 consecutive attempts = ~30s max added wait
  ```
- `src/mcp_coder/workflow_steps/ci.py` — import the new constant from
  `.constants`; modify `_poll_for_ci_completion`.

## WHAT

No new function signatures. `_poll_for_ci_completion`'s existing body gains
one local counter (`lookup_failed_attempts = 0`, initialised alongside
`other_commit_attempts`) and the waiting branch's condition/messages are
extended to cover the `lookup_failed` case.

## HOW

Everything stays inside the existing `for poll_attempt in
range(CI_MAX_POLL_ATTEMPTS):` loop, in the same branch that already handles
"no run yet" / "run for another commit" — do not add a second, parallel
branch. The only new top-level condition is `lookup_failed`, computed right
after `run_info = ci_status.get("run", {})` and used in the outer `if`
alongside the existing two.

## ALGORITHM

```
run_info = ci_status.get("run", {})
lookup_failed = bool(run_info.get("lookup_failed"))      # False if key absent (older installs)

if lookup_failed:
    lookup_failed_attempts += 1
else:
    lookup_failed_attempts = 0                            # any non-lookup_failed read resets it

... existing observed_sha / is_other_commit computation, unchanged ...

if lookup_failed or len(run_info) == 0 or is_other_commit:
    if lookup_failed:
        budget_spent = lookup_failed_attempts >= CI_LOOKUP_FAILED_MAX_POLL_ATTEMPTS
    elif is_other_commit:
        budget_spent = other_commit_attempts >= CI_EXPECTED_SHA_MAX_POLL_ATTEMPTS
    else:
        budget_spent = False

    if poll_attempt < CI_MAX_POLL_ATTEMPTS - 1 and not budget_spent:
        waiting_for = (
            "GitHub lookup failed for the latest CI run"
            if lookup_failed
            else f"Latest CI run is for {...}, waiting for {...}" if is_other_commit
            else "No CI run found yet"
        )
        log debug, sleep CI_POLL_INTERVAL_SECONDS, continue

    if lookup_failed:
        logger.info(
            "CI_API_ERROR: GitHub lookup failed %d consecutive time(s) - "
            "skipping CI check", lookup_failed_attempts,
        )
    elif is_other_commit:
        ... existing CI_TIMEOUT log, unchanged ...
    else:
        ... existing CI_NOT_CONFIGURED log, unchanged ...
    return None, True
```

Note the `lookup_failed` check comes first in the `if`/`elif` chain deciding
the budget/message/exit-log, even though the outer condition is a plain
`or` — this is what "checked before the `len(run_info) == 0` branch" means
in practice (the summary's correctness note explains why the outer `or` is
required: a `lookup_failed` run is not length-0 once the flag key is
present).

## DATA

Return type is unchanged: `tuple[Optional[CIStatusData], bool]`. No new
public data structures — `lookup_failed_attempts` is a local `int`.

## Tests to add

`tests/workflow_steps/test_ci.py`, new class
`TestPollForCiCompletionLookupFailed`. Build run payloads like the existing
`_run` helper in `TestPollForCiCompletionShaCorrelation`, but for a lookup
failure use `{"run": {"lookup_failed": True}, "jobs": []}` (deliberately
*not* an empty dict, to exercise the length-mismatch correctness detail):

- `test_lookup_failed_retries_then_succeeds` — 2 lookup-failed reads, then a
  normal completed/success read. Assert `get_latest_ci_status` called 3
  times, `time.sleep` called twice, final result is `(status, True)` with
  the success status.
- `test_lookup_failed_exhausts_to_graceful_exit` — 3 consecutive
  lookup-failed reads (`CI_LOOKUP_FAILED_MAX_POLL_ATTEMPTS`). Assert the
  call count is exactly 3 (no 4th call), result is `(None, True)`, and
  `caplog` contains `"lookup failed"` and `"3"`.
- `test_lookup_failed_counter_resets_on_successful_read` — lookup-failed,
  lookup-failed, then one normal **in-progress** read (non-`lookup_failed`,
  resets the counter), then 3 more lookup-failed reads exhausting the
  *fresh* budget, then nothing further. Assert total call count is exactly
  `2 + 1 + 3 = 6` and the result is `(None, True)` — proving the first two
  lookup-failures did not count toward the second exhaustion.
- `test_lookup_failed_checked_before_empty_run_branch` — a single
  lookup-failed read whose `run` dict is `{"lookup_failed": True}` (length
  1, not 0). Assert it is retried (not misread as "in progress" / not
  immediately treated as `CI_NOT_CONFIGURED`) — i.e. `time.sleep` is called
  and a second `get_latest_ci_status` call happens, with the second call
  returning a normal completed/success status to end the test deterministically.
- `test_lookup_failed_absent_key_behaves_as_before` (regression guard for
  older `mcp_workspace` installs) — a run dict that is genuinely empty
  (`{}`, no `lookup_failed` key at all) followed by a completed/success run,
  mirroring the existing `test_elapsed_time_in_no_run_found_log` /
  `test_a_run_without_a_sha_is_accepted`-style payload shape; assert the
  result and call count match pre-existing behaviour (i.e. this is purely a
  "nothing broke" check, reusing the existing "No CI run found yet" code
  path).

## Commit

One commit: the constant, the `_poll_for_ci_completion` changes, and the
five tests above, passing pylint/pytest/mypy.

## LLM prompt

> Implement Step 3 of `pr_info/steps/summary.md` (issue #1183) exactly as
> described in `pr_info/steps/step_3.md`. Follow TDD: add the five tests
> first (they must fail against today's code), then add
> `CI_LOOKUP_FAILED_MAX_POLL_ATTEMPTS` to `constants.py` and extend
> `_poll_for_ci_completion`'s existing waiting branch (do not add a second,
> parallel branch) until all tests — new and pre-existing — pass. Pay
> particular attention to the `test_lookup_failed_checked_before_empty_run_branch`
> case: `lookup_failed` must be checked as a top-level `or` condition, not
> nested inside `len(run_info) == 0`. Run pylint/pytest/mypy; all must pass.
> Make exactly one commit.
