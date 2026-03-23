# Issue #547: VSCode session detection — PID check short-circuits reliable window title check

## Problem

`is_session_active()` checks PID first, which short-circuits before the window title check.
When a VSCode process (PID) is reused for a different session, the PID check returns `True`
for the old session even though no window exists for it anymore.

## Architectural / Design Changes

### Before (current logic in `is_session_active`)

```
artifacts check → PID check (short-circuits!) → window title check → cmdline check
```

PID and cmdline checks reflect **launch-time state** — they don't know which session the
process currently serves. The window title check reflects **current state** (which workspace
is actually visible).

### After (new logic)

```
artifacts check →
  IF Windows + issue_num + repo available:
    window title check (authoritative) → return result
    (log warning if PID alive but window not found)
  ELSE (non-Windows fallback):
    PID check → cmdline check
```

**Key design decision:** On Windows, when the window title check is available (requires
`HAS_WIN32GUI`, `issue_num`, and `repo`), it is the **single source of truth**. Its result
is returned directly — no fallthrough to PID or cmdline checks, which can false-positive
when a VSCode process has been reused for a different session.

When the window check is not available (non-Windows, or missing `issue_num`/`repo`), the
existing PID → cmdline fallback is preserved unchanged.

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/workflows/vscodeclaude/sessions.py` | Reorder checks in `is_session_active()`, add warning log |
| `tests/workflows/vscodeclaude/test_sessions.py` | Update 1 existing test, add 3 new tests |

No new files, modules, or classes are created.

## Implementation Steps

| Step | Description |
|------|-------------|
| [Step 1](step_1.md) | Add tests for new `is_session_active()` behavior |
| [Step 2](step_2.md) | Implement the fix in `is_session_active()` and update existing test |
