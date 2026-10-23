# Step 1 — CI polling: read `lookup_failed` from the top level of `CIStatusData`

## LLM prompt
> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_1.md` exactly.
> Write the tests first, then change the code. Run pylint, pytest (fast unit set, `-n auto`) and mypy; all must pass.
> Format the code and make exactly one commit for this step.

## WHERE
- `src/mcp_coder/workflow_steps/ci.py` — `_poll_for_ci_completion`
- `tests/workflow_steps/test_ci.py` — the `lookup_failed` test class (~line 318)

## WHAT
No signature changes. In `_poll_for_ci_completion`:
```python
run_info = ci_status.get("run", {})
lookup_failed = bool(ci_status.get("lookup_failed"))   # was: run_info.get("lookup_failed")
```

## HOW
- `CIStatusData` (mcp-workspace) defines `lookup_failed: NotRequired[bool]` on the top level, next to `run` and `jobs`.
- Today the flag is never seen, so a lookup failure looks like "no run yet".

## Tests (write first)
- Change `_lookup_failed_run()` to return `{"run": {}, "jobs": [], "lookup_failed": True}`.
- Existing tests in the class must pass with that mock (retry then success, exhaust after
  `CI_LOOKUP_FAILED_MAX_POLL_ATTEMPTS`, counter reset, absent key behaves as before).
- Rewrite `test_lookup_failed_checked_before_empty_run_branch`: pass `expected_sha="abc..."`, let every poll return the
  lookup-failed mock, and assert the poll gives up after `CI_LOOKUP_FAILED_MAX_POLL_ATTEMPTS` (3) attempts, not
  `CI_EXPECTED_SHA_MAX_POLL_ATTEMPTS` (8). Assert the `CI_API_ERROR` log line.
  (The test only becomes discriminating after step 2, but asserting 3 attempts is correct now.)
- Add one test: a mock with `lookup_failed` only inside `run` (old shape) and nothing at the top level is **not**
  treated as a lookup failure (an empty-ish run → normal "no run" handling).

## DATA
Return value unchanged: `(None, True)` on lookup-failure exhaustion.
