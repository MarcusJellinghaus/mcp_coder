# Decisions Log

Decisions made during plan review discussion.

---

## Decision 1: Error Handling Strategy

**Question:** Should we define a custom `CacheError` exception for `get_all_cached_issues()`?

**Decision:** No change - keep existing behavior. The function can raise standard exceptions (`ValueError`, `KeyError`, `TypeError`), and the thin wrapper `get_cached_eligible_issues()` in coordinator catches them and falls back to `get_eligible_issues()`.

**Rationale:** User specified "the behaviour should not change, I just want to move code."

---

## Decision 2: `DUPLICATE_PROTECTION_SECONDS` Constant Location

**Question:** The constant currently lives in `cli/commands/coordinator/workflow_constants.py`. The new `issue_cache.py` in `utils/github_operations/` needs it, but importing from `workflow_constants.py` would violate layered architecture.

**Decision:** Move the constant to `src/mcp_coder/constants.py` (shared location at package root). Both `issue_cache.py` and `workflow_constants.py` will import from there.

---

## Decision 3: Re-exporting Private Functions

**Question:** Should coordinator's `__init__.py` continue re-exporting private functions (`_get_cache_file_path`, `_load_cache_file`, etc.) for backwards compatibility?

**Decision:** Stop exporting private functions from coordinator - only export public API (`CacheData`, `get_cached_eligible_issues`, `_update_issue_labels_in_cache`).

**Rationale:** Investigation showed no external source code imports these private functions from coordinator. Tests will update patch paths to `issue_cache` anyway.

---

## Decision 4: Grep for Other Patch Paths

**Question:** Should we add a verification step to grep for other test files patching coordinator cache functions?

**Decision:** Not needed - the test file being moved is the only one testing cache functionality.
