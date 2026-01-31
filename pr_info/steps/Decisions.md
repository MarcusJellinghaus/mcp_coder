# Decisions Log

## Issue #357 - Subprocess Library Isolation

Decisions made during plan review discussion.

---

### Decision 1: Add Missing Test File to Plan

**Context:** `tests/cli/test_main.py` imports `subprocess` but was not included in the plan. The import is unused.

**Decision:** Add this file to Step 2 to remove the unused import.

**Rationale:** Keeps the plan complete and ensures lint-imports will pass.

---

### Decision 2: Delete Test Rather Than Migrate

**Context:** `test_subprocess_encoding_directly()` in `tests/utils/test_git_encoding_stress.py` directly tests subprocess encoding behavior, violating the new constraint.

**Decision:** Delete the test as originally planned.

**Rationale:** The encoding handling is already covered by `subprocess_runner.py` with `errors="replace"`. The test is redundant.

---

### Decision 3: Keep Granular Task Tracking

**Context:** TASK_TRACKER.md lists Tasks 1.4-1.8 separately (one per file), while step_1.md consolidates them.

**Decision:** Keep the granular breakdown (1.4-1.8) in TASK_TRACKER.

**Rationale:** Easier to track progress file-by-file during implementation.

---

### Decision 4: Remove Fallback Without Investigation

**Context:** `claude_executable_finder.py` has fallback `subprocess.run()` calls that would be removed.

**Decision:** Remove the fallback as planned, trusting the subprocess_runner wrapper.

**Rationale:** The wrapper is robust and handles all edge cases. Simpler architecture without fallback patterns.
