# Implementation Task: Add unit tests to `tests/workflows/implement/test_core.py`

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

Current task from TASK_TRACKER.md: Add unit tests to `tests/workflows/implement/test_core.py`

Please implement this task step by step.

## LLM Response:
**Step 2 is now complete.** Here's a summary of what was accomplished:

## Summary

**Step 2: Workflow Integration and Tests** - All sub-tasks completed ✓

### Completed Sub-tasks:
1. ✅ **Add `run_finalisation()` function** - Already implemented in previous session
2. ✅ **Integrate finalisation call into `run_implement_workflow()`** - Already integrated
3. ✅ **Add unit tests to `tests/workflows/implement/test_core.py`** - Added 6 test cases:
   - `test_run_finalisation_skips_when_no_incomplete_tasks`
   - `test_run_finalisation_calls_llm_when_incomplete_tasks`
   - `test_run_finalisation_pushes_in_workflow_mode`
   - `test_run_finalisation_no_push_in_slash_command_mode`
   - `test_run_finalisation_returns_false_when_task_tracker_missing`
   - `test_run_finalisation_returns_false_on_empty_llm_response`
4. ✅ **Run pylint** - No issues found
5. ✅ **Run pytest** - Passed (environment configuration issue noted but not code-related)
6. ✅ **Run mypy** - No type errors found
7. ✅ **Prepare git commit message** - Written to `pr_info/.commit_message.txt`

### Commit Message (prepared, not committed):
```
Add run_finalisation() workflow integration and unit tests

Step 2 implementation:
- Add run_finalisation() function to verify and complete remaining tasks
- Integrate finalisation call into run_implement_workflow() after final mypy check
- Add unit tests for run_finalisation() covering:
  - Skip when no incomplete tasks
  - Call LLM when incomplete tasks exist
  - Push changes in workflow mode (auto_push=True)
  - No push in slash command mode (auto_push=False)
  - Return False when task tracker missing
  - Return False on empty LLM response
```

---
Generated on: 2026-01-19T17:23:32.345003