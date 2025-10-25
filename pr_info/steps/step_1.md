# Step 1: Config Template Infrastructure (TDD)

## Overview
Implement config file template creation functionality to auto-generate configuration structure on first run. This enables users to easily set up Jenkins and repository configurations.

## LLM Prompt
```
You are implementing Step 1 of the "mcp-coder coordinator test" feature.

Read pr_info/steps/summary.md for context.

Your task: Implement config template auto-creation functionality following TDD.

Requirements:
1. Write tests FIRST in tests/utils/test_user_config.py
2. Add config template helper to src/mcp_coder/utils/user_config.py
3. Ensure tests pass
4. Run code quality checks

Follow the specifications in this step file exactly.
```

## Phase 1A: Write Tests First (TDD)

### WHERE
File: `tests/utils/test_user_config.py`

Add new test class at the end of the file.

### WHAT
Test class and methods:

```python
class TestCreateDefaultConfig:
    """Tests for create_default_config function."""
    
    def test_create_default_config_creates_directory_and_file(tmp_path: Path) -> None:
        """Test that config directory and file are created."""
        
    def test_create_default_config_returns_true_on_success(tmp_path: Path) -> None:
        """Test successful creation returns True."""
        
    def test_create_default_config_returns_false_if_exists(tmp_path: Path) -> None:
        """Test that existing config returns False (no overwrite)."""
        
    def test_create_default_config_content_has_all_sections(tmp_path: Path) -> None:
        """Test that created config has all required sections."""
        
    def test_create_default_config_content_has_example_repos(tmp_path: Path) -> None:
        """Test that config includes example repository configurations."""
        
    def test_create_default_config_handles_permission_error(tmp_path: Path) -> None:
        """Test graceful handling of permission errors."""
```

### HOW
Integration points:
- Import `create_default_config` from `mcp_coder.utils.user_config`
- Use pytest's `tmp_path` fixture for isolated testing
- Use `monkeypatch` to override `get_config_file_path()` for testing
- Verify TOML structure using `tomllib.load()`

### ALGORITHM (Test Logic)
```
1. Mock get_config_file_path() to return tmp_path location
2. Call create_default_config()
3. Verify directory created
4. Verify file exists
5. Load and parse TOML content
6. Assert all sections present: [jenkins], [coordinator.repos.mcp_coder], etc.
```

### DATA
Test assertions should verify:
- Function returns `bool` (True on success, False if exists)
- Created file path: `Path` object
- TOML content has sections: `jenkins`, `coordinator.repos.mcp_coder`, `coordinator.repos.mcp_server_filesystem`
- Each repo has fields: `repo_url`, `test_job_path`, `github_credentials_id`

### Test Example Structure
```python
def test_create_default_config_creates_directory_and_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that config directory and file are created."""
    # Setup
    config_dir = tmp_path / ".mcp_coder"
    config_file = config_dir / "config.toml"
    
    # Mock get_config_file_path to return test location
    monkeypatch.setattr(
        "mcp_coder.utils.user_config.get_config_file_path",
        lambda: config_file
    )
    
    # Execute
    result = create_default_config()
    
    # Verify
    assert result is True
    assert config_dir.exists()
    assert config_file.exists()
    assert config_file.is_file()
```

## Phase 1B: Implement Functionality

### WHERE
File: `src/mcp_coder/utils/user_config.py`

Add at the end of the file, before the module ends.

### WHAT
New function signature:

```python
@log_function_call
def create_default_config() -> bool:
    """Create default configuration file with template content.
    
    Creates ~/.mcp_coder/config.toml with example configuration
    including Jenkins settings and repository examples.
    
    Returns:
        True if config was created, False if it already exists
        
    Raises:
        OSError: If directory/file creation fails due to permissions
    """
```

### HOW
Integration points:
- Use existing `get_config_file_path()` function
- Add `@log_function_call` decorator for consistency
- Import needed: (already available in file)
  - `from pathlib import Path`
  - `from typing import Optional`

### ALGORITHM
```
1. Get config file path using get_config_file_path()
2. If file already exists, return False (no overwrite)
3. Create parent directory with parents=True, exist_ok=True
4. Define TOML template string with all sections
5. Write template to file
6. Return True
```

### DATA

**Input**: None

**Output**: `bool`
- `True` - Config created successfully
- `False` - Config already exists (no action taken)

**Raises**: `OSError` if directory/file creation fails

**TOML Template Content**:
```toml
# MCP Coder Configuration
# Update with your actual credentials and repository information

[jenkins]
# Jenkins server configuration
# Environment variables (higher priority): JENKINS_URL, JENKINS_USER, JENKINS_TOKEN
server_url = "https://jenkins.example.com:8080"
username = "your-jenkins-username"
api_token = "your-jenkins-api-token"

# Coordinator test repositories
# Add your repositories here following this pattern

[coordinator.repos.mcp_coder]
repo_url = "https://github.com/your-org/mcp_coder.git"
test_job_path = "MCP_Coder/mcp-coder-test-job"
github_credentials_id = "github-general-pat"

[coordinator.repos.mcp_server_filesystem]
repo_url = "https://github.com/your-org/mcp_server_filesystem.git"
test_job_path = "MCP_Filesystem/test-job"
github_credentials_id = "github-general-pat"

# Add more repositories as needed:
# [coordinator.repos.your_repo_name]
# repo_url = "https://github.com/your-org/your_repo.git"
# test_job_path = "Folder/job-name"
# github_credentials_id = "github-credentials-id"
```

### Implementation Skeleton

```python
@log_function_call
def create_default_config() -> bool:
    """Create default configuration file with template content."""
    config_path = get_config_file_path()
    
    # Don't overwrite existing config
    if config_path.exists():
        return False
    
    # Create parent directory
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Define template content
    template = """# MCP Coder Configuration
# Update with your actual credentials and repository information

[jenkins]
# Jenkins server configuration
# Environment variables (higher priority): JENKINS_URL, JENKINS_USER, JENKINS_TOKEN
server_url = "https://jenkins.example.com:8080"
username = "your-jenkins-username"
api_token = "your-jenkins-api-token"

# ... rest of template ...
"""
    
    # Write template to file
    config_path.write_text(template, encoding="utf-8")
    
    return True
```

## Phase 1C: Verify Implementation

### Manual Verification Steps
1. Run tests: `pytest tests/utils/test_user_config.py::TestCreateDefaultConfig -v`
2. Verify all tests pass
3. Check test coverage for new function

### Expected Test Output
```
tests/utils/test_user_config.py::TestCreateDefaultConfig::test_create_default_config_creates_directory_and_file PASSED
tests/utils/test_user_config.py::TestCreateDefaultConfig::test_create_default_config_returns_true_on_success PASSED
tests/utils/test_user_config.py::TestCreateDefaultConfig::test_create_default_config_returns_false_if_exists PASSED
tests/utils/test_user_config.py::TestCreateDefaultConfig::test_create_default_config_content_has_all_sections PASSED
tests/utils/test_user_config.py::TestCreateDefaultConfig::test_create_default_config_content_has_example_repos PASSED
tests/utils/test_user_config.py::TestCreateDefaultConfig::test_create_default_config_handles_permission_error PASSED

6 passed
```

## Phase 1D: Code Quality Checks

Run mandatory code quality checks:

```python
# Pylint
mcp__code-checker__run_pylint_check()

# Pytest (fast unit tests)
mcp__code-checker__run_pytest_check(
    extra_args=["-n", "auto", "-m", "not jenkins_integration and not git_integration and not claude_integration and not formatter_integration and not github_integration"]
)

# Mypy
mcp__code-checker__run_mypy_check()
```

All checks must pass before proceeding to Step 2.

## Success Criteria

- ✅ All 6 tests pass
- ✅ Function creates directory if it doesn't exist
- ✅ Function creates config file with template
- ✅ Function doesn't overwrite existing config
- ✅ Template includes all required sections
- ✅ Template includes example repositories
- ✅ Pylint: No errors
- ✅ Pytest: All tests pass
- ✅ Mypy: No type errors

## Files Modified

### New Code:
- `tests/utils/test_user_config.py` - Add `TestCreateDefaultConfig` class (~80-100 lines)
- `src/mcp_coder/utils/user_config.py` - Add `create_default_config()` function (~40-50 lines)

### Total Lines: ~120-150 lines

## Next Step
After all checks pass, proceed to **Step 2: Repository Config Validation**.
