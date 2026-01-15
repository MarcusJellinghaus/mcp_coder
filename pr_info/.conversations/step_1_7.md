# Implementation Task: Update `test_find_multiple_files` in `TestFindPackageDataFiles` to use real `mcp_coder` files (Decision #10)

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

Current task from TASK_TRACKER.md: Update `test_find_multiple_files` in `TestFindPackageDataFiles` to use real `mcp_coder` files (Decision #10)

Please implement this task step by step.

## LLM Response:
I have completed the sub-task: **Update `test_find_multiple_files` in `TestFindPackageDataFiles` to use real `mcp_coder` files (Decision #10)**

## Summary of Changes

**File modified:** `tests/utils/test_data_files.py:121-131`

**Before:**
```python
def test_find_multiple_files(self) -> None:
    """Test finding multiple data files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        files = [
            temp_path / "src" / "mcp_coder" / "prompts" / "test1.md",
            temp_path / "src" / "mcp_coder" / "prompts" / "test2.md",
        ]
        for file_path in files:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text("# test content")

        result = find_package_data_files(
            package_name="mcp_coder",
            relative_paths=["prompts/test1.md", "prompts/test2.md"],
            development_base_dir=temp_path,
        )
        assert len(result) == 2
        assert result[0] == files[0]
        assert result[1] == files[1]
```

**After:**
```python
def test_find_multiple_files(self) -> None:
    """Test finding multiple data files using real mcp_coder package."""
    result = find_package_data_files(
        package_name="mcp_coder",
        relative_paths=["prompts/prompts.md", "prompts/prompt_instructions.md"],
    )

    assert len(result) == 2
    assert all(path.exists() for path in result)
```

**Key changes:**
1. Removed temporary directory creation and fake file setup
2. Removed `development_base_dir` parameter (Decision #6)
3. Uses real `mcp_coder` package files (`prompts/prompts.md`, `prompts/prompt_instructions.md`)
4. Simplified assertions to check that files exist

---
Generated on: 2026-01-15T16:47:37.693132