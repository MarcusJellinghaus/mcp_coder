# Step 2 — CI polling: cap the "no run" wait when `expected_sha` is given

## LLM prompt
> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_2.md` exactly.
> Write the tests first, then change the code. Run pylint, pytest (fast unit set, `-n auto`) and mypy; all must pass.
> Format the code and make exactly one commit for this step.

## WHERE
- `src/mcp_coder/workflow_steps/ci.py` — `_poll_for_ci_completion`
- `tests/workflow_steps/test_ci.py`

## WHAT
No signature change. With `expected_sha` given, "no run" and "run for another commit" share one counter
(the existing `other_commit_attempts`, renamed `expected_sha_attempts`), capped by `CI_EXPECTED_SHA_MAX_POLL_ATTEMPTS`.
Without `expected_sha`, behaviour is unchanged (no-run polls the full `CI_MAX_POLL_ATTEMPTS`).

## ALGORITHM
```
no_run = len(run_info) == 0
waiting_on_expected = not lookup_failed and expected_sha is not None and (no_run or is_other_commit)
if waiting_on_expected: expected_sha_attempts += 1
budget_spent = lookup_failed ? lookup cap : waiting_on_expected ? expected_sha_attempts >= CI_EXPECTED_SHA_MAX_POLL_ATTEMPTS : False
on exit: lookup_failed -> CI_API_ERROR; is_other_commit -> CI_TIMEOUT; else (no run) -> CI_NOT_CONFIGURED
```
Keep the `lookup_failed` branch first. Keep the debug "waiting_for" messages as they are.
Lookup-failed reads (which carry an empty `run`) never count against the `expected_sha` budget; they have their own cap.

## HOW
- Update the docstring of the `expected_sha` argument and the comment above `CI_EXPECTED_SHA_MAX_POLL_ATTEMPTS`
  in `workflow_steps/constants.py` to mention "no run" as well.

## Tests (write first)
- `expected_sha` given, every poll returns `{"run": {}, "jobs": []}` → returns `(None, True)` after exactly
  `CI_EXPECTED_SHA_MAX_POLL_ATTEMPTS` calls; `CI_NOT_CONFIGURED` logged.
- `expected_sha` given, mixed sequence (no run, other commit, no run, ...) → still gives up after
  `CI_EXPECTED_SHA_MAX_POLL_ATTEMPTS` calls in total (shared counter).
- `expected_sha` given, no run twice, then a completed success run for `expected_sha` → `(status, True)`.
- `expected_sha` given, sequence lookup-failed ×2 → no run × (`CI_EXPECTED_SHA_MAX_POLL_ATTEMPTS` − 1) → completed
  success run for `expected_sha` → `(status, True)`. The cap is not hit early: the two lookup-failed reads do not count
  against the `expected_sha` budget, so no `CI_NOT_CONFIGURED` log.
- No `expected_sha`, no run → still polls `CI_MAX_POLL_ATTEMPTS` (existing test; keep it passing).
- Patch `time.sleep` as the existing tests do.

## DATA
Return values unchanged.
