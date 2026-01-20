# Implementation Task: Extract `_run_ci_analysis()` helper function

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

Current task from TASK_TRACKER.md: Extract `_run_ci_analysis()` helper function

Please implement this task step by step.

## LLM Response:
I have completed all sub-tasks for the current task: **Extract `_run_ci_analysis()` helper function**.

## Summary

I successfully completed the following sub-tasks for **Step 5: Code Review Fixes**:

1. **Extract `_run_ci_analysis()` helper function** - Created a new function that handles CI failure analysis, including loading prompts, calling LLM, reading problem description from temp file, and saving conversation for debugging.

2. **Extract `_run_ci_fix()` helper function** - Created a new function that handles CI fix attempts, including loading prompts, calling LLM, saving conversation, running formatters, committing and pushing changes.

3. **Simplify `_run_ci_analysis_and_fix()` to use new helpers** - Refactored the main function to use `CIFixConfig` dataclass and call the two new helper functions.

4. **Remove pylint disables** - The refactored `_run_ci_analysis_and_fix()` no longer needs the `# pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-branches` comment.

5. **Update `_get_failed_jobs_summary` type annotation** - Changed from `list[dict[str, Any]] | list[Any]` to `list[JobData]`.

6. **Add short SHA (7 chars) to all CI status log messages** - Updated log messages in `_poll_for_ci_completion`, `_wait_for_new_ci_run`, and `check_and_fix_ci`.

7. **Update `_read_problem_description` for empty file** - Modified to use fallback when temp file exists but is empty or whitespace-only.

8. **Add tests for `_read_problem_description` edge cases** - Added 4 new test cases: empty file, whitespace-only file, file with content, and missing file.

9. **Run pylint** - Passed (only existing W0718 warnings for broad exception handling)

10. **Run mypy** - Passed with no type errors

11. **Prepare commit message** - Added to task tracker

---
Generated on: 2026-01-20T10:04:41.164148