# Step 3: Explore Test Project Setup and Cleanup

## Objective
Understand how to create controlled, isolated test environments for MCP testing. Figure out what cleanup is needed and how to ensure tests don't interfere with each other.

## WHERE
- **Implementation File**: `src/mcp_coder/mcp/test_project_manager.py` (simple utilities)
- **Test File**: `tests/mcp/test_project_manager.py`
- **Exploration Tests**: `tests/integration/test_mcp_project_setup.py`

## WHAT
### Core Utilities to Build
```python
def create_test_project(base_dir: Path, files: dict[str, str]) -> Path:
    """Create temporary test project with specified files"""

def cleanup_test_project(project_dir: Path) -> None:
    """Clean up test project and created files"""

def verify_test_files(project_dir: Path, expected_files: list[str]) -> bool:
    """Verify expected files exist in test project"""

def get_created_files_list(project_dir: Path) -> list[str]:
    """Get list of files that were created during testing"""
```

### Key Questions to Answer
- What files get created during MCP operations that need cleanup?
- How to ensure test isolation between different test runs?
- What's the best way to create temporary test environments?
- Do MCP servers cache anything that needs clearing?
- How to use pytest markers to separate MCP tests from other tests?

## HOW
### Integration Points
- **Build on Steps 1-2**: Use knowledge from operation exploration
- **File System Management**: Use `tempfile` and `pathlib` for cross-platform support
- **Test Isolation**: Ensure each test gets a clean environment with separate temporary directories
- **Cleanup Verification**: Check that cleanup actually removes all created files
- **Pytest Markers**: Use `@pytest.mark.mcp_integration` for test separation

### Exploration Strategy
- Create test projects, run MCP operations, see what gets created
- Test different cleanup approaches to find reliable method
- Experiment with file permissions and cross-platform issues
- Test concurrent access scenarios (multiple tests running)

## ALGORITHM
```
1. Create temporary directory for test project
2. Set up known files in test directory  
3. Point MCP server to test directory (manually for now)
4. Run various MCP operations and track what files are created
5. Test different cleanup strategies
6. Verify test isolation works properly
```

## DATA
### Test Project Templates
```python
BASIC_PROJECT_FILES = {
    "README.md": "# Test Project\nBasic MCP test project",
    "main.py": "print('Hello from test project')",
    "config.json": '{"name": "test", "version": "1.0"}'
}

ADVANCED_PROJECT_FILES = {
    **BASIC_PROJECT_FILES,
    "src/module.py": "def test_function(): return True",
    "tests/test_example.py": "def test_dummy(): assert True",
    "data/sample.txt": "Sample data file content"
}
```

### Cleanup Tracking
```python
class CleanupTracker:
    """Track files created during testing for cleanup verification"""
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.initial_files = set()
        self.final_files = set()
    
    def snapshot_before(self) -> None:
        """Record files before test operations"""
        
    def snapshot_after(self) -> None:
        """Record files after test operations"""
        
    def get_created_files(self) -> list[Path]:
        """Return files that were created during testing"""
```

## LLM Prompt
```
Please review the exploratory implementation plan in PR_Info, especially step_3.md.

I need you to explore test project setup and cleanup for MCP integration testing.

Key requirements:
1. Create utilities in `src/mcp_coder/mcp/test_project_manager.py` for test project management
2. Build exploration tests in `tests/integration/test_mcp_project_setup.py`
3. Test different approaches to creating isolated test environments
4. Figure out what cleanup is needed after MCP operations
5. Verify that tests don't interfere with each other
6. Set up pytest markers for MCP test isolation

This is about understanding the practical aspects of test environment management before building automation.

Please document your findings about test isolation, cleanup requirements, and any platform-specific issues.
```

## Implementation Notes
- **Cross-Platform**: Test on your current platform but consider others
- **File Permissions**: Some MCP operations might affect file permissions
- **Temporary Directories**: Use proper temporary directory management
- **Concurrent Testing**: Consider if multiple tests can run simultaneously
- **Error Scenarios**: What happens when cleanup fails?

## Success Criteria
- ✅ Can create isolated test environments with known file structures
- ✅ Understand what files/state gets created during MCP operations
- ✅ Have reliable cleanup that removes all test artifacts
- ✅ Verified that tests don't interfere with each other
- ✅ Documented any platform-specific or permission issues

## Expected Learnings
- Best practices for temporary test project creation
- What MCP server state needs to be reset between tests
- File system cleanup requirements and gotchas
- How to verify test isolation is working properly
- Cross-platform compatibility considerations for file operations

This step ensures we can build reliable, repeatable tests in the automation phase.
