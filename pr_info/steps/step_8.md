# Step 8: Integration Testing

## Context
Read `pr_info/steps/summary.md` for full context. End-to-end testing of environment variable flow.

## WHERE

**New file:**
- `tests/integration/test_env_vars_integration.py`

## WHAT

### Integration Test Scenarios

```python
def test_implement_workflow_with_env_vars():
    """Test full implement workflow sets env vars correctly."""

def test_commit_auto_with_env_vars():
    """Test commit auto workflow sets env vars correctly."""

def test_prompt_command_with_env_vars():
    """Test prompt command sets env vars correctly."""

def test_env_vars_propagate_to_subprocess():
    """Verify env vars reach subprocess in CLI method."""

def test_env_vars_propagate_to_sdk():
    """Verify env vars reach SDK in API method."""

def test_no_venv_error_handling():
    """Test error handling when venv not found."""
```

## HOW

**Test strategy:**
- Use real project directory structure
- Mock LLM responses
- Verify env vars set correctly at subprocess/SDK level
- Test both CLI and API methods
- Test error paths (no venv)

## ALGORITHM

```
1. Setup test project with venv
2. Call CLI commands (implement/commit/prompt)
3. Mock LLM calls and capture env vars
4. Assert MCP_CODER_* vars set correctly
5. Test error cases (no venv, etc.)
```

## DATA

**Expected env vars in subprocess:**
```python
{
    'MCP_CODER_PROJECT_DIR': '/absolute/path/to/project',
    'MCP_CODER_VENV_DIR': '/absolute/path/to/project/.venv',
    # Plus all inherited os.environ variables
}
```

## Test Coverage

**Full flow tests:**
1. CLI command → workflow → LLM interface → provider → subprocess (env vars present)
2. Error handling when venv missing
3. Both CLI and API methods
4. Env vars in correct format (absolute, OS-native)

## LLM Prompt

```
Context: Read pr_info/steps/summary.md and pr_info/steps/step_8.md

Task: Create integration tests for environment variable flow.

Create tests/integration/test_env_vars_integration.py with 6 test cases:
1. test_implement_workflow_with_env_vars - Full implement flow
2. test_commit_auto_with_env_vars - Full commit auto flow
3. test_prompt_command_with_env_vars - Prompt command flow
4. test_env_vars_propagate_to_subprocess - CLI method verification
5. test_env_vars_propagate_to_sdk - API method verification
6. test_no_venv_error_handling - Error handling

Test strategy:
- Setup real project directory structure with venv
- Mock LLM responses to avoid actual API calls
- Capture and verify env vars at subprocess/SDK level
- Test both CLI and API methods
- Verify error handling

Run all tests to verify complete implementation.
```
