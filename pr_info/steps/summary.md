# Issue #598: Workflow Failure Safety Net, Jenkins URL, and Heartbeat Logging

## Problem

The implement workflow can silently exit without setting a failure label, posting a GitHub comment, or logging any error. This leaves issues stuck at `status-06:implementing` permanently. Two production Jenkins runs exhibited this: one during an LLM call, one during CI polling — both stopped silently with no output.

## Root Cause

`_handle_workflow_failure()` only fires on explicitly caught errors inside `run_implement_workflow()`. There is no safety net for:
- Unexpected Python exceptions in uncovered code paths
- SIGTERM from Jenkins (job stopped/aborted)
- Any crash that bypasses the existing `if reason == "error"` branches

## Solution Overview

### 1. `try/finally` Safety Net + SIGTERM Handler (`core.py`)

Wrap `run_implement_workflow()` body in `try/finally`. A `reached_terminal_state` boolean tracks whether the workflow completed normally (success or already-handled failure). If `finally` runs and `reached_terminal_state` is False, call `_handle_workflow_failure()` with `FailureCategory.GENERAL`.

Register a SIGTERM handler at workflow start that triggers failure handling before exit. Restore the previous handler in `finally`.

### 2. Jenkins URL + Elapsed Time in Failure Comments (`constants.py`, `core.py`)

Add `build_url: Optional[str]` and `elapsed_time: Optional[float]` to `WorkflowFailure`. Populate from `BUILD_URL` env var and `time.time() - start_time`. Update `_format_failure_comment()` to include both when present. All `WorkflowFailure` constructions updated to include these fields.

### 3. Heartbeat Logging During Long Operations (`subprocess_runner.py`, `claude_code_cli.py`, `core.py`)

- **LLM subprocess calls**: Add optional heartbeat support to `execute_subprocess()` — a daemon thread using `threading.Event.wait()` loop that logs periodically. `ask_claude_code_cli()` opts in with 2-minute interval.
- **CI polling**: Add elapsed time to existing per-iteration log messages and emit a louder INFO heartbeat every ~2 minutes (every 8th iteration at 15s intervals). No threads needed — just arithmetic on the existing loop.

## Architecture / Design Changes

| Aspect | Before | After |
|--------|--------|-------|
| Unexpected exit handling | None — issue stuck forever | `try/finally` + SIGTERM handler calls `_handle_workflow_failure()` |
| `WorkflowFailure` dataclass | 5 fields (category, stage, message, tasks_completed, tasks_total) | 7 fields (+`build_url`, +`elapsed_time`, both optional) |
| `_format_failure_comment()` | Shows category, stage, error, progress, diff | Also shows elapsed time and Jenkins build URL when available |
| `execute_subprocess()` | No heartbeat | Optional heartbeat via daemon thread (`heartbeat_interval_seconds`, `heartbeat_message` params) |
| `ask_claude_code_cli()` | No heartbeat | Passes `heartbeat_interval_seconds=120` to `execute_subprocess()` |
| CI polling logs | Basic debug logs per iteration | Elapsed time on every iteration + INFO heartbeat every ~2 min |
| Signal handling | None | SIGTERM handler registered/restored around workflow |

## Files Modified

| File | Change Type |
|------|-------------|
| `src/mcp_coder/workflows/implement/constants.py` | Add `build_url` and `elapsed_time` fields to `WorkflowFailure` |
| `src/mcp_coder/utils/subprocess_runner.py` | Add optional heartbeat parameters to `execute_subprocess()` |
| `src/mcp_coder/llm/providers/claude/claude_code_cli.py` | Pass heartbeat params to `execute_subprocess()` |
| `src/mcp_coder/workflows/implement/core.py` | Safety net, SIGTERM handler, updated failure comment format, CI polling heartbeat |
| `tests/workflows/implement/test_constants.py` | Tests for new `WorkflowFailure` fields |
| `tests/utils/test_subprocess_runner.py` | Tests for heartbeat functionality |
| `tests/llm/providers/claude/test_claude_code_cli.py` | Tests for heartbeat passthrough |
| `tests/workflows/implement/test_core.py` | Tests for safety net, SIGTERM handler, failure comment format, CI heartbeat |

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Safety net | `try/finally` + `reached_terminal_state` flag | Standard Python pattern, covers all exit paths |
| SIGTERM handler | `signal.signal()` with restore in `finally` | Covers Jenkins stop signals, no side effects |
| Heartbeat thread | `threading.Event.wait()` daemon thread | Simpler than chained Timers, auto-cleanup on exit |
| CI polling heartbeat | Counter arithmetic on existing loop | No threads needed — loop already runs every 15s |
| Jenkins URL | `WorkflowFailure.build_url` field from env var | Keeps `_format_failure_comment()` pure (no env reads) |
| CLI layer | No changes | Clean separation — workflow layer owns the safety net |
