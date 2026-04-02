# Step 4: CI Wait Progress and check_branch_status Print Migration

## LLM Prompt
> Read `pr_info/steps/summary.md` for full context. Implement Step 4: Replace the print-based dot progress in check_branch_status.py with periodic OUTPUT log messages, and migrate all remaining print() calls in the file to logging. Run all code quality checks after changes.

## WHERE
- `src/mcp_coder/cli/commands/check_branch_status.py` — main changes
- `tests/cli/commands/test_check_branch_status_ci_waiting.py` — update tests for new logging pattern

## WHAT

### 4a. Import OUTPUT constant

```python
from ...utils.log_utils import OUTPUT
```

### 4b. Remove `_show_progress()` helper

Delete entirely:
```python
# DELETE THIS:
def _show_progress(show: bool) -> None:
    """Print a progress dot if show is True."""
    if not show:
        return
    print(".", end="", flush=True)
```

### 4c. Update `_wait_for_ci_completion()`

Replace the dot-based progress with periodic OUTPUT-level log messages.

**Key changes:**
1. Remove `show_progress` variable and all `_show_progress()` calls
2. Remove `print()` calls for the initial message and newline-after-dots
3. Add `logger.log(OUTPUT, ...)` at start and every ~60s (every 4th iteration)
4. Track elapsed time for the periodic message

```python
def _wait_for_ci_completion(
    ci_manager: CIResultsManager,
    branch: str,
    timeout_seconds: int,
    llm_mode: bool,
) -> Tuple[Optional[CIStatusData], bool]:
    if timeout_seconds <= 0:
        return None, True

    poll_interval = 15  # seconds
    max_attempts = timeout_seconds // poll_interval
    log_every_n = 4  # Log every 4 polls = ~60 seconds

    if not llm_mode:
        logger.log(OUTPUT, "Waiting for CI completion (timeout: %ds)...", timeout_seconds)

    ci_status: Optional[CIStatusData] = None
    for attempt in range(max_attempts):
        try:
            ci_status = ci_manager.get_latest_ci_status(branch)
        except Exception as e:
            logger.error("CI API error during polling: %s", e)
            raise RuntimeError(f"API error during CI polling: {e}") from e

        run_info = ci_status.get("run", {})

        # No CI run found yet
        if len(run_info) == 0:
            if attempt == max_attempts - 1:
                logger.info("No CI run found within timeout")
                return None, True
            # Periodic progress (every ~60s)
            if not llm_mode and attempt > 0 and attempt % log_every_n == 0:
                elapsed = (attempt + 1) * poll_interval
                logger.log(OUTPUT, "Still waiting for CI... (%ds elapsed)", elapsed)
            time.sleep(poll_interval)
            continue

        # Check if CI completed
        if run_info.get("status") == "completed":
            conclusion = run_info.get("conclusion")
            if conclusion == "success":
                logger.info("CI passed")
                return ci_status, True
            else:
                logger.info("CI completed with conclusion: %s", conclusion)
                return ci_status, False

        # CI still running — periodic progress
        if not llm_mode and attempt > 0 and attempt % log_every_n == 0:
            elapsed = (attempt + 1) * poll_interval
            logger.log(OUTPUT, "Still waiting for CI... (%ds elapsed)", elapsed)
        time.sleep(poll_interval)

    # Timeout reached
    logger.info("CI polling timeout reached")
    return ci_status, False
```

### 4d. Update `execute_check_branch_status()` PR waiting prints

The PR-waiting section also has `print()` calls. Migrate status messages:

```python
# BEFORE
print(f"Waiting for PR creation on branch '{current_branch}' (timeout: {args.pr_timeout}s)...")
print(f"PR #{pr_number} found ({pr_url}). Proceeding with branch-status check.")
print(f"No PR found for branch '{current_branch}' within timeout ({args.pr_timeout}s).")

# AFTER
logger.log(OUTPUT, "Waiting for PR creation on branch '%s' (timeout: %ds)...", current_branch, args.pr_timeout)
logger.log(OUTPUT, "PR #%s found (%s). Proceeding with branch-status check.", pr_number, pr_url)
logger.log(OUTPUT, "No PR found for branch '%s' within timeout (%ds).", current_branch, args.pr_timeout)
```

Also migrate the remote tracking branch error and multi-PR warning:
```python
# BEFORE
print(f"Branch '{current_branch}' has no remote tracking branch. Push first.")
print(f"Warning: Multiple PRs found for branch '{current_branch}'. Using PR #{pr_number}.")

# AFTER
logger.log(OUTPUT, "Branch '%s' has no remote tracking branch. Push first.", current_branch)
logger.warning("Multiple PRs found for branch '%s'. Using PR #%s.", current_branch, pr_number)
```

Also migrate the outer exception handler error print:
```python
# BEFORE
print(f"Error collecting branch status: {e}", file=sys.stderr)

# AFTER
logger.error("Error collecting branch status: %s", e)
```

**Keep as print():** The `print(output)` for the branch status report (`format_for_human()` / `format_for_llm()`) — this is data output.

Also migrate: `print("CI pending. Use --ci-timeout to wait for completion.")` → `logger.log(OUTPUT, "CI pending. Use --ci-timeout to wait for completion.")`.

### 4e. Update tests

Tests in `test_check_branch_status_ci_waiting.py` likely mock `print` or check for dot output. Update them to check for `logger.log` calls instead, or use `caplog` to verify the periodic messages.

## DATA
- No new data structures
- `poll_interval`: 15 seconds (unchanged)
- `log_every_n`: 4 (new constant, logs every ~60s)

## ALGORITHM
```
1. Log "Waiting for CI..." at start (if not llm_mode)
2. Poll CI status every 15 seconds
3. Every 4th poll (~60s): log "Still waiting... (Ns elapsed)"
4. On completion: log result at INFO level
5. On timeout: log at INFO level
```

## Commit Message
```
refactor(ci-wait): replace dot progress with periodic log messages

- Remove _show_progress() helper
- Log periodic OUTPUT-level messages every ~60s
- Keep 15s poll interval unchanged
- Migrate PR-wait print() calls to logging
```
