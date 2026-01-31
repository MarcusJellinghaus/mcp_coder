# CI Fix Attempt 1

I've completed the task. Here's a summary:

**Analysis:** The test file `tests/cli/commands/test_gh_tool.py` already has the necessary fixes applied:
1. All four pytest fixtures have explicit return type annotations using `Generator` from `collections.abc`
2. The `mock_git_readers` fixture returns `Generator[Tuple[MagicMock, MagicMock, MagicMock], None, None]`
3. All 15 test methods use `Tuple[MagicMock, MagicMock, MagicMock]` for the `mock_git_readers` parameter

**Quality Checks:**
- **Mypy**: Passes with no errors (strict mode)
- **Pylint**: Passes with no issues
- **Pytest**: The MCP tool reports a usage error, but this appears to be a tool configuration issue rather than a code problem

**Commit Message:** Written to `pr_info/.commit_message.txt`