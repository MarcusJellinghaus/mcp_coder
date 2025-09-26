# Step 3: Integration Tests and Documentation

## Objective
Add integration tests to verify the personal config system works end-to-end and update project documentation with usage examples.

## LLM Prompt
```
Create integration tests and documentation for the personal configuration system implemented in steps 1-2. Reference pr_info/steps/summary.md for context.

Tasks:
1. Add integration tests that create real config files and test the full workflow
2. Update project documentation with config file format and usage examples  
3. Ensure the new functionality is properly documented for future developers

Follow existing project patterns for integration tests and documentation.
```

## WHERE
- **Integration Tests**: `tests/utils/test_personal_config_integration.py`
- **Documentation**: Add section to `README.md` or create `docs/personal_config.md`

## WHAT
### Integration Test Functions
```python
def test_real_config_file_workflow(tmp_path)
def test_config_file_permissions() 
def test_config_directory_creation()
```

### Documentation Sections
- Configuration file format specification
- Setup instructions for users
- Usage examples for developers
- Security considerations

## HOW
### Integration Points
- **Test fixtures**: Use `tmp_path` for real file operations
- **File operations**: Create actual TOML files and test reading
- **Documentation**: Follow existing README.md style and structure

### Test Setup
```python
@pytest.fixture
def real_config_file(tmp_path):
    """Create a real config file for integration testing."""
    config_dir = tmp_path / ".config" / "mcp-coder"
    config_dir.mkdir(parents=True)
    config_file = config_dir / "config.toml"
    # Write real TOML content
```

## ALGORITHM
### Integration Test Flow
```
1. Create temporary directory structure mimicking user config
2. Write real TOML config file with test data
3. Call actual personal_config functions (no mocking)
4. Verify correct values are returned
5. Test error cases with malformed files
6. Clean up temporary files
```

### Documentation Structure
```
1. Add "Personal Configuration" section to README
2. Document config file location by OS
3. Show TOML format example  
4. Provide usage examples for developers
5. List security best practices
```

## DATA
### Test Data
```toml
# Real TOML content for integration tests
[tokens]
github = "ghp_integration_test_token"
another_service = "token_xyz"

[settings]
default_branch = "main"
editor = "vscode"
```

### Documentation Examples
- Sample config file contents
- Code examples showing how to use `get_config_value()`
- Platform-specific file paths for user reference

## Implementation Requirements
- **Integration tests** run against real file system (not mocked)
- **Documentation** is clear and actionable for end users
- **Examples** show both success and failure cases
- **Security notes** explain token handling best practices

## File Structure After Step 3
```
tests/utils/
├── test_personal_config.py              # Unit tests (Step 1)
├── test_personal_config_integration.py  # Integration tests (Step 3)
src/mcp_coder/utils/
├── personal_config.py                   # Implementation (Step 2)
docs/ or README.md                       # Documentation (Step 3)
```

## Acceptance Criteria
- [ ] Integration tests pass with real file operations
- [ ] Documentation clearly explains config file setup
- [ ] Usage examples are accurate and helpful
- [ ] Security considerations are documented
- [ ] File permissions and directory creation work correctly
- [ ] Documentation follows project's existing style
- [ ] New functionality is discoverable by future developers
