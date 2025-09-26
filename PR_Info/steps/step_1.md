# Step 1: Create Personal Config Tests (TDD Foundation)

## Objective
Implement comprehensive unit tests for personal configuration functionality before writing the actual implementation, following TDD methodology.

## LLM Prompt
```
Implement unit tests for a personal configuration system as described in pr_info/steps/summary.md. 

Create tests for:
1. Platform-specific config file path resolution
2. Reading config values from TOML files
3. Handling missing files and keys gracefully

Follow the test patterns established in the existing test suite. Use pytest fixtures and mocking where appropriate to ensure tests are isolated and deterministic.
```

## WHERE
- **File**: `tests/utils/test_personal_config.py`
- **Module**: New test module in utils test package

## WHAT
Test functions to implement:
```python
def test_get_config_file_path_linux_mac()
def test_get_config_file_path_windows() 
def test_get_config_value_file_exists()
def test_get_config_value_file_missing()
def test_get_config_value_section_missing()
def test_get_config_value_key_missing()
```

## HOW
### Integration Points
- Import from `mcp_coder.utils.personal_config` (module doesn't exist yet - TDD)
- Use `pytest.fixture` for test data setup
- Use `unittest.mock.patch` for platform detection and file operations
- Follow existing test patterns from `tests/utils/`

### Test Data Setup
```python
@pytest.fixture
def sample_config_content():
    return """
[tokens]
github = "ghp_test_token_123"

[settings]
default_branch = "main"
"""
```

## ALGORITHM
Test implementation pseudocode:
```
1. Mock platform.system() for Windows/Unix path tests
2. Create temporary config files with known content
3. Test path resolution returns correct OS-specific paths
4. Test config value retrieval with various scenarios
5. Assert None returned for missing files/sections/keys
6. Verify no exceptions raised for missing resources
```

## DATA
### Test Inputs
- Mock platform types: "Windows", "Linux", "Darwin"
- Sample TOML config content with tokens and settings sections
- Various section/key combinations for testing

### Expected Outputs
- **Path resolution**: `Path` objects with correct platform-specific paths
- **Value retrieval**: String values for existing keys, None for missing
- **Error cases**: None (no exceptions) for all missing resource scenarios

## Acceptance Criteria
- [ ] All tests fail initially (no implementation exists)
- [ ] Tests cover Windows and Unix path resolution
- [ ] Tests verify TOML parsing and key lookup
- [ ] Tests handle all error cases gracefully
- [ ] Tests are isolated and use mocking for file system operations
- [ ] Test coverage includes edge cases (empty files, malformed TOML)
