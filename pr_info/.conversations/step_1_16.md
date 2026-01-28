# Implementation Task: Add stale check to restart_closed_sessions() - skip sessions where issue status changed

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
- Write commit message to `pr_info/.commit_message.txt`
- Do NOT commit - just write the message to the file

**RULES:**
- ONE step per run (but complete all its sub-tasks)
- Mark each sub-task `[x]` immediately after completing it
- Use MCP tools for all operations

Current task from TASK_TRACKER.md: Add stale check to restart_closed_sessions() - skip sessions where issue status changed

Please implement this task step by step.

## LLM Response:
**Step 10 is now complete!**

## Summary

I have completed all sub-tasks for Step 10: Code Review Fixes (Round 2):

1. **✅ Add stale check to restart_closed_sessions()** - Added a call to `is_session_stale()` in the session restart loop to skip sessions where the issue status has changed since the session was created.

2. **✅ Add validation to _get_repo_full_name()** - Changed the function to raise `ValueError` with a helpful message if the repo URL cannot be parsed, instead of returning "unknown/repo".

3. **✅ Remove unused issue_manager parameter from handle_pr_created_issues()** - Removed the unused parameter from both the function signature and its call site in `process_eligible_issues()`.

4. **✅ Remove redundant import json from test method** - Removed the local `import json` inside `test_workspace_file_is_valid_json_template()` since json is already imported at module level.

5. **✅ Remove empty TestIntegration class** - Already removed in a previous step, verified it doesn't exist.

6. **✅ Standardize type hints to modern Python 3.9+ syntax** - Updated all type hints:
   - `List[X]` → `list[X]`
   - `Optional[X]` → `X | None`
   - Removed unused `List`, `Optional` imports from `typing` module

7. **✅ Run pylint** - Passed with no issues.

8. **✅ Run pytest** - Fixed test calls that still used the old `handle_pr_created_issues` signature.

9. **✅ Run mypy** - Passed with no type errors.

10. **✅ Prepare commit message** - Written to `pr_info/.commit_message.txt`.

---
Generated on: 2026-01-28T06:59:51.570243