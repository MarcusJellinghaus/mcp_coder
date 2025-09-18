# Step 4: Implement Core MCP Integration Tests

## Objective
Create comprehensive integration tests that verify Claude Code API can successfully connect to and use MCP servers, focusing on filesystem operations with mcp-server-filesystem.

## WHERE
- **File**: `tests/integration/test_mcp_integration.py`
- **Supporting File**: `tests/integration/__init__.py`
- **Configuration**: Update `tests/integration/conftest.py` with MCP-specific fixtures

## WHAT
### Main Test Functions
```python
class TestMCPIntegration:
    def test_mcp_server_connection(self, mcp_config_manager, test_project_with_files)
    def test_file_list_operation(self, mcp_config_manager, test_project_with_files)
    def test_file_read_operation(self, mcp_config_manager, test_project_with_files) 
    def test_file_create_operation(self, mcp_config_manager, test_project_with_files)
    def test_file_update_operation(self, mcp_config_manager, test_project_with_files)
    def test_multiple_operations_session(self, mcp_config_manager, test_project_with_files)
    def test_mcp_session_timeout_handling(self, mcp_config_manager, test_project_with_files)
    def test_mcp_error_handling(self, mcp_config_manager, test_project_with_files)
```

### Test Categories
- **Connection Tests**: Verify MCP server connection and session establishment
- **Basic Operations**: Test individual file operations (list, read, create, update)
- **Complex Workflows**: Multi-step operations within single Claude Code session
- **Error Scenarios**: Invalid requests, server unavailable, timeout handling
- **Performance Tests**: Measure response times and resource usage

## HOW
### Integration Points
- **Claude Code API**: Use `ask_claude_code_api_detailed_sync()` for MCP integration
- **Fixtures**: Use MCP config manager and test utilities from previous steps
- **Validation**: Use session validator to verify MCP tool usage
- **Pytest Markers**: Use `@pytest.mark.claude_integration` for MCP tests

### Test Strategy
- Each test sets up MCP server, runs operations, validates results, cleans up
- Use realistic prompts that would naturally trigger MCP tools
- Verify both response content and actual file system changes
- Include timeout testing with configurable limits (30s, 5min, 1hr)

## ALGORITHM
```
1. Set up MCP server configuration for test project
2. Send Claude Code API request with MCP-triggering prompt
3. Wait for response with appropriate timeout
4. Validate response shows MCP tool usage
5. Verify expected file operations actually occurred
```

## DATA
### Test Scenarios
```python
FILE_OPERATIONS_TESTS = [
    {
        "name": "list_files",
        "prompt": "Please list all files in the current directory",
        "expected_tools": ["list_directory"],
        "verify_response_contains": ["README.md", "main.py"]
    },
    {
        "name": "read_file",
        "prompt": "Please read the contents of README.md", 
        "expected_tools": ["read_file"],
        "verify_response_contains": ["Test Project"]
    },
    {
        "name": "create_file",
        "prompt": "Create a file called test_output.txt with content 'MCP Test Success'",
        "expected_tools": ["save_file"],
        "verify_file_created": "test_output.txt"
    }
]
```

### Timeout Configuration
- **Quick Operations**: 30 seconds (file list, read)
- **Medium Operations**: 5 minutes (file create, update)  
- **Complex Operations**: 1 hour (multi-step workflows)

## LLM Prompt
```
Please review the implementation plan in PR_Info, especially the summary and step_4.md.

I need you to implement comprehensive MCP integration tests that verify Claude Code API works correctly with MCP servers.

Key requirements:
1. Create `tests/integration/test_mcp_integration.py` with the TestMCPIntegration class
2. Test basic MCP filesystem operations: list, read, create, update files
3. Verify MCP server connection and tool usage in Claude Code responses
4. Include timeout handling and error scenario testing
5. Use fixtures from previous steps for setup and validation
6. Follow existing pytest patterns and use claude_integration marker

The tests should use realistic prompts that naturally trigger MCP tools and verify both the response content and actual file system changes occurred.

Please ensure tests are isolated, repeatable, and include proper cleanup. Verify the implementation works with the MCP configuration manager and session validator from earlier steps.
```

## Implementation Notes
- **Realistic Prompts**: Use natural language that would trigger MCP tools
- **Complete Validation**: Check both Claude responses and actual file changes
- **Test Isolation**: Each test should be independent and repeatable
- **Timeout Handling**: Progressive timeout strategy based on operation complexity
- **Error Scenarios**: Test server unavailable, invalid requests, network issues

## Success Criteria
- ✅ Successfully connects to MCP server and establishes session
- ✅ File operations work correctly through MCP tools
- ✅ Claude Code responses show evidence of MCP tool usage
- ✅ Actual file system changes match expected operations
- ✅ Timeout handling works for different operation types
- ✅ Error scenarios are handled gracefully with clear messages
- ✅ Tests are isolated, repeatable, and properly clean up resources
