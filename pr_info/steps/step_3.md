# Step 3: Update Command Handlers (Prompt, Commit)

## LLM Prompt
```
You are implementing Step 3 of the execution-dir feature.

Reference documents:
- Summary: pr_info/steps/summary.md
- Previous steps: pr_info/steps/step_1.md, pr_info/steps/step_2.md (completed)
- This step: pr_info/steps/step_3.md

Task: Update prompt and commit command handlers to extract and use execution_dir.

Follow Test-Driven Development:
1. Read this step document completely
2. Update tests first
3. Modify command handlers
4. Verify all tests pass

Apply KISS principle - minimal changes, clear flow.
```

## Objective
Update `prompt` and `commit auto` command handlers to extract `execution_dir` from CLI args and pass it to LLM calls.

## WHERE
**Modified files:**
- File: `src/mcp_coder/cli/commands/prompt.py`
  - Function: `execute_prompt()`
- File: `src/mcp_coder/cli/commands/commit.py`
  - Function: `execute_commit_auto()`

**Test files:**
- File: `tests/cli/commands/test_prompt.py`
  - Add tests for execution_dir handling
- File: `tests/cli/commands/test_commit.py`
  - Add tests for execution_dir handling

## WHAT

### Function Modifications

**In `prompt.py`:**
```python
def execute_prompt(args: argparse.Namespace) -> int:
    """Execute the prompt command.
    
    Args:
        args: Parsed command line arguments with:
            - prompt: The prompt text
            - project_dir: Optional project directory
            - execution_dir: Optional execution directory (NEW)
            - verbosity: Output verbosity level
            - ... (other existing args)
    """
    # Extract execution_dir and resolve
    from ..utils import resolve_execution_dir
    execution_dir = resolve_execution_dir(args.execution_dir)
    
    # Pass to LLM interface (will be updated in step 5)
    # For now, just extract and validate
```

**In `commit.py`:**
```python
def execute_commit_auto(args: argparse.Namespace) -> int:
    """Execute auto-commit with LLM-generated message.
    
    Args:
        args: Parsed command line arguments with:
            - project_dir: Optional project directory
            - execution_dir: Optional execution directory (NEW)
            - llm_method: LLM method to use
            - ... (other existing args)
    """
    # Extract execution_dir and resolve
    from ..utils import resolve_execution_dir
    execution_dir = resolve_execution_dir(args.execution_dir)
    
    # Pass to LLM interface (will be updated in step 5)
    # For now, just extract and validate
```

## HOW

### Integration Points

1. **Import utility function:**
   ```python
   from ..utils import resolve_execution_dir
   ```

2. **Extract from args:**
   ```python
   execution_dir = resolve_execution_dir(args.execution_dir)
   ```

3. **Store for later use:**
   - Store `execution_dir` as local variable
   - Will be passed to LLM calls in Step 5
   - For now, just validate it doesn't raise errors

4. **Error handling:**
   ```python
   try:
       execution_dir = resolve_execution_dir(args.execution_dir)
   except ValueError as e:
       logger.error(f"Invalid execution directory: {e}")
       print(f"Error: {e}", file=sys.stderr)
       return 1
   ```

## ALGORITHM

```
FUNCTION execute_prompt(args):
    TRY:
        execution_dir = resolve_execution_dir(args.execution_dir)
        Log: "Using execution directory: {execution_dir}"
    CATCH ValueError as e:
        Log error: "Invalid execution directory"
        Return 1
    
    # Continue with existing logic
    # Store execution_dir for Step 5 integration
    
FUNCTION execute_commit_auto(args):
    # Same pattern as above
```

## DATA

### Input
- `args.execution_dir`: `str | None`

### Output
- `execution_dir`: `Path` object (validated, absolute)

### Error Handling
- Invalid path → Log error, return 1
- Valid path → Continue execution

## Test Requirements

### Test Cases for `test_prompt.py`
1. **Test default execution_dir (None)** → Uses CWD
2. **Test explicit absolute path** → Validates and uses path
3. **Test explicit relative path** → Resolves relative to CWD
4. **Test invalid path** → Returns error code 1
5. **Test execution_dir with all other args** → No conflicts

### Test Cases for `test_commit.py`
1. **Test default execution_dir (None)** → Uses CWD
2. **Test explicit absolute path** → Validates and uses path
3. **Test invalid path** → Returns error code 1
4. **Test execution_dir with preview mode** → Works together

### Test Structure
```python
# In test_prompt.py
class TestPromptExecutionDir:
    """Tests for execution_dir handling in prompt command."""
    
    def test_default_execution_dir_uses_cwd(self, mock_ask_llm):
        """Default execution_dir should use current working directory."""
        
    def test_explicit_execution_dir_absolute(self, tmp_path, mock_ask_llm):
        """Explicit absolute execution_dir should be validated."""
        
    def test_invalid_execution_dir_returns_error(self, mock_ask_llm):
        """Invalid execution_dir should return error code 1."""

# In test_commit.py  
class TestCommitAutoExecutionDir:
    """Tests for execution_dir handling in commit auto command."""
    
    def test_default_execution_dir_uses_cwd(self, mock_git_repo):
        """Default execution_dir should use current working directory."""
        
    def test_explicit_execution_dir_validated(self, tmp_path, mock_git_repo):
        """Explicit execution_dir should be validated and used."""
```

## Implementation Notes

### KISS Principles Applied
- Minimal changes to existing code
- Reuse existing error handling patterns
- Clear separation: validation vs. usage
- Consistent pattern across both commands

### Why This Design
1. **Early validation**: Catch errors before LLM calls
2. **Clear logging**: Users know what directory is being used
3. **Graceful errors**: Invalid paths return proper error codes
4. **Future-ready**: Prepared for Step 5 integration

### Current State vs. After This Step

**Before:**
```python
def execute_prompt(args):
    # No execution_dir handling
    response = prompt_llm(..., project_dir=str(project_dir))
```

**After:**
```python
def execute_prompt(args):
    execution_dir = resolve_execution_dir(args.execution_dir)
    logger.debug(f"Execution directory: {execution_dir}")
    # Will pass to LLM in Step 5
    response = prompt_llm(..., project_dir=str(project_dir))
```

## Verification Steps
1. Run tests: `pytest tests/cli/commands/test_prompt.py -v`
2. Run tests: `pytest tests/cli/commands/test_commit.py -v`
3. Test invalid path manually:
   ```bash
   mcp-coder prompt "test" --execution-dir /nonexistent
   # Should print error and exit with code 1
   ```
4. Run mypy on modified files
5. Run pylint on modified files

## Dependencies
- Depends on: Step 1 (resolve_execution_dir utility)
- Used by: Step 5 (LLM interface integration)

## Estimated Complexity
- Lines of code: ~30 lines (15 per command)
- Test lines: ~120 lines (60 per command)
- Complexity: Low (straightforward extraction and validation)

## Logging Strategy
Add debug logging for visibility:
```python
logger.debug(f"Execution directory resolved to: {execution_dir}")
logger.debug(f"Project directory: {project_dir}")
```

This helps troubleshoot the separation of concerns.
