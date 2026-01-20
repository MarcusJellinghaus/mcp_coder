# Implementation Task: Write tests for step-level data in `tests/utils/github_operations/test_ci_results_manager_status.py`

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

Current task from TASK_TRACKER.md: Write tests for step-level data in `tests/utils/github_operations/test_ci_results_manager_status.py`

Please implement this task step by step.

## LLM Response:
**Step 0 is now complete!** Here's a summary of what was implemented:

## Summary of Step 0: Foundational Enhancements

### Files Modified:

1. **`src/mcp_coder/utils/github_operations/ci_results_manager.py`**
   - Added `StepData` TypedDict for workflow job step data
   - Added `JobData` TypedDict for workflow job data  
   - Updated `CIStatusData.jobs` from `List[Dict[str, Any]]` to `List[JobData]`
   - Updated `get_latest_ci_status()` to include step data for each job
   - Updated `__all__` exports to include new TypedDicts

2. **`src/mcp_coder/utils/git_operations/commits.py`**
   - Added `get_latest_commit_sha()` helper function for debug logging support
   - Added imports for `subprocess` and `Optional`

3. **`tests/utils/github_operations/test_ci_results_manager_status.py`**
   - Added `TestGetLatestCIStatusSteps` class with 4 new tests:
     - `test_jobs_include_steps_data` 
     - `test_steps_contain_required_fields`
     - `test_empty_steps_when_job_has_no_steps`
     - `test_multiple_jobs_with_steps`
   - Updated existing mocks to include `steps` attribute

4. **`tests/utils/github_operations/test_ci_results_manager_foundation.py`**
   - Added `steps` field to test data to match new TypedDict

5. **`tests/utils/git_operations/test_commits.py`**
   - Added `TestGetLatestCommitSha` class with 3 new tests:
     - `test_returns_sha_in_git_repo`
     - `test_returns_none_outside_git_repo`
     - `test_sha_matches_repo_head`

### Verification:
- ✅ Pylint passes (no errors/warnings related to changes)
- ✅ Mypy passes (no type errors)
- ✅ All sub-tasks marked complete in TASK_TRACKER.md
- ✅ Commit message prepared

---
Generated on: 2026-01-20T08:41:04.667201