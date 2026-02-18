# Summary: Fix Status Table Action for `status-10:pr-created` Issues

## Issue Reference
Issue #453 — Status table incorrectly shows `-> Create and start` for `status-10:pr-created` issues.

---

## Problem

`display_status_table()` in `status.py` displays eligible issues not yet in sessions.
For every such issue, it currently assigns one of two actions:

```
-> Needs branch      (if status requires branch but none is linked)
-> Create and start  (all other cases)
```

`status-10:pr-created` passes the eligibility filter (it is `category: human_action`,
assigned to the user) but has `initial_command: null` in `labels.json`.
This means `is_status_eligible_for_session()` returns `False` for it — no session will
ever be created — but the table misleadingly shows `-> Create and start`.

---

## Fix

A single **display-only** change inside the eligible-issues loop of `display_status_table()`.
Insert one `elif` branch that calls `is_status_eligible_for_session(status)` (already
imported) before falling through to `-> Create and start`:

```python
if needs_branch:
    action = "-> Needs branch"
elif not is_status_eligible_for_session(status):
    action = "(awaiting merge)"
else:
    action = "-> Create and start"
```

---

## Architectural / Design Notes

- **No architectural change.** This is a pure display-logic fix.
- **No new imports.** `is_status_eligible_for_session` is already imported at the top of `status.py`.
- **No filter change.** `_filter_eligible_vscodeclaude_issues` correctly includes `status-10` issues
  in the eligible list (they are valid `human_action` issues assigned to the user) — hiding them
  would remove useful status information from the table.
- **Generality.** Using `is_status_eligible_for_session()` rather than a hardcoded string comparison
  means any future status with `initial_command: null` will automatically display `(awaiting merge)`
  without further changes.

---

## Files Modified

| File | Action |
|------|--------|
| `src/mcp_coder/workflows/vscodeclaude/status.py` | Modify — add `elif` branch in eligible-issues loop |
| `tests/workflows/vscodeclaude/test_status_display.py` | Modify — add one test method to `TestStatusDisplay` |

## Files Created

None.

---

## Steps

| Step | Description |
|------|-------------|
| Step 1 | Add test and implement the `elif` fix in `display_status_table()` together |
