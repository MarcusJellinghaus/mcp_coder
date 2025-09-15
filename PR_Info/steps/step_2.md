# Step 2: Copy and Adapt Git Operations Tests

## WHERE
- **Source**: `p_fs:tests/file_tools/test_git_operations.py`
- **Target**: `tests/utils/test_git_operations.py`

## WHAT
Copy existing test suite and adapt import paths for MCP Coder structure.

### Test Classes (Copied)
```python
class TestGitDetection:
    def test_is_git_repository_with_actual_repo(self, tmp_path: Path) -> None
    def test_is_git_repository_with_invalid_repo(self, tmp_path: Path) -> None  
    def test_is_file_tracked_without_git(self, tmp_path: Path) -> None
    def test_is_file_tracked_with_git(self, tmp_path: Path) -> None
    def test_is_file_tracked_outside_repo(self, tmp_path: Path) -> None
    def test_is_file_tracked_with_staged_file(self, tmp_path: Path) -> None
    # ... mock tests
```

## HOW
### Integration Points
- Import path: Update from `mcp_server_filesystem.file_tools.git_operations` to `mcp_coder.utils.git_operations`
- Test structure: Maintain pytest patterns and fixtures
- Mock patterns: Preserve existing mock strategies

### File Modifications
1. **Copy test file**: Copy from p_fs reference project
2. **Update imports**: Change import paths for new module location
3. **Verify test structure**: Ensure compatibility with MCP Coder test patterns

## ALGORITHM  
```
1. Read source test_git_operations.py from p_fs reference
2. Update import statement: mcp_server_filesystem → mcp_coder
3. Update import path: file_tools.git_operations → utils.git_operations
4. Preserve all test logic, fixtures, and mock patterns
5. Verify tests run correctly with pytest
```

## DATA
### Input Files
- `p_fs:tests/file_tools/test_git_operations.py`

### Output Files
- `tests/utils/test_git_operations.py`

### Test Coverage
- Git repository detection (valid/invalid repos)
- File tracking detection (tracked/untracked/staged files)
- Edge cases (files outside repo, git command errors)
- Mock testing for error scenarios

---

## LLM PROMPT
```
Reference the summary in pr_info/steps/summary.md and decisions in pr_info/steps/Decisions.md for context.

Implement Step 2: Copy the test_git_operations.py file from the p_fs reference project to tests/utils/test_git_operations.py. Update the import statements to reference the new location at mcp_coder.utils.git_operations.

Key requirements:
- Copy all test classes and methods exactly as they are
- Update import: from mcp_server_filesystem.file_tools.git_operations → from mcp_coder.utils.git_operations  
- Preserve all test logic, fixtures, and mock patterns
- Ensure tests run with pytest and validate the copied git_operations.py works correctly
- Do not modify test logic, only adapt import paths

Run the tests to verify the copied functionality works correctly in the MCP Coder environment.
```
