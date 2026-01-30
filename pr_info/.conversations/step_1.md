# Implementation Task: Write unit tests for `_parse_base_branch()` in `tests/utils/github_operations/test_issue_manager.py`

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

Current task from TASK_TRACKER.md: Write unit tests for `_parse_base_branch()` in `tests/utils/github_operations/test_issue_manager.py`

Please implement this task step by step.

## LLM Response:
I've completed the task. Here's a summary of what was done:

## Summary

**Task Completed:** Write unit tests for `_parse_base_branch()` in `tests/utils/github_operations/test_issue_manager.py`

**What was added:**
I appended a new test class `TestParseBaseBranch` to the test file with 11 test cases covering:

1. **Valid base branches (4 tests):**
   - `test_parse_base_branch_with_h3_header` - Standard H3 header format
   - `test_parse_base_branch_case_insensitive` - Lowercase header
   - `test_parse_base_branch_uppercase` - Uppercase header  
   - `test_parse_base_branch_with_h1_header` - H1 header format

2. **Returns None cases (5 tests):**
   - `test_parse_base_branch_no_section` - Missing section
   - `test_parse_base_branch_empty_body` - Empty string body
   - `test_parse_base_branch_none_body` - None body
   - `test_parse_base_branch_empty_content` - Section with no content
   - `test_parse_base_branch_whitespace_only` - Section with only whitespace

3. **Error cases (2 tests):**
   - `test_parse_base_branch_multiline_raises_error` - Raises ValueError for multi-line content
   - `test_parse_base_branch_multiline_with_spaces_raises_error` - Raises ValueError for multi-line with spaces

The tests are written following TDD - they import `_parse_base_branch` from `issue_manager.py` (which doesn't exist yet), so they will fail until the implementation is done in the next sub-task.

**Task tracker updated:** `- [x]` marked for this sub-task.

---
Generated on: 2026-01-30T21:22:36.132310