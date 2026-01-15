# Implementation Task: Rename and convert `test_find_installed_file_via_importlib` to `test_find_file_in_installed_package` using real `mcp_coder` package (Decision #11)

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

Current task from TASK_TRACKER.md: Rename and convert `test_find_installed_file_via_importlib` to `test_find_file_in_installed_package` using real `mcp_coder` package (Decision #11)

Please implement this task step by step.

## LLM Response:
## Summary

I've completed the sub-task: **Rename and convert `test_find_installed_file_via_importlib` to `test_find_file_in_installed_package` using real `mcp_coder` package (Decision #11)**

### Changes made:

**File:** `tests/utils/test_data_files.py:22-34`

The test was transformed from a complex 40-line test that:
- Created a temporary directory with a fake package
- Manipulated `sys.path` and `sys.modules`
- Used `development_base_dir=None` parameter
- Required cleanup in a finally block

To a simple 13-line test that:
- Uses the real `mcp_coder` package (already installed)
- Tests with actual file `prompts/prompts.md`
- Has no cleanup requirements
- Removes the obsolete `development_base_dir` parameter

### New test implementation:
```python
def test_find_file_in_installed_package(self) -> None:
    """Test finding a file in installed package using importlib.resources.

    Uses real mcp_coder package - no mocking or sys.path manipulation needed.
    """
    result = find_data_file(
        package_name="mcp_coder",
        relative_path="prompts/prompts.md",
    )

    assert result.exists()
    assert result.name == "prompts.md"
    assert "mcp_coder" in str(result)
```

The task tracker has been updated to mark this sub-task as complete (`[x]`).

---
Generated on: 2026-01-15T16:34:15.330282