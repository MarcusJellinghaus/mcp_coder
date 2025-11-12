# Step 2: Update Config Loading and Validation (TDD)

## Context
Reference: `pr_info/steps/summary.md`

This step adds support for loading and validating the new `executor_os` configuration field. Follows TDD approach: write tests first, then implement.

## Objective
1. Write tests for `executor_os` validation
2. Update `load_repo_config()` to load `executor_os` field
3. Update `validate_repo_config()` to validate `executor_os` values
4. Ensure backward compatibility (defaults to "linux")

## WHERE

### Test File
**File**: `tests/cli/commands/test_coordinator.py`

**Function**: Add new test method to existing test class

### Implementation File
**File**: `src/mcp_coder/cli/commands/coordinator.py`

**Functions to modify**:
- `load_repo_config()` (around line 240)
- `validate_repo_config()` (around line 260)

## WHAT

### Test Functions

#### `test_validate_repo_config_invalid_executor_os()`
Test that validation fails for invalid `executor_os` values.

**Signature**:
```python
def test_validate_repo_config_invalid_executor_os() -> None:
    """Test validation fails for invalid executor_os values."""
```

#### `test_validate_repo_config_valid_executor_os()`
Test that validation passes for valid `executor_os` values.

**Signature**:
```python
def test_validate_repo_config_valid_executor_os() -> None:
    """Test validation passes for valid executor_os values."""
```

#### `test_load_repo_config_defaults_executor_os()`
Test that `executor_os` defaults to "linux" when not specified.

**Signature**:
```python
def test_load_repo_config_defaults_executor_os() -> None:
    """Test executor_os defaults to 'linux' when not specified."""
```

### Implementation Functions

#### Modified: `load_repo_config()`
Load `executor_os` from config with default.

**Signature**: (unchanged)
```python
def load_repo_config(repo_name: str) -> dict[str, Optional[str]]:
```

**Returns**: Add `executor_os` to returned dict
```python
{
    "repo_url": str | None,
    "executor_test_path": str | None,
    "github_credentials_id": str | None,
    "executor_os": str  # Always present, defaults to "linux"
}
```

#### Modified: `validate_repo_config()`
Validate `executor_os` is "windows" or "linux".

**Signature**: (unchanged)
```python
def validate_repo_config(repo_name: str, config: dict[str, Optional[str]]) -> None:
```

**Raises**: `ValueError` if `executor_os` invalid

## HOW

### Integration Points

**Imports**: None needed (uses existing functions)

**Config Access**: Use existing `get_config_value()` function

**Error Format**: Follow existing error message pattern:
```
Config file: {path} - section [{section}] - value for field '{field}' invalid. Must be 'windows' or 'linux'
```

## ALGORITHM

### `load_repo_config()` Modification
```
1. Load existing fields (repo_url, executor_test_path, github_credentials_id)
2. Load executor_os from config
3. If executor_os is None, default to "linux"
4. Return dict with all four fields
```

### `validate_repo_config()` Modification
```
1. Validate existing required fields (current logic)
2. Get executor_os from config (always present after load)
3. If executor_os not in ["windows", "linux"]:
   - Build error message with config path and section
   - Raise ValueError
4. Continue with existing validation
```

### Test Algorithm
```
# Test invalid values
1. Create config dict with executor_os = "invalid"
2. Call validate_repo_config()
3. Assert ValueError raised with correct message

# Test valid values
1. For each valid value ("windows", "linux"):
   - Create config dict with that executor_os
   - Call validate_repo_config()
   - Assert no exception raised

# Test default
1. Mock get_config_value to return None for executor_os
2. Call load_repo_config()
3. Assert returned dict has executor_os = "linux"
```

## DATA

### Config Dict Structure (Updated)
```python
{
    "repo_url": "https://github.com/user/repo.git",
    "executor_test_path": "Tests/executor-test",
    "github_credentials_id": "github-pat",
    "executor_os": "linux"  # NEW: Always present, defaults to "linux"
}
```

### Valid Values
- `"windows"` - Use Windows batch script templates
- `"linux"` - Use Linux bash script templates (default)

### Error Message Format
```
Config file: /home/user/.config/mcp_coder/config.toml - section [coordinator.repos.my_repo] - value for field 'executor_os' invalid. Must be 'windows' or 'linux'
```

## Implementation Steps

### Part 1: Write Tests (TDD)

1. Open `tests/cli/commands/test_coordinator.py`
2. Add test function `test_validate_repo_config_invalid_executor_os`:
   ```python
   def test_validate_repo_config_invalid_executor_os():
       """Test validation fails for invalid executor_os values."""
       from mcp_coder.cli.commands.coordinator import validate_repo_config
       
       config = {
           "repo_url": "https://github.com/test/repo.git",
           "executor_test_path": "Tests/test",
           "github_credentials_id": "cred-id",
           "executor_os": "macos",  # Invalid value
       }
       
       with pytest.raises(ValueError, match="executor_os.*invalid.*windows.*linux"):
           validate_repo_config("test_repo", config)
   ```

3. Add test function `test_validate_repo_config_valid_executor_os`:
   ```python
   def test_validate_repo_config_valid_executor_os():
       """Test validation passes for valid executor_os values."""
       from mcp_coder.cli.commands.coordinator import validate_repo_config
       
       for os_value in ["windows", "linux"]:
           config = {
               "repo_url": "https://github.com/test/repo.git",
               "executor_test_path": "Tests/test",
               "github_credentials_id": "cred-id",
               "executor_os": os_value,
           }
           
           # Should not raise
           validate_repo_config("test_repo", config)
   ```

4. Add test function `test_load_repo_config_defaults_executor_os`:
   ```python
   def test_load_repo_config_defaults_executor_os(monkeypatch):
       """Test executor_os defaults to 'linux' when not specified."""
       from mcp_coder.cli.commands.coordinator import load_repo_config
       
       def mock_get_config(section, key):
           values = {
               "repo_url": "https://github.com/test/repo.git",
               "executor_test_path": "Tests/test",
               "github_credentials_id": "cred-id",
               "executor_os": None,  # Not in config
           }
           return values.get(key)
       
       monkeypatch.setattr(
           "mcp_coder.cli.commands.coordinator.get_config_value",
           mock_get_config
       )
       
       config = load_repo_config("test_repo")
       assert config["executor_os"] == "linux"
   ```

5. Run tests (should fail):
   ```bash
   mcp__code-checker__run_pytest_check(
       extra_args=["-n", "auto", "-m", "not git_integration and not claude_integration and not formatter_integration and not github_integration", "-k", "test_validate_repo_config or test_load_repo_config"]
   )
   ```

### Part 2: Implement Functionality

6. Open `src/mcp_coder/cli/commands/coordinator.py`

7. Update `load_repo_config()`:
   ```python
   def load_repo_config(repo_name: str) -> dict[str, Optional[str]]:
       """Load repository configuration from config file.
       
       Args:
           repo_name: Name of repository to load (e.g., "mcp_coder")
       
       Returns:
           Dictionary with repo_url, executor_test_path, github_credentials_id, executor_os
           Values may be None except executor_os which defaults to "linux"
       """
       section = f"coordinator.repos.{repo_name}"
       
       repo_url = get_config_value(section, "repo_url")
       executor_test_path = get_config_value(section, "executor_test_path")
       github_credentials_id = get_config_value(section, "github_credentials_id")
       executor_os = get_config_value(section, "executor_os") or "linux"  # NEW: Default to linux
       
       return {
           "repo_url": repo_url,
           "executor_test_path": executor_test_path,
           "github_credentials_id": github_credentials_id,
           "executor_os": executor_os,  # NEW: Always present
       }
   ```

8. Update `validate_repo_config()`:
   ```python
   def validate_repo_config(repo_name: str, config: dict[str, Optional[str]]) -> None:
       """Validate repository configuration has all required fields.
       
       Args:
           repo_name: Name of repository being validated
           config: Repository configuration dict with possibly None values
       
       Raises:
           ValueError: If any required fields are missing or invalid
       """
       # Validate required fields (existing logic)
       required_fields = ["repo_url", "executor_test_path", "github_credentials_id"]
       missing_fields = []
       
       for field in required_fields:
           if field not in config or not config[field]:
               missing_fields.append(field)
       
       if missing_fields:
           config_path = get_config_file_path()
           section_name = f"coordinator.repos.{repo_name}"
           
           if len(missing_fields) == 1:
               field = missing_fields[0]
               error_msg = (
                   f"Config file: {config_path} - "
                   f"section [{section_name}] - "
                   f"value for field '{field}' missing"
               )
           else:
               fields_str = "', '".join(missing_fields)
               error_msg = (
                   f"Config file: {config_path} - "
                   f"section [{section_name}] - "
                   f"values for fields '{fields_str}' missing"
               )
           
           raise ValueError(error_msg)
       
       # NEW: Validate executor_os field
       executor_os = config.get("executor_os", "linux")
       if executor_os not in ["windows", "linux"]:
           config_path = get_config_file_path()
           section_name = f"coordinator.repos.{repo_name}"
           error_msg = (
               f"Config file: {config_path} - "
               f"section [{section_name}] - "
               f"value for field 'executor_os' invalid. Must be 'windows' or 'linux'"
           )
           raise ValueError(error_msg)
   ```

9. Run tests again (should pass):
   ```bash
   mcp__code-checker__run_pytest_check(
       extra_args=["-n", "auto", "-m", "not git_integration and not claude_integration and not formatter_integration and not github_integration", "-k", "test_validate_repo_config or test_load_repo_config"]
   )
   ```

10. Run all code quality checks:
    ```bash
    mcp__code-checker__run_all_checks(
        extra_args=["-n", "auto", "-m", "not git_integration and not claude_integration and not formatter_integration and not github_integration"]
    )
    ```

## Testing

### Test Cases

1. **Invalid executor_os**: Reject values other than "windows" or "linux"
2. **Valid windows**: Accept "windows"
3. **Valid linux**: Accept "linux"
4. **Default value**: Default to "linux" when not specified
5. **Case sensitivity**: Ensure case-sensitive validation

### Expected Results

- Tests should fail initially (TDD approach)
- Tests should pass after implementation
- All pylint, pytest, mypy checks should pass

## LLM Prompt for Implementation

```
I need to implement Step 2 of the Windows support implementation using TDD.

Context:
- Read pr_info/steps/summary.md for overall architecture
- Read pr_info/steps/step_2.md for detailed requirements

Task:
Follow TDD approach to add executor_os config field support:

Part 1 - Write Tests First:
1. Add test_validate_repo_config_invalid_executor_os to tests/cli/commands/test_coordinator.py
2. Add test_validate_repo_config_valid_executor_os
3. Add test_load_repo_config_defaults_executor_os
4. Run tests (should fail) using mcp__code-checker__run_pytest_check

Part 2 - Implement Functionality:
5. Update load_repo_config() in src/mcp_coder/cli/commands/coordinator.py to load executor_os with default "linux"
6. Update validate_repo_config() to validate executor_os is "windows" or "linux"
7. Run tests again (should pass)
8. Run all quality checks using mcp__code-checker__run_all_checks

Requirements:
- Follow exact test implementations from step_2.md
- Use existing error message format pattern
- Ensure backward compatibility (default to "linux")
- All quality checks must pass

After implementation:
- Report test results
- Fix any issues found
```
