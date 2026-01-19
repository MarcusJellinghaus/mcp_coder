# Implementation Task: Add `test_commit_changes_uses_file_when_present` test to `TestCommitChanges`

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

Current task from TASK_TRACKER.md: Add `test_commit_changes_uses_file_when_present` test to `TestCommitChanges`

Please implement this task step by step.

## LLM Response:
I have completed the task. Here's a summary of what was done:

## Task Completed: Add `test_commit_changes_uses_file_when_present` test to `TestCommitChanges`

**File Modified:** `tests/workflows/implement/test_task_processing.py`

**Changes Made:**
- Added a new test method `test_commit_changes_uses_file_when_present` to the `TestCommitChanges` class
- The test verifies that when a commit message file exists at `pr_info/.commit_message.txt`:
  1. The `commit_changes()` function uses the prepared message from the file
  2. The LLM generation function is NOT called (confirming file-based message is preferred)
  3. The commit message file is deleted after reading
  4. The commit is called with the prepared message content

**Test Logic:**
```python
@patch("mcp_coder.workflows.implement.task_processing.commit_all_changes")
@patch("mcp_coder.workflows.implement.task_processing.generate_commit_message_with_llm")
def test_commit_changes_uses_file_when_present(
    self, mock_generate_message: MagicMock, mock_commit: MagicMock, tmp_path: Path
) -> None:
    # Creates commit file, calls commit_changes, verifies:
    # - LLM not called
    # - File deleted
    # - Prepared message used in commit
```

**Task Tracker Updated:** Marked `- [x] Add test_commit_changes_uses_file_when_present test to TestCommitChanges` as complete.

---
Generated on: 2026-01-19T16:36:17.535366