# Issue #712: Add generic faulthandler crash instrumentation utility

## Summary

Add a lightweight crash diagnostics utility so that long-running CLI commands (`implement`, `create_plan`, `create_pr`) capture native-level tracebacks on crash. This supports diagnosing issue #710 (silent process death) without adding heavy telemetry.

## Architectural / Design Changes

### New module
- **`src/mcp_coder/utils/crash_logging.py`** — self-contained utility with no internal dependencies beyond stdlib. Uses module-level `_state` dict to hold the open file handle for process lifetime (faulthandler requires a live FD at crash time). Exposes `enable_crash_logging()` (public) and `_reset_for_testing()` (test helper).

### Modified modules
- **`src/mcp_coder/cli/main.py`** — adds stderr-based `faulthandler.enable()` at the very top, before heavy imports. This is a zero-cost safety net for all CLI commands.
- **`src/mcp_coder/cli/commands/implement.py`** — calls `enable_crash_logging()` after `log_command_startup()`.
- **`src/mcp_coder/cli/commands/create_plan.py`** — same.
- **`src/mcp_coder/cli/commands/create_pr.py`** — same.

### Design decisions
- **Two layers of crash logging**: (1) stderr safety net in `main.py` (catches startup crashes, no file I/O), (2) per-command file-based logging (richer, writes to `{project_dir}/logs/faulthandler/`).
- **Module-level `_state` dict** instead of multiple globals — avoids `global` statements and simplifies `_reset_for_testing()`.
- **Never raises** — all errors swallowed and logged at WARNING.
- **Idempotent** — second call returns existing path.
- **Timestamp format** reuses the pattern from `session_storage.py:62` for consistency across project artifacts.

## Files Created

| File | Purpose |
|------|---------|
| `src/mcp_coder/utils/crash_logging.py` | `enable_crash_logging()` + `_reset_for_testing()` |
| `tests/utils/test_crash_logging.py` | Unit tests + subprocess integration test |

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/cli/main.py` | Add stderr faulthandler safety net at top |
| `src/mcp_coder/cli/commands/implement.py` | Call `enable_crash_logging()` after startup |
| `src/mcp_coder/cli/commands/create_plan.py` | Call `enable_crash_logging()` after startup |
| `src/mcp_coder/cli/commands/create_pr.py` | Call `enable_crash_logging()` after startup |

## Implementation Steps

| Step | Description | Commit |
|------|-------------|--------|
| 1 | Create `crash_logging.py` with tests | `feat: add crash_logging utility with enable_crash_logging and tests` |
| 2 | Add stderr safety net to `main.py` with test | `feat: add faulthandler stderr safety net to CLI entry point` |
| 3 | Wire `enable_crash_logging` into implement, create_plan, create_pr | `feat: wire enable_crash_logging into long-running CLI commands` |
| 4 | Add subprocess integration test for real crash capture | `test: add subprocess integration test for faulthandler crash capture` |
