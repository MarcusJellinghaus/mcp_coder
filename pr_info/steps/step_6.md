# Step 6: Add Elapsed Time and Heartbeat to CI Polling Logs

## Context

See [summary.md](summary.md) for full context. This step adds elapsed time info to existing CI polling log messages and a periodic INFO-level heartbeat every ~2 minutes — using only the existing loop, no threads.

## WHERE

- **Source**: `src/mcp_coder/workflows/implement/core.py` — `_poll_for_ci_completion()` function
- **Tests**: `tests/workflows/implement/test_core.py`

## WHAT

### Updated `_poll_for_ci_completion()` (pseudocode for changes):

```python
def _poll_for_ci_completion(ci_manager, branch):
    poll_start_time = time.time()                         # NEW
    heartbeat_iteration_interval = 8  # ~2min at 15s      # NEW

    for poll_attempt in range(CI_MAX_POLL_ATTEMPTS):
        # ... existing CI status check code ...

        elapsed = time.time() - poll_start_time           # NEW
        elapsed_min, elapsed_sec = divmod(int(elapsed), 60)  # NEW

        # Existing "in progress" log — add elapsed time
        logger.debug(
            f"CI run in progress (status: {run_status}, "
            f"attempt {poll_attempt + 1}/{CI_MAX_POLL_ATTEMPTS}, "
            f"elapsed: {elapsed_min}m {elapsed_sec}s)"        # CHANGED
        )

        # Periodic heartbeat at INFO level (~every 2 min)     # NEW
        if (poll_attempt + 1) % heartbeat_iteration_interval == 0:
            logger.info(
                "CI polling heartbeat: waiting for CI completion "
                "(attempt %d/%d, elapsed: %dm %ds)",
                poll_attempt + 1, CI_MAX_POLL_ATTEMPTS,
                elapsed_min, elapsed_sec,
            )

        time.sleep(CI_POLL_INTERVAL_SECONDS)
```

Also add elapsed time to the "No CI run found yet" debug log in the same function.

## HOW

- Add `poll_start_time = time.time()` at function start
- Compute elapsed time before each log statement
- Append elapsed to existing debug log messages
- Add INFO heartbeat every 8th iteration (8 x 15s = 120s ~ 2 min)
- No new threads, no new imports, no signature changes

## TESTS

Add to `tests/workflows/implement/test_core.py`:

```python
class TestPollForCiCompletionHeartbeat:
    def test_heartbeat_logged_at_interval(self, caplog):
        """INFO heartbeat is logged every 8 iterations."""
        mock_ci_manager = MagicMock()
        in_progress = {"run": {"status": "in_progress", "run_ids": [1], "commit_sha": "abc"}, "jobs": []}
        completed = {"run": {"status": "completed", "conclusion": "success", "run_ids": [1], "commit_sha": "abc"}, "jobs": []}
        mock_ci_manager.get_latest_ci_status.side_effect = [in_progress] * 9 + [completed]

        with patch("mcp_coder.workflows.implement.core.time.sleep"):
            with caplog.at_level(logging.INFO):
                _poll_for_ci_completion(mock_ci_manager, "main")

        heartbeat_logs = [r for r in caplog.records if "CI polling heartbeat" in r.message]
        assert len(heartbeat_logs) == 1  # Fires at iteration 8

    def test_elapsed_time_in_debug_logs(self, caplog):
        """Debug logs include elapsed time."""
        mock_ci_manager = MagicMock()
        in_progress = {"run": {"status": "in_progress", "run_ids": [1], "commit_sha": "abc"}, "jobs": []}
        completed = {"run": {"status": "completed", "conclusion": "success", "run_ids": [1], "commit_sha": "abc"}, "jobs": []}
        mock_ci_manager.get_latest_ci_status.side_effect = [in_progress, completed]

        with patch("mcp_coder.workflows.implement.core.time.sleep"):
            with caplog.at_level(logging.DEBUG):
                _poll_for_ci_completion(mock_ci_manager, "main")

        debug_logs = [r for r in caplog.records if "elapsed" in r.message.lower() and "in progress" in r.message.lower()]
        assert len(debug_logs) >= 1
```

## COMMIT

`feat(core): add elapsed time and heartbeat to CI polling logs (#598)`

## LLM PROMPT

```
Implement Step 6 from pr_info/steps/step_6.md.
Context: pr_info/steps/summary.md

1. In `_poll_for_ci_completion()` in `src/mcp_coder/workflows/implement/core.py`:
   - Add `poll_start_time = time.time()` at function start
   - Add elapsed time to existing debug log messages ("CI run in progress" and "No CI run found yet")
   - Add INFO-level heartbeat log every 8th iteration ("CI polling heartbeat: ...")
2. Add tests in `tests/workflows/implement/test_core.py` for the heartbeat and elapsed time logging.

No signature changes, no threads, no new imports needed (time is already imported).
Run all code quality checks.
Commit: "feat(core): add elapsed time and heartbeat to CI polling logs (#598)"
```
