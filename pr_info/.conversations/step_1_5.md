# Implementation Task: Write tests for failing when pr_info/ folder missing

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

Current task from TASK_TRACKER.md: Write tests for failing when pr_info/ folder missing

Please implement this task step by step.

## LLM Response:
**Task completed.** I've implemented Step 2, Sub-task 1: "Write tests for failing when pr_info/ folder missing".

**Changes made:**
1. Added `TestCheckPrerequisitesTaskTracker` class with `test_fails_when_pr_info_missing` test to `tests/workflows/implement/test_prerequisites.py:248-262`
2. Marked the sub-task as complete in `pr_info/TASK_TRACKER.md`
3. Wrote commit message to `pr_info/.commit_message.txt`

The test verifies that when a git repository exists but `pr_info/` directory is missing, `check_prerequisites()` returns `False` and logs the message "folder pr_info not found. Run 'create_plan' first."

---
Generated on: 2026-01-31T14:04:54.811223