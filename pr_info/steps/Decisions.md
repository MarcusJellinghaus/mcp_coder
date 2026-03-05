# Decisions Log — Issue #491

Decisions made during plan review discussion.

---

## D1: `provider` param in `log_conversation_artifacts()`

**Decision: Omit `provider`.**

`log_conversation_artifacts()` logs a minimal set of params (model, working_directory,
branch_name, step_name, prompt_length). The `provider` field present in `log_conversation()`
is intentionally excluded — `provider` is always `"claude"` in this codebase and adds
little analytical value for resumed runs.

---

## D2: Two-run edge case in Step 4's else-path

**Decision: Accept the two-run behaviour; document it with a `logger.debug()` message.**

In the else-path of `_log_to_mlflow()` (when `session_id` is None or not in the LRU
map), a fresh MLflow run is started and `log_conversation()` is called. This creates a
second run whose metrics duplicate those already logged by `log_llm_response()` in the
(now closed) previous run.

This is acceptable — the edge case is rare (Claude omitting session_id, or LRU
eviction after >100 concurrent sessions). A `logger.debug()` message documents the
behaviour at the call site.

---

## D3: LRU eviction test approach (Test 5 in step_1.md)

**Decision: Use `end_run()` to trigger eviction (Approach Y).**

Pre-fill `_session_run_map` with 100 entries, then call
`end_run("FINISHED", session_id="sid-100")` to trigger the real eviction code.

Rationale: tests the actual `end_run()` eviction logic rather than reimplementing
the eviction in the test. Catches bugs in `end_run()` itself; direct map manipulation
would not.

---

## D4: Explain `start_run()` in Step 4's else-path LLM prompt

**Decision: Add an explanatory comment to the step_4.md LLM prompt.**

The comment clarifies that `start_run()` is required in both branches of
`_log_to_mlflow()` because `log_llm_response()` (Step 2) always closes the run
before `_log_to_mlflow()` is called. Without this context, an implementing LLM might
find the `start_run()` call in the else-path surprising or redundant.
