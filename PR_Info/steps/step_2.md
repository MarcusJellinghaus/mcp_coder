# Step 2: Copy and Adapt Git Operations Tests

## Goal
Verify foundation works correctly by copying and adapting existing tests from p_fs.

## Tasks
1. Copy test file from p_fs reference to `tests/utils/test_git_operations.py`
2. Update import paths to reference new location
3. Run tests to confirm foundation is solid

## Test Coverage Being Copied
- Git repository detection (valid/invalid repos)
- File tracking detection (tracked/untracked/staged files)
- Edge cases (files outside repo, git command errors)
- Mock testing for error scenarios

## Expected Changes
- **Source**: `p_fs:tests/file_tools/test_git_operations.py`
- **Target**: `tests/utils/test_git_operations.py`
- **Import Change**: `mcp_server_filesystem.file_tools.git_operations` → `mcp_coder.utils.git_operations`

## Done When
- All existing tests pass
- Test file imports correctly
- Foundation functionality verified in MCP Coder environment

## Integration Notes
- Preserve all test logic, fixtures, and mock patterns
- Only modify import paths, not test behavior
- Ensure compatibility with MCP Coder test patterns
