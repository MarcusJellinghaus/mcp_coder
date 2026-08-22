# Step 3 — Blocked detection in `process_single_task`

The core fix. Everything else in this issue supports this step.

## WHERE

| File | Change |
|------|--------|
| `src/mcp_coder/workflows/implement/task_processing.py` | start-of-task cleanup, LLM-block restructure, blocked branch, docstrings |
| `tests/workflows/implement/test_task_processing.py` | new tests |

`process_task_with_retry` needs **no** logic change — it already returns immediately for
any reason other than `"no_changes"`, so `blocked` never retries. Pin that with a test.

## WHAT

No new functions. Three edits inside `process_single_task`:

1. **Start-of-task cleanup** — beside the existing `_cleanup_commit_message_file` call:

```python
_cleanup_commit_message_file(project_dir)
read_and_clear_blocked(project_dir)   # drop a stale marker from a previous failed run
```

2. **LLM-block restructure** — the three early exits become assignments to one local, and
   the marker is read in `finally`.

3. **Branch once, before the Step 6 files-changed check.**

Update the `process_single_task` docstring's reason list to include `'blocked'`.

## HOW

Restructured Step 5 block (existing code otherwise untouched):

```python
llm_error: str | None = None
try:
    ...build full_prompt, call prompt_llm...
    response = llm_response["text"]
    if not response or not response.strip():
        logger.error("LLM returned empty response")
        logger.debug(f"Response was: {repr(response)}")
        llm_error = "error"
    else:
        logger.info("LLM response received successfully")
        try:
            store_session(...)
        except Exception as store_err:
            logger.warning("Failed to store implement session: %s", store_err)
except (LLMTimeoutError, McpServersUnavailableError) as e:
    llm_error = llm_failure_reason(e) or "error"
    logger.error("LLM call failed (%s) for task: %s", llm_error, next_task)
except Exception as e:
    logger.error(f"Error calling LLM: {e}")
    llm_error = "error"
finally:
    blocked = read_and_clear_blocked(project_dir)
```

Note the `else:` around `store_session` — the empty-response guard no longer returns, so
the session-storage block must not run in that case.

Then, immediately after (still before Step 6):

```python
if llm_error in ("timeout", "mcp_unavailable"):
    return TaskOutcome(False, llm_error, blocked or "")
if blocked:
    logger.error("Task blocked: %s", blocked)
    return TaskOutcome(False, "blocked", blocked)
if llm_error:
    return TaskOutcome(False, llm_error)
```

## ALGORITHM

```
cleanup stale marker at task start
run the LLM call; record any failure in llm_error instead of returning
finally: blocked = read_and_clear_blocked(project_dir)   # cannot be bypassed
typed LLM failure wins the label -> return it, carrying the marker text as detail
else marker present         -> return TaskOutcome(False, "blocked", text)
else untyped error          -> return it
else fall through to the Step 6 files-changed check
```

## DATA

| Situation | Returned |
|---|---|
| marker only | `TaskOutcome(False, "blocked", "<text>")` |
| marker + changed files | `TaskOutcome(False, "blocked", "<text>")` — **never** success |
| marker + `LLMTimeoutError` | `TaskOutcome(False, "timeout", "<text>")` |
| marker + `McpServersUnavailableError` | `TaskOutcome(False, "mcp_unavailable", "<text>")` |
| marker + empty response | `TaskOutcome(False, "blocked", "<text>")` |
| empty marker | `TaskOutcome(False, "blocked", BLOCKED_REASON_FALLBACK)` |
| no marker | unchanged behaviour |

In every case above the marker file is deleted.

## Why this ordering (do not rearrange)

- **Before Step 6.** `pr_info/` is in no `.gitignore`, `get_full_status` includes
  `untracked`, and Step 9 `commit_changes` stages everything. A marker written alone would
  otherwise read as "files changed → success" and get committed — the inverted path, worse
  than the bug being fixed.
- **Not in `process_task_with_retry`.** By the time the wrapper sees the outcome, Step 9
  has already committed the marker.
- **Empty marker must not fall through to `no_changes`** — the marker is itself an
  untracked change, so falling through restores the same inverted path.
- **`finally`, not four call sites.** A marker left on disk poisons the next run:
  `check_git_clean` refuses it, and `prepare_task_tracker` hard-fails with
  `task_tracker_prep_failed` because it requires exactly one changed file equal to
  `TASK_TRACKER.md`.
- **Typed LLM failure wins the label** — it drives what the operator does next, and an
  unavailable MCP server is more actionable than the agent's downstream complaint about it.
  The text is preserved as `detail` either way.

## TESTS (write first)

New class `TestProcessSingleTaskBlocked` in
`tests/workflows/implement/test_task_processing.py`. Model the mock setup on the existing
`TestProcessSingleTask` tests; use `tmp_path` as `project_dir` so the real marker file can
be written, and create `tmp_path / "pr_info"`.

1. `test_blocked_wins_over_changed_files` — marker present **and** `get_full_status`
   returns `{"staged": ["f.py"], ...}` → `outcome.reason == "blocked"`,
   `outcome.success is False`, `commit_changes` **not** called, marker deleted.
   *This is the most important test in the change.*
2. `test_empty_marker_is_blocked_not_no_changes` — whitespace-only marker, empty git status
   → `reason == "blocked"`, `detail == BLOCKED_REASON_FALLBACK`.
3. `test_marker_plus_timeout_keeps_timeout_label` — `prompt_llm` raises `LLMTimeoutError`,
   marker present → `reason == "timeout"`, `detail` contains the marker text, marker
   deleted from disk.
4. `test_marker_plus_mcp_unavailable_keeps_mcp_label` — same shape with
   `McpServersUnavailableError` → `reason == "mcp_unavailable"`, detail carried.
5. `test_stale_marker_removed_at_task_start` — marker present, `get_next_task` returns
   `None` → `reason == "no_tasks"` and the marker is gone.
6. `test_no_marker_still_reports_no_changes` — regression guard: empty git status, no
   marker → `reason == "no_changes"` (unchanged behaviour).
7. `test_blocked_does_not_retry` — patch
   `task_processing.process_single_task` to return `TaskOutcome(False, "blocked", "why")`;
   `process_task_with_retry` returns it with `call_count == 1`.

## COMMIT

`Detect pr_info/.blocked.txt and return a blocked outcome`

## LLM PROMPT

```
Read pr_info/steps/summary.md (sections 3 and 4, and the "Invariants the tests must pin"
list) and pr_info/steps/step_3.md, then implement Step 3 only.

This is the core fix: process_single_task learns to recognise pr_info/.blocked.txt and
return TaskOutcome(False, "blocked", <text>). Do NOT touch core.py, labels.json,
RETRY_REMINDER or prompts.md — those are Steps 4, 5 and 6. After this step the "blocked"
reason reaches core.py and falls through its reason chain to the generic path; that is
expected and is fixed in Step 5.

Work test-first: write TestProcessSingleTaskBlocked as described, watch it fail, then
implement.

Three things are load-bearing and must not be rearranged:
1. The marker check runs BEFORE the Step 6 files-changed check. If it runs after, or in
   process_task_with_retry, a lone marker file reads as "files changed -> success" and
   gets committed — the exact inversion this issue exists to prevent.
2. An empty or whitespace-only marker returns "blocked", never "no_changes".
3. The marker is read in a `finally` so none of the three early exits (empty-response
   guard, the two typed-exception handlers) can leave it on disk.

Watch for the one non-obvious consequence of the restructure: the empty-response guard no
longer returns, so the store_session block must move into an `else:` branch.

Use MCP tools for all file operations. When done, run all three checks and fix everything
they report:
  mcp__tools-py__run_pylint_check
  mcp__tools-py__run_mypy_check
  mcp__tools-py__run_pytest_check with
    extra_args=["-n","auto","-m","not git_integration and not claude_cli_integration and
    not claude_api_integration and not formatter_integration and not github_integration
    and not langchain_integration"]

Then run ./tools/format_all.sh and make exactly one commit.
```
