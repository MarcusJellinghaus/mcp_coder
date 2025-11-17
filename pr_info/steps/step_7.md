# Step 7: Update Workflow Layers

## LLM Prompt
```
You are implementing Step 7 of the execution-dir feature.

Reference documents:
- Summary: pr_info/steps/summary.md
- Previous steps: pr_info/steps/step_1.md through step_6.md (completed)
- This step: pr_info/steps/step_7.md

Task: Update workflow functions to accept and pass execution_dir to LLM calls.

Follow Test-Driven Development:
1. Read this step document completely
2. Update tests first
3. Modify workflow functions
4. Verify all tests pass

Apply KISS principle - add parameter, pass it through, minimal changes.
```

## Objective
Update workflow layer functions to accept `execution_dir` parameter and pass it to LLM interface calls.

## WHERE
**Modified files:**
- File: `src/mcp_coder/workflows/implement/core.py`
  - Function: `prepare_task_tracker()`
  - Function: `run_implement_workflow()`
  - Function: Any other functions calling LLM
- File: `src/mcp_coder/workflows/create_plan.py`
  - Main workflow function
- File: `src/mcp_coder/workflows/create_pr/core.py`
  - Main workflow functions

**Test files:**
- File: `tests/workflows/implement/test_core.py`
- File: `tests/workflows/create_plan/test_main.py`
- File: `tests/workflows/create_pr/test_workflow.py`

## WHAT

### Function Signature Updates

**In `workflows/implement/core.py`:**

```python
def prepare_task_tracker(
    project_dir: Path,
    provider: str,
    method: str,
    mcp_config: Optional[str] = None,
    execution_dir: Optional[Path] = None,  # NEW PARAMETER
) -> bool:
    """Prepare task tracker by populating it if it has no implementation steps.

    Args:
        project_dir: Path to the project directory
        provider: LLM provider (e.g., 'claude')
        method: LLM method (e.g., 'cli' or 'api')
        mcp_config: Optional path to MCP configuration file
        execution_dir: Optional working directory for Claude subprocess.
            Default: None (uses caller's working directory)

    Returns:
        bool: True if task tracker is ready, False on error
    """
    # ... existing code ...
    
    # Modified LLM call
    response = ask_llm(
        prompt_template,
        provider=provider,
        method=method,
        timeout=LLM_TASK_TRACKER_PREPARATION_TIMEOUT_SECONDS,
        env_vars=env_vars,
        project_dir=str(project_dir),
        execution_dir=str(execution_dir) if execution_dir else None,  # NEW
        mcp_config=mcp_config,
    )

def run_implement_workflow(
    project_dir: Path,
    provider: str,
    method: str,
    mcp_config: Optional[str] = None,
    execution_dir: Optional[Path] = None,  # NEW PARAMETER
) -> int:
    """Main workflow orchestration function.

    Args:
        project_dir: Path to the project directory
        provider: LLM provider (e.g., 'claude')
        method: LLM method (e.g., 'cli' or 'api')
        mcp_config: Optional path to MCP configuration file
        execution_dir: Optional working directory for Claude subprocess

    Returns:
        int: Exit code (0 for success, 1 for error)
    """
    # ... existing code ...
    
    # Pass execution_dir to prepare_task_tracker
    if not prepare_task_tracker(project_dir, provider, method, mcp_config, execution_dir):
        return 1
    
    # Pass execution_dir to process_single_task (if it calls LLM)
    success, reason = process_single_task(
        project_dir, provider, method, mcp_config, execution_dir
    )
```

**In `workflows/create_plan.py`:**
```python
def create_plan(
    project_dir: Path,
    issue_number: int,
    provider: str,
    method: str,
    mcp_config: Optional[str] = None,
    execution_dir: Optional[Path] = None,  # NEW PARAMETER
) -> int:
    """Generate implementation plan for GitHub issue.

    Args:
        project_dir: Path to the project directory
        issue_number: GitHub issue number
        provider: LLM provider
        method: LLM method
        mcp_config: Optional MCP config path
        execution_dir: Optional working directory for Claude subprocess

    Returns:
        int: Exit code
    """
    # ... existing code ...
    
    # Modified LLM calls
    response = ask_llm(
        prompt,
        provider=provider,
        method=method,
        env_vars=env_vars,
        project_dir=str(project_dir),
        execution_dir=str(execution_dir) if execution_dir else None,  # NEW
        mcp_config=mcp_config,
    )
```

**In `workflows/create_pr/core.py`:**
```python
def create_pr_workflow(
    project_dir: Path,
    provider: str,
    method: str,
    mcp_config: Optional[str] = None,
    execution_dir: Optional[Path] = None,  # NEW PARAMETER
) -> int:
    """Create pull request with AI-generated summary.

    Args:
        project_dir: Path to the project directory
        provider: LLM provider
        method: LLM method
        mcp_config: Optional MCP config path
        execution_dir: Optional working directory for Claude subprocess

    Returns:
        int: Exit code
    """
    # Pass execution_dir to all LLM calls
```

## HOW

### Integration Points

1. **Add parameter to function signatures:**
   ```python
   def workflow_function(..., execution_dir: Optional[Path] = None):
   ```

2. **Pass to LLM calls:**
   ```python
   response = ask_llm(
       ...,
       project_dir=str(project_dir),
       execution_dir=str(execution_dir) if execution_dir else None,
       ...
   )
   ```

3. **Convert Path to str:**
   ```python
   # execution_dir is Path from command handler
   # Convert to str for LLM interface
   execution_dir_str = str(execution_dir) if execution_dir else None
   ```

4. **Propagate through workflow:**
   ```python
   # Main workflow calls sub-functions
   prepare_task_tracker(..., execution_dir=execution_dir)
   process_single_task(..., execution_dir=execution_dir)
   ```

## ALGORITHM

```
FOR EACH workflow_function:
    UPDATE signature:
        ADD parameter: execution_dir: Optional[Path] = None
    
    FOR EACH llm_call IN function:
        UPDATE call:
            ADD execution_dir=str(execution_dir) if execution_dir else None
    
    FOR EACH sub_function_call:
        IF sub_function uses LLM:
            PASS execution_dir parameter
```

## DATA

### Parameter Type
- Input: `Optional[Path]` (from command handlers)
- Internal: Convert to `str` for LLM calls
- Default: `None` (uses caller's CWD)

### Example Propagation
```python
# Command handler (Step 4)
execution_dir = resolve_execution_dir(args.execution_dir)  # Path object

# Workflow layer (this step)
run_implement_workflow(..., execution_dir=execution_dir)  # Pass Path

# LLM call (convert to str)
ask_llm(..., execution_dir=str(execution_dir) if execution_dir else None)
```

## Test Requirements

### Test Cases for Implement Workflow
1. **Test execution_dir passed to prepare_task_tracker** → Verify propagation
2. **Test execution_dir passed to LLM calls** → Mock captures parameter
3. **Test execution_dir None uses default** → No errors
4. **Test execution_dir affects Claude context** → Integration test

### Test Cases for Create Plan
1. **Test execution_dir in plan generation** → Passed to LLM
2. **Test execution_dir with issue context** → Works together

### Test Cases for Create PR
1. **Test execution_dir in PR generation** → Passed to LLM
2. **Test execution_dir affects template discovery** → Integration test

### Test Structure
```python
# In test_core.py (implement)
class TestImplementWorkflowExecutionDir:
    """Tests for execution_dir in implement workflow."""
    
    def test_execution_dir_passed_to_prepare_task_tracker(self, mock_llm):
        """execution_dir should be passed to task tracker preparation."""
        
    def test_execution_dir_passed_to_llm_calls(self, mock_llm):
        """All LLM calls should receive execution_dir."""
        
    def test_execution_dir_none_uses_default(self, mock_llm):
        """execution_dir=None should work without errors."""

# Similar for create_plan and create_pr tests
```

## Implementation Notes

### KISS Principles Applied
- Simple parameter addition
- Pass-through logic
- Consistent conversion (Path → str)
- Minimal code changes

### Why This Design
1. **Type Safety**: Use `Path` in workflow layer, convert to `str` for LLM
2. **Consistency**: Same pattern across all workflows
3. **Clarity**: Clear separation between project and execution
4. **Flexibility**: Each workflow can use different execution dir

### Functions That Need Updates

**In `implement/core.py`:**
- `prepare_task_tracker()` - Calls LLM directly
- `run_implement_workflow()` - Main orchestrator
- Any helper functions that call LLM

**In `create_plan.py`:**
- Main workflow function
- Any prompt generation functions

**In `create_pr/core.py`:**
- `create_pr_workflow()` or similar
- PR generation functions

### Search Pattern
Find all LLM calls in workflows:
```python
# Search for these patterns:
ask_llm(
prompt_llm(
# And add execution_dir parameter
```

## Verification Steps
1. Run workflow tests:
   ```bash
   pytest tests/workflows/implement/ -v
   pytest tests/workflows/create_plan/ -v
   pytest tests/workflows/create_pr/ -v
   ```
2. Verify parameter propagation with mocks
3. Run integration tests with real workflows
4. Check mypy: `mypy src/mcp_coder/workflows/`
5. Run pylint on modified files

## Dependencies
- Depends on: Step 5 (LLM interface accepts execution_dir)
- Prepares for: Step 8 (end-to-end integration testing)

## Estimated Complexity
- Lines of code: ~40 lines (signatures + pass-through)
- Test lines: ~150 lines
- Complexity: Medium (multiple files, careful propagation)

## Potential Sub-Functions to Update

**In `implement/task_processing.py`:**
If functions like `process_single_task()` or `check_and_fix_mypy()` call LLM:
```python
def process_single_task(
    project_dir: Path,
    provider: str,
    method: str,
    mcp_config: Optional[str],
    execution_dir: Optional[Path] = None,  # NEW
) -> tuple[bool, str]:
    """Process a single implementation task."""
    # Pass execution_dir to any LLM calls
```

## Logging Strategy
Add debug logging for traceability:
```python
logger.debug(
    f"Workflow execution: project_dir={project_dir}, "
    f"execution_dir={execution_dir or 'CWD'}"
)
```

## Error Handling
No new error handling needed - rely on:
- Command handler validation (Step 3-4)
- LLM interface validation (Step 5)
- Subprocess error handling (existing)

## Complete Example: Implement Workflow

**Before:**
```python
def run_implement_workflow(project_dir, provider, method, mcp_config):
    prepare_task_tracker(project_dir, provider, method, mcp_config)
    # ...
    ask_llm(prompt, project_dir=str(project_dir), ...)
```

**After:**
```python
def run_implement_workflow(project_dir, provider, method, mcp_config, execution_dir=None):
    prepare_task_tracker(project_dir, provider, method, mcp_config, execution_dir)
    # ...
    ask_llm(
        prompt,
        project_dir=str(project_dir),
        execution_dir=str(execution_dir) if execution_dir else None,
        ...
    )
```
