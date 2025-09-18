# Step 3: Create MCP Test Utilities

## Objective
Implement utility functions and fixtures to support MCP integration testing, including test data generation, temporary project setup, and common assertion helpers.

## WHERE
- **File**: `src/mcp_coder/mcp/test_utilities.py`
- **Test File**: `tests/mcp/test_utilities.py`
- **Fixtures**: `tests/integration/conftest.py` (pytest fixtures)

## WHAT
### Main Functions
```python
class MCPTestUtilities:
    def create_test_project(self, temp_dir: Path, files: dict[str, str]) -> Path
    def generate_test_files(self) -> dict[str, str]
    def cleanup_test_files(self, project_dir: Path, created_files: list[str]) -> None
    def wait_for_mcp_server(self, timeout: int = 30) -> bool
    def assert_file_operations_occurred(self, project_dir: Path, operations: list[dict]) -> None

# Pytest fixtures for integration tests
@pytest.fixture
def test_project_with_files() -> Iterator[Path]:
    """Create temporary project with test files"""

@pytest.fixture  
def mcp_config_manager() -> Iterator[MCPConfigManager]:
    """Pre-configured MCP config manager with cleanup"""

@pytest.fixture
def mcp_session_validator() -> MCPSessionValidator:
    """Session validator instance"""
```

### Data Structures
```python
TestFileSet = {
    "README.md": "# Test Project\n\nMCP integration test project",
    "main.py": "print('Hello, MCP integration!')",
    "data.json": '{"test": true, "integration": "mcp"}',
    "config.txt": "test_mode=true\nverbose=false"
}

FileOperation = {
    "type": str,  # "create", "read", "update", "delete"
    "filename": str,
    "expected_content": str | None,
    "verify_exists": bool
}
```

## HOW
### Integration Points
- **Pytest Integration**: Use `@pytest.fixture` decorators for test setup
- **Temporary Files**: Use `tempfile.TemporaryDirectory()` for isolated test environments
- **Path Handling**: Use `pathlib.Path` for cross-platform compatibility
- **Cleanup**: Ensure all temporary resources are properly cleaned up

### Test Data Strategy
- Generate realistic test files for various scenarios
- Include different file types (text, JSON, Python, etc.)
- Create predictable content for verification
- Support custom file sets for specific test cases

## ALGORITHM
```
1. Create temporary directory for test project
2. Generate or use provided test files
3. Set up test file structure in temporary directory
4. Provide cleanup utilities for test teardown
5. Include assertion helpers for common validation tasks
```

## DATA
### Input Parameters
- `temp_dir: Path` - Base temporary directory
- `files: dict[str, str]` - Filename to content mapping
- `operations: list[dict]` - Expected file operations to verify

### Return Values
- **Test Project Path**: `Path` to created test project directory
- **File List**: List of created filenames for cleanup
- **Success Indicators**: Boolean results for setup/cleanup operations

## LLM Prompt
```
Please review the implementation plan in PR_Info, especially the summary and step_3.md.

I need you to implement MCP Test Utilities that provide helper functions and pytest fixtures for MCP integration testing.

Key requirements:
1. Create `src/mcp_coder/mcp/test_utilities.py` with the MCPTestUtilities class
2. Generate realistic test file sets for various testing scenarios
3. Implement pytest fixtures in `tests/integration/conftest.py` for test setup
4. Include utilities for creating temporary projects and cleaning up
5. Provide assertion helpers for common MCP integration validations
6. Write unit tests in `tests/mcp/test_utilities.py`

Focus on making integration tests easy to write and maintain. The utilities should handle the repetitive parts of test setup/cleanup and provide clear assertion helpers.

Please verify your implementation works with the existing pytest configuration and integrates well with the MCP config manager and session validator from previous steps.
```

## Implementation Notes
- **Pytest Integration**: Work with existing pytest configuration and markers
- **Cross-Platform**: Handle Windows/macOS/Linux path differences correctly
- **Resource Management**: Ensure temporary files and directories are cleaned up
- **Realistic Data**: Generate test files that represent real-world usage patterns
- **Flexibility**: Support custom test scenarios while providing sensible defaults

## Success Criteria
- ✅ Generates comprehensive test file sets for various scenarios
- ✅ Creates isolated temporary test environments
- ✅ Provides easy-to-use pytest fixtures for integration tests
- ✅ Includes helpful assertion utilities for MCP validation
- ✅ Properly cleans up all temporary resources
- ✅ Integrates seamlessly with existing pytest configuration
