# Implementation Task: Add `test_commit_changes_logs_message_on_failure` test to `TestCommitChanges`

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

Current task from TASK_TRACKER.md: Add `test_commit_changes_logs_message_on_failure` test to `TestCommitChanges`

Please implement this task step by step.

## LLM Response:
I have completed the task. Here's a summary:

## Summary

**Task completed:** Added `test_commit_changes_logs_message_on_failure` test to `TestCommitChanges`

**What was done:**
- Added a new test method `test_commit_changes_logs_message_on_failure` to the `TestCommitChanges` class in `tests/workflows/implement/test_task_processing.py`
- The test verifies that when a commit operation fails, the commit message is logged so it's not lost
- The test uses pytest's `caplog` fixture to capture log output and verify the message appears

**Test implementation (`tests/workflows/implement/test_task_processing.py:367-386`):**
```python
@patch("mcp_coder.workflows.implement.task_processing.commit_all_changes")
def test_commit_changes_logs_message_on_failure(
    self, mock_commit: MagicMock, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Test commit message is logged when commit fails."""
    # Create commit message file
    pr_info = tmp_path / "pr_info"
    pr_info.mkdir()
    commit_file = pr_info / ".commit_message.txt"
    commit_file.write_text("feat: important message")

    mock_commit.return_value = {
        "success": False,
        "commit_hash": None,
        "error": "Git failed",
    }

    result = commit_changes(tmp_path)

    assert result is False
    # Message should be logged so it's not lost
    assert "feat: important message" in caplog.text
```

**Task tracker updated:** Marked the sub-task as complete `[x]` in `pr_info/TASK_TRACKER.md`

**Next sub-tasks remaining in Step 2:**
- Run quality checks (pylint, pytest, mypy) and fix any issues
- Prepare git commit message

---
Generated on: 2026-01-19T17:22:51.478130