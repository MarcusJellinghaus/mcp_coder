# Plan Review Log — Issue #657

## Round 1 — 2026-03-31
**Findings**:
- [accept] Step 1: `Path` import note incorrect — not already imported in helpers.py
- [critical] Step 2: Only one of two `cleanup_stale_sessions` call sites updated with `workspace_base`
- [critical] Step 2: Workspace file deletion timing unclear — should happen before folder deletion
- [accept] Step 2: Missing test for workspace file deletion failure
- [accept] Step 3: Missing test for sanitized repo name + folder collision
- [accept] Step 4: Too large (5 source + 2 test files) — should be split
- [critical] Step 4: Folder identification requirement #5 needs disk scanning for orphan folders, not just JSON lookup
- [skip] Q1: Empty/error folder soft-delete — user says keep was_clean only, these folders likely come from deletion process

**User decisions**:
- Q1 (empty folder soft-delete): B — only clean-git folders get soft-deleted
- Q2 (folder identification): Disk scan for orphan folders not in sessions.json and not in .to_be_deleted, log warning
- Q3 (workspace file deletion timing): B — always delete before folder deletion attempt

**Changes**:
- Step 1: Fixed `Path` import note
- Step 2: Both call sites get `workspace_base`; `.code-workspace` deletion moved before folder deletion; added workspace file failure test
- Step 3: Added sanitized repo name collision test
- Step 4: Split into Step 4 (status filtering) + Step 5 (session lookup + orphan detection)
- Step 5: New file with `warn_orphan_folders()` helper, disk scanning logic, 8 tests
- Summary + TASK_TRACKER updated to 5 steps

**Status**: All changes applied and verified

## Final Status

Round 1 complete. Plan updated from 4 steps to 5 steps. All findings addressed (3 critical fixes, 4 accepted improvements, 1 skipped). Plan is ready for implementation.
