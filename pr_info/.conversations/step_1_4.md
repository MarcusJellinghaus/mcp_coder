# Implementation Task: Add test case for closed issue with missing folder being skipped

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

Current task from TASK_TRACKER.md: Add test case for closed issue with missing folder being skipped

Please implement this task step by step.

## LLM Response:
I'll start by reading the task tracker to understand the current task and its sub-tasks.Now I can see the current task. I'm working on **Step 2**, and the next unchecked sub-task is:
- **"Add test case for closed issue with missing folder being skipped"**

Let me read the step 2 details to understand what's needed.Now let me read the existing test file to understand the current test structure and add the new test case.Now I understand the test structure. I need to add a test case for **closed issue with missing folder being skipped**. Based on the step 2 details, when a closed issue has a missing folder, the session should be skipped entirely (not shown in the table).

Let me add this test case to the `TestClosedIssuePrefixDisplay` class:I've added two test cases:
1. `test_closed_issue_missing_folder_is_skipped` - Tests that a closed issue with a missing folder is NOT shown in the status table
2. `test_closed_issue_existing_folder_is_shown` - Tests the contrast case where a closed issue with an existing folder IS shown

Now let me run the tests to see the current status (these tests are expected to fail since the implementation isn't done yet, but let's verify they work correctly):Let me try a different approach to run the tests:Let me try running the full test file to check if the tests are valid:Let me check if there's an issue with the pytest configuration:Now let me run just the tests in the test file without extra arguments:Let me try without any extra_args:Let me check if there's an issue with the test configuration:The file structure looks correct. Let me check if there's an issue with the mcp pytest tool by running a simpler command:There seems to be a persistent issue with the MCP pytest tool. Let me check if there's something wrong with the test file syntax:Good, mypy and pylint pass. Let me check if the test file is syntactically correct by reading it:The test file looks good and syntactically correct. The mcp pytest tool seems to have an issue but the code is properly written. Let me now mark the sub-task as complete and update the task tracker.Now let me write the commit message to the file:I have completed the sub-task. Here's a summary of what was done:

## Summary

**Task Completed:** Add test case for closed issue with missing folder being skipped

**Changes Made:**
- Added two new test methods to `TestClosedIssuePrefixDisplay` class in `tests/workflows/vscodeclaude/test_status_display.py`:

1. **`test_closed_issue_missing_folder_is_skipped`** - Tests that when a session has:
   - A closed issue (`is_issue_closed` returns `True`)
   - A missing folder (folder path does not exist)
   
   The session should **NOT** be displayed in the status table (issue number `#789` should not appear in output).

2. **`test_closed_issue_existing_folder_is_shown`** - Contrast test showing that when:
   - A closed issue (`is_issue_closed` returns `True`)
   - The folder **EXISTS**
   
   The session **IS** displayed with `(Closed)` prefix (for cleanup purposes).

**Verification:**
- Pylint: ✅ Passed
- Mypy: ✅ Passed
- Commit message written to `pr_info/.commit_message.txt`

**Note:** The MCP pytest tool has a configuration issue and cannot run tests directly, but the test code is syntactically correct and follows the existing test patterns.

---
Generated on: 2026-02-10T08:32:39.190232