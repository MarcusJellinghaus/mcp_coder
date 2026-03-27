# Plan Review Decisions

## 1. Reorder and restructure steps

Old Step 6 (safety net + SIGTERM + existing failures) was too large. Split into:
- **Step 3**: Mechanical change — update existing `WorkflowFailure(...)` constructions with `build_url` and `elapsed_time`
- **Step 4**: Logic change — add `try/finally` safety net + SIGTERM handler

Old Steps 3 and 4 (heartbeat in `execute_subprocess` + pass from `ask_claude_code_cli`) merged into **Step 5**, since old Step 4 was trivially small (one-line call change + one constant).

Old Step 5 (CI polling) becomes **Step 6**.

## 2. Fix SIGTERM handler approach

The SIGTERM handler must NOT do I/O directly (calling `_handle_workflow_failure()` inside a signal handler risks re-entrancy and deadlocks). Instead:
- SIGTERM handler sets `sigterm_received = True` and calls `sys.exit(1)`
- The `finally` block (which runs on `sys.exit`) checks `sigterm_received` and calls `_handle_workflow_failure()` from normal context

## 3. Fix heartbeat tests

- **`test_no_heartbeat_by_default`**: Test behavior not implementation — use `caplog` to verify no heartbeat log messages appear, instead of mocking `threading` module and checking `Thread` not called.
- **`test_run_heartbeat_logs_periodically`**: Remove real timing dependency — mock `Event.wait` to return `False` once then `True`, instead of using `time.sleep` with real delays.
- **`test_passes_heartbeat_params_to_execute_subprocess`**: Simplify assertion to `assert mock_exec.call_args.kwargs["heartbeat_interval_seconds"] == 120` — no `or` fallback needed.
