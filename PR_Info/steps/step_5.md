# Step 5: Create MCP Filesystem-Specific Tests

## Objective
Implement detailed tests specifically for mcp-server-filesystem integration, covering advanced filesystem operations, reference projects, and edge cases.

## WHERE
- **File**: `tests/integration/test_mcp_filesystem.py`
- **Supporting Tests**: Additional test cases in main integration test file
- **Documentation**: Update test documentation with filesystem-specific scenarios

## WHAT
### Main Test Functions
```python
class TestMCPFilesystemOperations:
    def test_directory_operations(self, mcp_config_manager, test_project_with_files)
    def test_reference_project_access(self, mcp_config_manager, test_project_with_files) 
    def test_file_move_operations(self, mcp_config_manager, test_project_with_files)
    def test_file_edit_operations(self, mcp_config_manager, test_project_with_files)
    def test_batch_file_operations(self, mcp_config_manager, test_project_with_files)
    def test_large_file_handling(self, mcp_config_manager, test_project_with_files)
    def test_filesystem_edge_cases(self, mcp_config_manager, test_project_with_files)
    def test_concurrent_operations(self, mcp_config_manager, test_project_with_files)
```

### Advanced Filesystem Features
- **Reference Projects**: Test read-only access to additional directories
- **File Editing**: Test precise file modifications using edit_file tool
- **Directory Operations**: Test directory creation, listing, navigation
- **Move Operations**: Test file/directory move and rename operations
- **Batch Operations**: Test multiple file operations in single session

## HOW
### Integration Points
- **MCP Filesystem Tools**: `list_directory`, `read_file`, `save_file`, `edit_file`, `move_file`
- **Reference Projects**: Test `get_reference_projects`, `list_reference_directory`, `read_reference_file`
- **Advanced Scenarios**: Multi-step workflows, error recovery, resource limits
- **Performance Testing**: Large files, many files, concurrent operations

### Test Coverage Strategy
- Cover all mcp-server-filesystem tools individually and in combination
- Test both success paths and error conditions
- Include edge cases like large files, special characters, permissions
- Verify reference project functionality works correctly

## ALGORITHM
```
1. Set up MCP filesystem server with test project and reference projects
2. Execute comprehensive filesystem operation tests
3. Verify advanced features like file editing and reference projects
4. Test edge cases and error conditions
5. Validate performance characteristics and resource usage
```

## DATA
### Filesystem Test Scenarios
```python
FILESYSTEM_OPERATIONS = [
    {
        "category": "directory_ops",
        "tests": [
            {"prompt": "List all directories in the project", "tools": ["list_directory"]},
            {"prompt": "Show me the file structure", "tools": ["list_directory"]}
        ]
    },
    {
        "category": "file_editing", 
        "tests": [
            {"prompt": "Change 'Hello' to 'Hi' in main.py", "tools": ["edit_file"]},
            {"prompt": "Add a comment to the top of main.py", "tools": ["read_file", "edit_file"]}
        ]
    },
    {
        "category": "reference_projects",
        "tests": [
            {"prompt": "What reference projects are available?", "tools": ["get_reference_projects"]},
            {"prompt": "Read the README from the docs reference", "tools": ["read_reference_file"]}
        ]
    }
]
```

### Edge Case Testing
- **Large Files**: Test with files >1MB to verify handling
- **Special Characters**: Test filenames with unicode, spaces, symbols
- **Deep Directories**: Test nested directory structures
- **Concurrent Access**: Simulate multiple operations on same files

## LLM Prompt
```
Please review the implementation plan in PR_Info, especially the summary and step_5.md.

I need you to implement comprehensive filesystem-specific tests for mcp-server-filesystem integration with Claude Code.

Key requirements:
1. Create `tests/integration/test_mcp_filesystem.py` with TestMCPFilesystemOperations class
2. Test all mcp-server-filesystem tools: file operations, directory ops, reference projects
3. Include advanced scenarios like file editing, batch operations, and reference project access
4. Test edge cases: large files, special characters, concurrent operations
5. Verify performance characteristics and resource usage
6. Use existing fixtures and follow established test patterns

Focus on comprehensive coverage of the mcp-server-filesystem capabilities and realistic usage scenarios that would occur in actual development workflows.

Please ensure tests cover both individual tool usage and complex multi-step workflows, with proper validation of all filesystem changes.
```

## Implementation Notes
- **Complete Tool Coverage**: Test every mcp-server-filesystem tool individually
- **Realistic Workflows**: Multi-step operations that developers would actually perform
- **Edge Case Handling**: Large files, special characters, deep directory structures
- **Reference Projects**: Test read-only access to additional codebases
- **Performance Validation**: Monitor response times and resource usage

## Success Criteria
- ✅ All mcp-server-filesystem tools work correctly with Claude Code
- ✅ Reference project functionality enables read-only access to additional directories
- ✅ File editing operations work precisely without corrupting files
- ✅ Directory operations handle complex nested structures
- ✅ Batch operations complete successfully within reasonable timeframes
- ✅ Edge cases are handled gracefully without crashes
- ✅ Performance meets acceptable thresholds for development workflows
