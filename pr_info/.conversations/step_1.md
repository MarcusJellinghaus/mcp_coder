# Implementation Task: Create `tests/cli/commands/test_set_status.py` with unit tests

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

Current task from TASK_TRACKER.md: Create `tests/cli/commands/test_set_status.py` with unit tests

Please implement this task step by step.

## LLM Response:
**Step 1 is now complete.** 

Here's a summary of what was accomplished:

## Summary

### Created: `tests/cli/commands/test_set_status.py`

The test file includes:

1. **TestSetStatusHelpers** (3 tests)
   - `test_get_status_labels_from_config` - Tests loading status labels from config
   - `test_validate_status_label_valid` - Tests validation accepts valid status labels
   - `test_validate_status_label_invalid` - Tests validation rejects invalid labels

2. **TestComputeNewLabels** (3 tests)
   - `test_compute_replaces_status_label` - Tests that existing status-* labels are replaced
   - `test_compute_preserves_non_status_labels` - Tests that non-status labels are preserved
   - `test_compute_with_no_existing_status` - Tests adding status when none exists

3. **TestExecuteSetStatus** (5 tests)
   - `test_execute_success_with_branch_detection` - Tests auto-detected issue from branch
   - `test_execute_success_with_explicit_issue` - Tests with --issue flag
   - `test_execute_invalid_label_returns_one` - Tests invalid label returns exit code 1
   - `test_execute_no_issue_detected_returns_one` - Tests branch pattern mismatch
   - `test_execute_github_error_returns_one` - Tests GitHub API error handling

### Quality Checks
- **Pylint**: No errors in the test file (import errors expected until Step 2)
- **Mypy**: No type issues (import-not-found expected until Step 2)
- **pytest**: Tests are discoverable (expected to fail until Step 2)

### Commit Message
Written to `pr_info/.commit_message.txt`

---
Generated on: 2026-01-21T10:45:22.266427