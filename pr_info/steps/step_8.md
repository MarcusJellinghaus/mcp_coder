# Step 8: Testing Strategy

## Context
Read `pr_info/steps/summary.md` for full context. Unit tests for env_vars threading and integration test extension.

## WHERE

**Modified file:**
- `tests/llm/providers/claude/test_claude_integration.py` (extend existing)

## WHAT

### Unit Tests (with mocking)

Add unit tests to existing test files to verify env_vars threading:

**In existing test files (Steps 1-6):**
- `tests/llm/test_env.py` - Test `prepare_llm_environment()` function
- `tests/llm/test_interface.py` - Mock env_vars passed to providers
- `tests/llm/providers/claude/test_claude_code_cli.py` - Mock env_vars passed to subprocess
- `tests/llm/providers/claude/test_claude_code_api.py` - Mock env_vars passed to SDK
- `tests/workflows/implement/test_core.py` - Mock env preparation in workflow
- `tests/utils/test_commit_operations.py` - Mock env preparation in commit
- `tests/cli/commands/test_prompt.py` - Mock graceful error handling

### Integration Test (real Claude Code calls)

**In `test_claude_integration.py`:**

```python
@pytest.mark.claude_cli_integration
def test_env_vars_propagation():
    """Verify env_vars propagate to Claude Code in both CLI and API methods.
    
    This is a real integration test that makes actual API calls to verify
    environment variables are correctly set and accessible.
    """
```

## HOW

**Test strategy:**
- **Unit tests**: Mock LLM calls, verify env_vars parameter threading
- **Integration test**: Real Claude Code call to verify env_vars actually reach subprocess/SDK
- Test both CLI and API methods in integration test
- Unit tests cover error paths (no venv, graceful degradation)

## ALGORITHM

```
Unit tests (mocked):
1. Mock prepare_llm_environment() in each layer
2. Verify env_vars parameter passed through call chain
3. Test error handling (RuntimeError, graceful degradation)

Integration test (real):
1. Call ask_llm with env_vars parameter
2. Make real Claude Code call (CLI and API)
3. Verify successful execution (env vars accessible to MCP servers)
```

## DATA

**Unit test example (mocked):**
```python
@patch('mcp_coder.llm.env.prepare_llm_environment')
def test_ask_llm_with_env_vars(mock_prepare):
    mock_prepare.return_value = {
        'MCP_CODER_PROJECT_DIR': '/test/path',
        'MCP_CODER_VENV_DIR': '/test/path/.venv'
    }
    # Verify env_vars passed through
```

**Integration test (real):**
```python
def test_env_vars_propagation():
    # Test CLI method
    result_cli = ask_llm(
        "Test question",
        method="cli",
        timeout=60
    )
    assert result_cli  # Successful execution means env_vars worked
    
    # Test API method
    result_api = ask_llm(
        "Test question",
        method="api",
        timeout=60
    )
    assert result_api  # Successful execution means env_vars worked
```

## Test Coverage

**Coverage:**
1. Unit tests: Each layer verified in isolation with mocks (Steps 1-6)
2. Integration test: Full flow verification with real Claude Code
3. Both CLI and API methods tested
4. Error handling: RuntimeError propagation and graceful degradation

## LLM Prompt

```
Context: Read pr_info/steps/summary.md and pr_info/steps/step_8.md

Task: Complete testing for environment variable feature.

1. Verify unit tests added in Steps 1-6 cover env_vars threading with mocks
2. Extend tests/llm/providers/claude/test_claude_integration.py:
   - Add test_env_vars_propagation()
   - Test both CLI and API methods
   - Make real Claude Code calls to verify env_vars work end-to-end
   - Verify MCP servers can access environment variables

Test strategy:
- Unit tests (mocked): Already added in each step
- Integration test (real): One focused test in test_claude_integration.py
- Verify both methods work with actual Claude Code execution

Run all tests to verify complete implementation.
```
