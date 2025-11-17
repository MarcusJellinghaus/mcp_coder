# Step 5: Update LLM Interface Layer

## LLM Prompt
```
You are implementing Step 5 of the execution-dir feature.

Reference documents:
- Summary: pr_info/steps/summary.md
- Previous steps: pr_info/steps/step_1.md through step_4.md (completed)
- This step: pr_info/steps/step_5.md

Task: Add execution_dir parameter to LLM interface functions (ask_llm, prompt_llm).

Follow Test-Driven Development:
1. Read this step document completely
2. Update tests first
3. Add parameter to interface functions
4. Verify all tests pass

Apply KISS principle - add parameter, pass it through, minimal logic.
```

## Objective
Add `execution_dir` parameter to `ask_llm()` and `prompt_llm()` functions, keeping it separate from `project_dir`.

## WHERE
**Modified file:**
- File: `src/mcp_coder/llm/interface.py`
  - Function: `ask_llm()`
  - Function: `prompt_llm()`

**Test file:**
- File: `tests/llm/test_interface.py`
  - Add tests for execution_dir parameter

## WHAT

### Function Signature Updates

**ask_llm() - Before:**
```python
def ask_llm(
    question: str,
    provider: str = "claude",
    method: str = "cli",
    session_id: str | None = None,
    timeout: int = LLM_DEFAULT_TIMEOUT_SECONDS,
    env_vars: dict[str, str] | None = None,
    project_dir: str | None = None,
    mcp_config: str | None = None,
) -> str:
```

**ask_llm() - After:**
```python
def ask_llm(
    question: str,
    provider: str = "claude",
    method: str = "cli",
    session_id: str | None = None,
    timeout: int = LLM_DEFAULT_TIMEOUT_SECONDS,
    env_vars: dict[str, str] | None = None,
    project_dir: str | None = None,
    execution_dir: str | None = None,  # NEW PARAMETER
    mcp_config: str | None = None,
) -> str:
    """
    Ask a question to an LLM provider.
    
    Args:
        ...existing args...
        project_dir: Optional project directory for MCP_CODER_PROJECT_DIR env var
        execution_dir: Optional working directory for LLM subprocess (default: current directory)
        mcp_config: Optional path to MCP configuration file
    """
```

**prompt_llm() - Similar addition:**
```python
def prompt_llm(
    question: str,
    provider: str = "claude",
    method: str = "cli",
    session_id: str | None = None,
    timeout: int = LLM_DEFAULT_TIMEOUT_SECONDS,
    env_vars: dict[str, str] | None = None,
    project_dir: str | None = None,
    execution_dir: str | None = None,  # NEW PARAMETER
    mcp_config: str | None = None,
) -> LLMResponseDict:
```

## HOW

### Integration Points

1. **Parameter addition:**
   - Add `execution_dir` parameter after `project_dir`
   - Default value: `None`
   - Type hint: `str | None`

2. **Pass to provider:**
   ```python
   # In ask_llm()
   return ask_claude_code(
       question,
       method=method,
       session_id=session_id,
       timeout=timeout,
       env_vars=env_vars,
       cwd=execution_dir,  # Pass as cwd to subprocess
       mcp_config=mcp_config,
   )
   ```

3. **Pass to lower-level functions:**
   ```python
   # In prompt_llm()
   if method == "cli":
       return ask_claude_code_cli(
           question,
           session_id=session_id,
           timeout=timeout,
           env_vars=env_vars,
           cwd=execution_dir,  # Pass as cwd
           mcp_config=mcp_config,
       )
   ```

## ALGORITHM

```
FUNCTION ask_llm(..., project_dir, execution_dir, ...):
    Validate inputs (existing logic)
    
    IF provider == "claude":
        RETURN ask_claude_code(
            question,
            ...,
            cwd=execution_dir,  # NEW: Pass execution_dir as cwd
            ...
        )
    ELSE:
        RAISE ValueError("Unsupported provider")

FUNCTION prompt_llm(..., project_dir, execution_dir, ...):
    Validate inputs (existing logic)
    
    IF provider == "claude":
        IF method == "cli":
            RETURN ask_claude_code_cli(..., cwd=execution_dir, ...)
        ELIF method == "api":
            RETURN ask_claude_code_api(..., cwd=execution_dir, ...)
    ELSE:
        RAISE ValueError("Unsupported provider/method")
```

## DATA

### Parameter Semantics

**project_dir:**
- Purpose: Where files live, used for `MCP_CODER_PROJECT_DIR` env var
- Used by: `prepare_llm_environment()` to set environment variables
- Not passed to subprocess as cwd

**execution_dir:**
- Purpose: Where Claude subprocess runs
- Used by: Passed as `cwd` parameter to subprocess
- Affects: Where Claude looks for `.mcp.json` and relative file paths

### Key Distinction
```python
# Separate concerns:
env_vars = prepare_llm_environment(project_dir)  # Environment variables
# ...
ask_claude_code(..., env_vars=env_vars, cwd=execution_dir)  # Subprocess execution
```

## Test Requirements

### Test Cases for ask_llm()
1. **Test execution_dir passed to provider** → Verify cwd parameter
2. **Test execution_dir None defaults to current dir** → Subprocess uses CWD
3. **Test execution_dir with absolute path** → Subprocess uses specified path
4. **Test separation from project_dir** → Both parameters work independently

### Test Cases for prompt_llm()
1. **Test execution_dir with CLI method** → Passed to CLI provider
2. **Test execution_dir with API method** → Passed to API provider
3. **Test execution_dir in returned metadata** → Not stored in response
4. **Test both project_dir and execution_dir** → Can differ

### Test Structure
```python
class TestAskLLMExecutionDir:
    """Tests for execution_dir parameter in ask_llm."""
    
    def test_execution_dir_passed_to_provider(self, mock_provider):
        """execution_dir should be passed as cwd to provider."""
        
    def test_execution_dir_none_uses_default(self, mock_provider):
        """execution_dir=None should let subprocess use CWD."""
        
    def test_execution_dir_independent_of_project_dir(self, mock_provider):
        """execution_dir and project_dir should be independent."""

class TestPromptLLMExecutionDir:
    """Tests for execution_dir parameter in prompt_llm."""
    
    def test_execution_dir_with_cli_method(self, mock_cli):
        """execution_dir should be passed to CLI provider."""
        
    def test_execution_dir_with_api_method(self, mock_api):
        """execution_dir should be passed to API provider."""
```

## Implementation Notes

### KISS Principles Applied
- Simple parameter addition
- Pass-through logic (no transformation)
- Clear naming: `execution_dir` → `cwd`
- No complex validation (done in command handlers)

### Why This Design
1. **Separation of Concerns**: `project_dir` and `execution_dir` are distinct
2. **Backward Compatible**: Default `None` maintains existing behavior
3. **Clear Semantics**: Parameter name matches purpose
4. **Provider Agnostic**: Works with any future provider

### Documentation Updates
Update docstrings to clearly explain:
- `project_dir`: For environment variables and git operations
- `execution_dir`: For subprocess working directory
- Default behavior when `execution_dir=None`

## Verification Steps
1. Run tests: `pytest tests/llm/test_interface.py -v`
2. Verify parameter passing with mocks
3. Run mypy: `mypy src/mcp_coder/llm/interface.py`
4. Run pylint: Should pass with no errors
5. Check existing tests still pass

## Dependencies
- Depends on: Step 4 (command handlers prepare the parameter)
- Prepares for: Step 6 (Claude provider documentation)

## Estimated Complexity
- Lines of code: ~10 lines (parameter additions + pass-through)
- Test lines: ~80 lines
- Complexity: Low (simple parameter addition)

## Integration with Existing Code

**Before this step:**
```python
# Command handler
ask_llm(question, project_dir=str(project_dir))

# Interface layer
def ask_llm(..., project_dir):
    return ask_claude_code(..., cwd=project_dir)  # Conflated!
```

**After this step:**
```python
# Command handler (from Step 3-4)
ask_llm(question, project_dir=str(project_dir), execution_dir=str(execution_dir))

# Interface layer (this step)
def ask_llm(..., project_dir, execution_dir):
    env_vars = prepare_llm_environment(project_dir)
    return ask_claude_code(..., env_vars=env_vars, cwd=execution_dir)  # Separated!
```

## Example Usage After This Step
```python
# Separate project and execution locations
response = ask_llm(
    "Analyze the code",
    project_dir="/home/user/projects/myapp",  # Where files are
    execution_dir="/home/user/workspace",      # Where Claude runs
)

# Default execution (uses CWD)
response = ask_llm(
    "Analyze the code",
    project_dir="/home/user/projects/myapp",
    # execution_dir=None (default)
)
```
