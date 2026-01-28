# Implementation Task: Write tests for get_file_metrics() function

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

Current task from TASK_TRACKER.md: Write tests for get_file_metrics() function

Please implement this task step by step.

## LLM Response:
I've completed the task. Here's a summary:

## Task Completed: Write tests for get_file_metrics() function

**What was done:**
- Added 4 test methods to the `TestGetFileMetrics` class in `tests/checks/test_file_sizes.py`:
  1. `test_get_file_metrics_multiple_files` - Tests getting metrics for multiple files with known line counts
  2. `test_get_file_metrics_skips_binary` - Tests that binary files are excluded from results (as specified in the algorithm)
  3. `test_get_file_metrics_empty_list` - Tests handling of empty file list
  4. `test_get_file_metrics_returns_file_metrics_objects` - Tests that results are proper `FileMetrics` objects

- Updated the import statement to include `FileMetrics` and `get_file_metrics`
- Marked the sub-task as complete in `pr_info/TASK_TRACKER.md`

**Next task:** The next unchecked sub-task is "Implement get_file_metrics() function" which will implement the function to make these tests pass.

---
Generated on: 2026-01-28T16:39:44.179903