# Plan Review Log — Issue #657 (Round 2)

## Round 2 — 2026-03-31
**Findings**:
- [critical] Step 2: Second `delete_session_folder` call site (empty-dir) not addressed — needs explicit `was_clean=False`
- [critical] Step 4: Soft-deleted session exclusion from `session_keys` correct but undocumented
- [accept] Step 5: `warn_orphan_folders` has no caller (YAGNI) — user decided to call from cleanup
- [accept] Step 2: Workspace deletion timing change applies to all paths, not just soft-delete
- [accept] Step 5: Multi-match error semantics change — user confirmed always applies
- [accept] Step 2: Missing end-to-end retry test
- [accept] Step 2: `remove_session` call clarity on soft-delete vs success path
- [accept] Step 5: `warn_orphan_folders` missing `sanitize_folder_name` import
- [skip] Concurrent access concern (out of scope)
- [skip] `__init__.py` re-export (minor)

**User decisions**:
- Q1 (orphan caller): A — call `warn_orphan_folders` from `cleanup_stale_sessions`
- Q2 (multi-match error): Always applies regardless of `workspace_base`

**Changes**:
- Step 2: Documented second call site (was_clean=False), workspace deletion applies to all paths, remove_session clarity, added e2e test
- Step 4: Added session_keys exclusion note
- Step 5: Added caller in cleanup.py, fixed sanitize import, confirmed multi-match always applies, updated backward-compat test

**Status**: All changes applied and verified

**Late addition**: Made `workspace_base` required (`str`) everywhere — removed `| None` optionality and backward-compat tests. User confirmed it's always passed in production; `None` default was unnecessary.

## Final Status

Round 2 complete. Plan refined with 2 critical fixes, 6 accepted improvements, 2 skipped. `workspace_base` made required. Plan is ready for implementation.
