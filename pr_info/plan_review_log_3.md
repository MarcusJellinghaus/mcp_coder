# Plan Review Log — Issue #657 (Round 3)

## Round 3a — 2026-03-31
**Findings**:
- [critical] Step 5: `warn_orphan_folders` receives `repo_full_name` from caller but sanitizes as short name — produces wrong folder patterns
- [accept] Step 1: `TO_BE_DELETED_FILENAME` not explicitly listed in `__all__`
- [accept] Step 1: `__init__.py` re-export additions underspecified
- [accept] Step 2: Workspace file path should use `workspace_base` param, not `folder_path.parent`
- [accept] Step 2: Required param `workspace_base` placed after defaulted params — reorder needed
- [accept] Step 5: `sessions_by_repo` needs construction in `cleanup_stale_sessions`
- [accept] Step 5: `load_sessions()`/`load_to_be_deleted()` called per loop invocation — acceptable at expected scale
- [accept] All steps: Existing tests need `workspace_base` added to modified function calls — not mentioned
- [skip] Race condition on `.to_be_deleted` — scoped out in Round 2

**Decisions**: All straightforward — no user escalation needed.
**User decisions**: None required.
**Changes**:
- Step 1: Added `TO_BE_DELETED_FILENAME` to `__all__`, specified re-exports in `__init__.py`
- Step 2: Reordered `workspace_base` before optional params in both signatures, added workspace file path construction note
- Step 5: Fixed repo name extraction (`split("/")[-1]`), added `sessions_by_repo` construction, added I/O note
- Summary: Added note about updating existing tests for new `workspace_base` parameter

**Status**: Changes applied, committing next
