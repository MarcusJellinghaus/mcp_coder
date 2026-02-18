# Summary: Improve Stale Session Warning Messages with Reason (#452)

## Overview

When `cleanup_stale_sessions` encounters a non-empty "No Git" or "Error" folder it skips
with a generic warning that gives no indication of *why* the session is stale. This change
threads a human-readable `reason` string through the cleanup pipeline so the warning becomes
actionable (e.g. `[WARN] Skipping (no git, closed): /path/to/folder`).

---

## Architectural / Design Changes

### Return-type change to `get_stale_sessions`

| Before | After |
|--------|-------|
| `list[tuple[VSCodeClaudeSession, str]]` | `list[tuple[VSCodeClaudeSession, str, str]]` |
| `(session, git_status)` | `(session, git_status, reason)` |

The third element is a plain `str` — no new types or data classes are introduced.

### Short-circuit → explicit flag

The existing condition:

```python
if (
    is_closed
    or is_blocked
    or is_ineligible
    or is_session_stale(session, cached_issues=cached_for_stale_check)
):
```

is replaced with an explicit `is_stale` bool so the reason-building logic can inspect
each flag independently without repeating the call to `is_session_stale`.

### Reason-building logic (inside `get_stale_sessions`)

```
reasons = []
if is_closed:   reasons.append("closed")
if is_blocked:  reasons.append("blocked")
if is_ineligible: reasons.append("bot status")
if is_stale:
    if cache available and status_labels:
        reasons.append("stale → {status_labels[0]}")
    else:
        reasons.append("stale")
reason = ", ".join(reasons)   # e.g. "closed, blocked"
```

### Warning message change (inside `cleanup_stale_sessions`)

Only the **non-empty No Git / Error** branch changes:

```python
# Before
logger.warning("Skipping folder (%s): %s", git_status.lower(), folder)
print(f"[WARN] Skipping ({git_status.lower()}): {folder}")

# After
logger.warning("Skipping folder (%s, %s): %s", git_status.lower(), reason, folder)
print(f"[WARN] Skipping ({git_status.lower()}, {reason}): {folder}")
```

Dirty folder warnings are **not changed**.

---

## Reason Values

| Reason | Condition |
|--------|-----------|
| `"closed"` | `issue["state"] == "closed"` |
| `"blocked"` | issue has a blocked/wait label |
| `"bot status"` | current status is ineligible (bot-pickup / bot-busy / pr-created) |
| `"stale → status-XX:name"` | status changed, cache available |
| `"stale"` | status changed, no cache |

Multiple conditions combine: `"closed, blocked"`, `"closed, blocked, bot status"`, etc.

---

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/workflows/vscodeclaude/cleanup.py` | Return 3-tuple; build reason; update warning messages |
| `tests/workflows/vscodeclaude/test_cleanup.py` | Update 2-tuple unpacks; add reason tests |

No new files, no new modules, no changes to `__init__.py`.
