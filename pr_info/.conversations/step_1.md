# Implementation Task: Replace `STATUS_FILE_TEMPLATE` with plain text banner format

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

Current task from TASK_TRACKER.md: Replace `STATUS_FILE_TEMPLATE` with plain text banner format

Please implement this task step by step.

## LLM Response:
I'll start by reading the task tracker to understand the current task and its sub-tasks.Now I can see Step 1 is the first step with unchecked sub-tasks. Let me read the step 1 detail file to understand the implementation requirements.Now let me read the current templates.py file to understand the existing code.Now I have a clear understanding of the current code. Let me create a todo list to track my progress through the sub-tasks of Step 1.Now I'll implement the first sub-task: Replace `STATUS_FILE_TEMPLATE` with the new plain text banner format.The first sub-task is complete. Let me mark it and move to the second sub-task.Now updating GITIGNORE_ENTRY to use `.txt` instead of `.md`:Second sub-task complete. Now let me move to the third sub-task - adding a second task to TASKS_JSON_TEMPLATE:Third sub-task complete. Now let me move to the fourth sub-task - removing INTERVENTION_ROW:Let me read the current file to see the exact text of INTERVENTION_ROW and its surrounding context:Now I can see INTERVENTION_ROW. Let me remove it completely:Fourth sub-task complete. Now let me run the code checks. First, let me update the todo list and run pylint:Pylint found an issue - there's still a reference to `INTERVENTION_ROW` in workspace.py. However, according to the task instructions, I should only modify the templates.py file in Step 1. The workspace.py modifications are part of Step 2. Let me check the step 1 instructions again to confirm this is expected.

Looking at step_1.md, it says under VERIFICATION: "**Note:** Do not run tests after this step - tests will break until Step 3 completes."

This suggests that having intermediate breakage between steps is expected. The reference to `INTERVENTION_ROW` in workspace.py will be fixed in Step 2 when we update the workspace functions.

However, for Step 1, I should still verify that the templates.py file itself has no pylint issues. Let me run pylint specifically on just the templates.py file:Let me run pylint directly on the templates file only:Pylint passes for the templates.py file. The error about `INTERVENTION_ROW` not being found is in workspace.py, which imports it - that's expected and will be fixed in Step 2.

Let me update the task tracker to mark this sub-task complete and move to pytest:Let me try running the test without extra path:Let me check the test directory structure:I see tests are in `tests/` directory. According to step_1.md, the verification note says "Do not run tests after this step - tests will break until Step 3 completes." So I should not expect pytest to pass at this point.

However, since the task tracker has "Run pytest and fix any issues" as a sub-task, let me see if the tests related to templates specifically can be checked. The step_1.md also mentions "Quick syntax check only" as verification. Let me note that the tests are expected to fail until Step 3, but I'll mark this as complete per the instruction since the template file changes are syntactically correct.

Let me run mypy to check type issues:Mypy passes for the templates.py file. Now let me mark mypy complete and move to the final sub-task - preparing the git commit message:Now I'll write the commit message to the file:Now let me update the task tracker to mark all the sub-tasks as complete:**Step 1 Complete!** 

Here's a summary of what was accomplished:

## Step 1: Update Templates - COMPLETED ✓

### Changes made to `src/mcp_coder/workflows/vscodeclaude/templates.py`:

1. **STATUS_FILE_TEMPLATE** - Replaced markdown table format with plain text banner format:
   - Uses `=====` borders
   - Shows emoji, issue number, and title on first line
   - Lists Repo, Status, Branch, Started, URL in plain text format
   - Uses `{intervention_line}` placeholder instead of `{intervention_row}`

2. **GITIGNORE_ENTRY** - Updated from `.vscodeclaude_status.md` to `.vscodeclaude_status.txt`

3. **TASKS_JSON_TEMPLATE** - Added second VSCode task:
   - "Open Status File" task that runs `code ${workspaceFolder}/.vscodeclaude_status.txt`
   - Both tasks have `runOn: folderOpen`

4. **INTERVENTION_ROW** - Removed entirely (was only used for the old markdown table format)

### Verification:
- ✓ Pylint passes on templates.py
- ✓ Mypy passes on templates.py
- ✓ Commit message written to `pr_info/.commit_message.txt`

### Note:
Tests are expected to fail until Step 3 is completed, as mentioned in the step_1.md verification section.

---
Generated on: 2026-02-04T10:48:32.794853