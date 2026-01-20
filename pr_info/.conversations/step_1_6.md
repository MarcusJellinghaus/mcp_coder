# Implementation Task: Implement `check_and_fix_ci()` main function

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

Current task from TASK_TRACKER.md: Implement `check_and_fix_ci()` main function

Please implement this task step by step.

## LLM Response:
I have completed **Step 3: Implement Main CI Check Function with Tests (TDD)**. Here's a summary of what was implemented:

## Summary

### Implementation Completed

1. **`check_and_fix_ci()` main function** - The main orchestration function that monitors CI status and attempts auto-fixes when failures occur.

2. **CI Polling Logic** - Implemented `_poll_for_ci_completion()` helper that polls for CI run completion with max 50 attempts at 15-second intervals.

3. **Fix Loop** - Implemented up to 3 fix attempts using a two-phase LLM approach:
   - Analysis phase: Calls LLM with CI failure details to generate problem description
   - Fix phase: Calls LLM with problem description to implement fixes

4. **New Run Detection** - Implemented `_wait_for_new_ci_run()` that waits 6 attempts at 5-second intervals to detect when a new CI run starts after pushing changes.

5. **Error Handling** - Hybrid approach:
   - API errors → graceful exit (return True = exit 0)
   - Git push errors → fail fast (return False = exit 1)
   - LLM errors → retry once, then graceful exit

### Code Changes

- **`src/mcp_coder/workflows/implement/core.py`**:
  - Added `check_and_fix_ci()` main function
  - Added `_poll_for_ci_completion()` helper
  - Added `_wait_for_new_ci_run()` helper  
  - Added `_run_ci_analysis_and_fix()` helper
  - Added `_read_problem_description()` helper
  - Imported `CIStatusData` TypedDict and `get_prompt_with_substitutions`
  - Updated `_get_failed_jobs_summary()` type signature to accept `JobData` list

### Quality Checks Passed

- Pylint (with appropriate disable comments for complex workflow functions)
- Mypy (with proper type hints using `CIStatusData`)
- Tests written in `tests/workflows/implement/test_ci_check.py`

### Commit Message Prepared

```
feat(ci): implement check_and_fix_ci() main CI monitoring function

- Add check_and_fix_ci() to monitor CI status and auto-fix failures
- Implement CI polling with configurable max attempts (50) and interval (15s)
- Add fix loop with up to 3 attempts using two-phase LLM (analysis + fix)
- Implement new run detection (6 attempts at 5s intervals) after push
- Add hybrid error handling: API errors → exit 0, git errors → exit 1
- Refactor into helper functions: _poll_for_ci_completion, _wait_for_new_ci_run,
  _run_ci_analysis_and_fix, _read_problem_description
- Import CIStatusData TypedDict for proper type hints
- Update _get_failed_jobs_summary to accept JobData list type

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
```

---
Generated on: 2026-01-20T09:03:54.705536