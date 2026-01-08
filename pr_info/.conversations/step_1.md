# Implementation Task: Implement test `test_cleanup_repository_includes_conversations_cleanup` in `tests/workflows/create_pr/test_repository.py`

## Prompt Sent to LLM:
Implement ONE step from the task tracker.

**1. SELECT STEP**
- Read `pr_info/TASK_TRACKER.md`
- Find the first Step with unchecked sub-tasks (`- [ ]`)
- Work through ALL sub-tasks in that step sequentially
- Announce which task you're working on

**2. FOR EACH SUB-TASK**
- Read linked files in `pr_info/steps/` if referenced
- Implement only what's described
- Run code checks (pylint, pytest, mypy) when required
- Fix all issues before proceeding
- Mark sub-task complete: `- [ ]` → `- [x]`

**3. COMPLETE THE STEP**
- All sub-tasks must be `[x]` before finishing
- Prepare commit message when that sub-task appears
- Do NOT commit - just prepare the message

**RULES:**
- ONE step per run (but complete all its sub-tasks)
- Mark each sub-task `[x]` immediately after completing it
- Use MCP tools for all operations

Current task from TASK_TRACKER.md: Implement test `test_cleanup_repository_includes_conversations_cleanup` in `tests/workflows/create_pr/test_repository.py`

Please implement this task step by step.

## LLM Response:
## Step 1 Complete

**Summary of changes made:**

1. **Added new test** `test_cleanup_repository_includes_conversations_cleanup` in `tests/workflows/create_pr/test_repository.py:95-114`
   - Mocks all four cleanup helpers: `delete_steps_directory`, `truncate_task_tracker`, `clean_profiler_output`, and `delete_conversations_directory`
   - Verifies that all functions are called correctly when `cleanup_repository()` is invoked
   - This test will **fail** until Step 2 implements the `delete_conversations_directory` function (TDD approach)

2. **Updated existing tests** to mock `clean_profiler_output` for full isolation:
   - `test_cleanup_repository_success` (line 12-31)
   - `test_cleanup_repository_delete_fails` (line 33-52)
   - `test_cleanup_repository_truncate_fails` (line 54-73)
   - `test_cleanup_repository_both_fail` (line 75-93)

3. **Quality checks passed:**
   - Pylint: No issues
   - Mypy: No type errors

---

**Prepared Git Commit Message:**

```
test: add test for conversations directory cleanup in cleanup_repository

- Add test_cleanup_repository_includes_conversations_cleanup to verify
  that cleanup_repository() calls delete_conversations_directory()
- Update existing cleanup_repository tests to mock clean_profiler_output
  for proper isolation of unit tests
- Following TDD approach: test will fail until implementation is added

Closes #259
```

---
Generated on: 2026-01-09T00:44:50.619241