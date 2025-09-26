# Step 1: Core Implementation with Essential Tests

## Objective
Implement the personal configuration module with essential, focused tests following practical TDD approach.

## LLM Prompt
```
Implement the personal configuration system as described in pr_info/steps/summary.md with essential testing.

Implement core functionality:
1. Personal config module with platform-specific path resolution
2. TOML config value reading with graceful error handling
3. Essential unit tests covering practical scenarios

Follow TDD principles but focus on essential test coverage. Use pytest fixtures and mocking for reliable, isolated tests.
```

## WHERE
- **Files**: 
  - `src/mcp_coder/utils/personal_config.py` (implementation)
  - `tests/utils/test_personal_config.py` (essential tests)

## WHAT
Core functions to implement:
```python
# Implementation
def get_config_file_path() -> Path
def get_config_value(section: str, key: str) -> Optional[str]

# Essential tests
def test_get_config_file_path_platform()
def test_get_config_value_success()
def test_get_config_value_missing_cases()
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
- [ ] Core implementation completed
- [ ] Essential tests pass (path resolution, config reading, error handling)
- [ ] Tests are isolated and use appropriate mocking
- [ ] Implementation uses `tomllib` (Python 3.11+)
- [ ] All functions handle missing resources gracefully (return None)
- [ ] Code follows project patterns and style
