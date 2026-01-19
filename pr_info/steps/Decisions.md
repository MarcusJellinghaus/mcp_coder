# Decisions Log

## Discussion Date: 2026-01-19

### Decision 1: Cleanup Function Placement

**Question:** Where should `_cleanup_commit_message_file(project_dir)` be called in `process_single_task()`?

**Decision:** At the very start of the function, before `env_vars = prepare_llm_environment(project_dir)`.

**Rationale:** Clearer as a "reset state" operation - clean slate before any work begins.

---

### Decision 2: Invalid File Content Handling

**Question:** How should we handle potentially malformed content in the commit message file (e.g., if LLM writes explanatory text instead of just a commit message)?

**Decision:** Trust the LLM - use `parse_llm_commit_response()` as-is without additional validation.

**Rationale:** Simpler implementation (KISS). The function extracts the first non-empty line as the summary, which handles most cases.

---

### Decision 3: Test Coverage for File Deletion Timing

**Question:** Should we add a specific test that verifies the file is deleted before `git add` (by checking mock call order)?

**Decision:** No extra test needed - current test coverage is sufficient (verifying file is gone after call completes).

**Rationale:** The implementation will delete the file before git operations; testing the end state is adequate.
