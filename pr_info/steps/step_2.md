# Step 2: Update CLI Provider with Environment Variables

## Context
Read `pr_info/steps/summary.md` for full context. This step adds `env_vars` parameter to CLI provider.

## WHERE

**Modified files:**
- `src/mcp_coder/llm/providers/claude/claude_code_cli.py`
- `tests/llm/providers/claude/test_claude_code_cli.py`

## WHAT

### Updated Function Signature
```python
def ask_claude_code_cli(
    question: str,
    session_id: str | None = None,
    timeout: int = 30,
    env_vars: dict[str, str] | None = None,  # NEW
) -> LLMResponseDict:
```

## HOW

**Integration:**
- Pass `env_vars` to `CommandOptions` when creating options
- Existing `subprocess_runner.execute_subprocess()` already merges env vars

**Code change location:**
```python
# Around line 175 in ask_claude_code_cli()
options = CommandOptions(
    timeout_seconds=timeout,
    input_data=question,
    env=env_vars  # NEW: Add this parameter
)
```

## ALGORITHM

```
1. Accept env_vars parameter (defaults to None)
2. Create CommandOptions with env=env_vars
3. Pass to execute_subprocess() (already handles merging)
4. No other logic changes needed
```

## DATA

**Input:**
```python
env_vars = {
    'MCP_CODER_PROJECT_DIR': 'C:\\project',
    'MCP_CODER_VENV_DIR': 'C:\\project\\.venv'
}
```

**Output:** Same `LLMResponseDict` structure as before

## Test Coverage

**New test:**
```python
def test_ask_claude_code_cli_with_env_vars(mock_subprocess, mock_find_claude):
    """Test that env_vars are passed to subprocess."""
    env_vars = {'MCP_CODER_PROJECT_DIR': '/test/path'}
    result = ask_claude_code_cli("test", env_vars=env_vars)
    
    # Verify CommandOptions.env was set
    call_args = mock_subprocess.call_args
    assert call_args[0][1].env == env_vars
```

**Extend existing tests:**
- Verify backward compatibility when `env_vars=None`

## LLM Prompt

```
Context: Read pr_info/steps/summary.md and pr_info/steps/step_2.md

Task: Add env_vars parameter to CLI provider.

Changes:
1. Update ask_claude_code_cli() signature to accept env_vars: dict[str, str] | None = None
2. Pass env_vars to CommandOptions(env=env_vars)
3. Update docstring

Tests:
1. Add test_ask_claude_code_cli_with_env_vars() in tests/llm/providers/claude/test_claude_code_cli.py
2. Verify env_vars passed to subprocess
3. Verify backward compatibility with env_vars=None
4. Run tests

Follow TDD: Write tests first, then implementation.
```
