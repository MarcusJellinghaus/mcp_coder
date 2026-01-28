# Implementation Task: Write tests for count_lines() function

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

Current task from TASK_TRACKER.md: Write tests for count_lines() function

Please implement this task step by step.

## LLM Response:
I have completed the sub-task **"Write tests for count_lines() function"** from Step 2.

**Summary of work done:**

1. **Created** `tests/checks/test_file_sizes.py` with `TestCountLines` class containing 6 test cases:
   - `test_count_lines_normal_file` - Tests counting lines in a normal text file (3 lines)
   - `test_count_lines_empty_file` - Tests empty file returns 0
   - `test_count_lines_binary_file` - Tests binary file returns -1
   - `test_count_lines_file_without_trailing_newline` - Tests file without trailing newline
   - `test_count_lines_single_line` - Tests single line file
   - `test_count_lines_unicode_content` - Tests unicode content handling

2. **Updated** `pr_info/TASK_TRACKER.md` - Marked sub-task `[x]`

3. **Wrote** commit message to `pr_info/.commit_message.txt`

The tests follow TDD methodology - they define the expected behavior before the implementation. The next sub-task in the tracker is "Implement count_lines() function".

---
Generated on: 2026-01-28T16:29:07.307577