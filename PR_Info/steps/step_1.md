# Step 1: Create MCP Configuration Manager

## Objective
Implement a configuration manager that can programmatically set up and tear down MCP server configurations for testing, using patterns from the p_config reference project.

## WHERE
- **File**: `src/mcp_coder/mcp/config_manager.py`
- **Test File**: `tests/mcp/test_config_manager.py`
- **Module Structure**: New `mcp` package under `src/mcp_coder/`

## WHAT
### Main Functions
```python
class MCPConfigManager:
    def setup_test_mcp_server(self, project_dir: Path, server_name: str) -> dict[str, Any]
    def cleanup_test_mcp_server(self, server_name: str) -> bool
    def get_config_status(self, server_name: str) -> dict[str, Any]
    def backup_existing_config(self) -> Path | None
    def restore_config(self, backup_path: Path) -> bool
```

### Data Structures
```python
MCPConfigResult = {
    "success": bool,
    "server_name": str,
    "config_path": str,
    "backup_path": str | None,
    "error": str | None
}
```

## HOW
### Integration Points
- **Import**: `from pathlib import Path`, `import tempfile`, `import json`
- **Dependencies**: Use reference project p_config patterns for configuration logic
- **Error Handling**: Custom `MCPConfigError` exception class
- **Logging**: Use existing `mcp_coder.utils.log_utils` for structured logging

### Configuration Strategy
- Create temporary Claude Desktop configuration for testing
- Use mcp-server-filesystem as the test MCP server
- Implement proper backup/restore of existing configurations
- Handle cross-platform configuration file paths

## ALGORITHM
```
1. Detect existing Claude Desktop configuration file location
2. Create backup of current configuration (if exists)
3. Generate MCP server configuration using p_config patterns
4. Write test configuration to Claude Desktop config file
5. Validate configuration was applied successfully
```

## DATA
### Input Parameters
- `project_dir: Path` - Directory for MCP server to serve
- `server_name: str` - Unique name for test server instance

### Return Values
- **Success**: `MCPConfigResult` with success=True, paths, and server details
- **Failure**: `MCPConfigResult` with success=False and error message

## LLM Prompt
```
Please review the implementation plan in PR_Info, especially the summary and step_1.md.

I need you to implement the MCP Configuration Manager that will handle programmatic setup and cleanup of MCP server configurations for integration testing.

Key requirements:
1. Create `src/mcp_coder/mcp/config_manager.py` with the MCPConfigManager class
2. Use patterns from p_config reference project for reliable configuration handling
3. Support setup/cleanup of mcp-server-filesystem for testing
4. Handle backup/restore of existing Claude Desktop configurations
5. Include proper error handling and logging
6. Write comprehensive unit tests in `tests/mcp/test_config_manager.py`

Focus on the KISS principle - keep the configuration logic simple but robust. The goal is reliable setup/teardown of test MCP servers, not a full-featured configuration system.

Please verify your implementation by running the MCP server checks and ensure all tests pass.
```

## Implementation Notes
- **Cross-Platform**: Handle Windows/macOS/Linux Claude Desktop config paths
- **Safety First**: Always backup existing configurations before modification
- **Validation**: Verify MCP server is properly configured and accessible
- **Cleanup**: Ensure test configurations are completely removed
- **Isolation**: Each test should have a unique server name to avoid conflicts

## Success Criteria
- ✅ Can programmatically set up mcp-server-filesystem configuration
- ✅ Properly backs up and restores existing Claude Desktop configs
- ✅ Handles cross-platform configuration file paths correctly
- ✅ Includes comprehensive error handling and logging
- ✅ Unit tests achieve >90% coverage
- ✅ Integration with existing project logging and error handling
