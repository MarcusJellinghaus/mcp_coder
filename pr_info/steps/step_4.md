# Step 4: Update Command Handlers (Implement, Create-Plan, Create-PR)

## LLM Prompt
```
You are implementing Step 4 (reordered to Step 7) of the execution-dir feature.

Reference documents:
- Summary: pr_info/steps/summary.md
- Previous steps: step_1.md, step_2.md, step_5.md, step_6.md, step_7.md, step_3.md (completed)
- This step: pr_info/steps/step_4.md
- Note: Steps reordered - workflows updated before command handlers (Decision #2)

Task: Update implement, create-plan, and create-pr command handlers to extract and pass execution_dir to workflow layer.

Follow Test-Driven Development:
1. Read this step document completely
2. Update tests first
3. Modify command handlers
4. Verify all tests pass

Apply KISS principle - follow same pattern as Step 3.
```

## Objective
Update `implement`, `create-plan`, and `create-pr` command handlers to extract `execution_dir` and pass it to workflow functions.

## WHERE
**Modified files:**
- File: `src/mcp_coder/cli/commands/implement.py`
  - Function: `execute_implement()`
- File: `src/mcp_coder/cli/commands/create_plan.py`
  - Function: `execute_create_plan()`
- File: `src/mcp_coder/cli/commands/create_pr.py`
  - Function: `execute_create_pr()`

**Test files:**
- File: `tests/cli/commands/test_implement.py`
- File: `tests/cli/commands/test_create_plan.py`
- File: `tests/cli/commands/test_create_pr.py`

## WHAT

### Function Modifications

**Pattern to apply in all three files:**
```python
def execute_XXX(args: argparse.Namespace) -> int:
    """Execute the XXX command.
    
    Args:
        args: Parsed command line arguments with:
            - project_dir: Optional project directory
            - execution_dir: Optional execution directory (NEW)
            - llm_method: LLM method to use
            - ... (other existing args)
    """
    try:
        # Existing: Resolve project directory
        project_dir = resolve_project_dir(args.project_dir)
        
        # NEW: Resolve execution directory
        from ..utils import resolve_execution_dir
        execution_dir = resolve_execution_dir(args.execution_dir)
        
        # NEW: Log both directories for clarity
        logger.debug(f"Project directory: {project_dir}")
        logger.debug(f"Execution directory: {execution_dir}")
        
        # Existing: Parse LLM method
        provider, method = parse_llm_method_from_args(args.llm_method)
        
        # Existing: Resolve MCP config
        mcp_config = resolve_mcp_config_path(getattr(args, "mcp_config", None))
        
        # Modified: Pass execution_dir to workflow
        return run_XXX_workflow(
            project_dir,
            provider,
            method,
            mcp_config,
            execution_dir  # NEW PARAMETER
        )
        
    except ValueError as e:
        # Handle invalid execution_dir
        logger.error(f"Invalid execution directory: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        # Existing error handling
        ...
```

## HOW

### Integration Points

1. **Import utility:**
   ```python
   from ..utils import resolve_execution_dir
   ```

2. **Extract and validate:**
   ```python
   execution_dir = resolve_execution_dir(args.execution_dir)
   ```

3. **Pass to workflow:**
   ```python
   # In implement.py
   return run_implement_workflow(project_dir, provider, method, mcp_config, execution_dir)
   
   # In create_plan.py  
   return create_plan(project_dir, issue_number, provider, method, mcp_config, execution_dir)
   
   # In create_pr.py
   return create_pr(project_dir, provider, method, mcp_config, execution_dir)
   ```

4. **Error handling:**
   - Wrap in try-except for ValueError
   - Log and return error code 1

## ALGORITHM

```
FOR EACH command IN [implement, create_plan, create_pr]:
    FUNCTION execute_command(args):
        TRY:
            project_dir = resolve_project_dir(args.project_dir)
            execution_dir = resolve_execution_dir(args.execution_dir)  # NEW
            
            Log: "Project directory: {project_dir}"
            Log: "Execution directory: {execution_dir}"
            
            provider, method = parse_llm_method(args.llm_method)
            mcp_config = resolve_mcp_config(args.mcp_config)
            
            RETURN run_workflow(..., execution_dir)  # NEW PARAMETER
            
        CATCH ValueError as e:
            Log error
            RETURN 1
        CATCH Exception as e:
            # Existing error handling
```

## DATA

### Input
- `args.execution_dir`: `str | None`

### Output
- `execution_dir`: `Path` object passed to workflow layer

### Modified Function Signatures
```python
# These workflow functions will be updated in Step 7
run_implement_workflow(project_dir, provider, method, mcp_config, execution_dir)
create_plan(project_dir, issue_number, provider, method, mcp_config, execution_dir)
create_pr(project_dir, provider, method, mcp_config, execution_dir)
```

## Test Requirements

### Test Cases (for each command)
1. **Test default execution_dir** → Uses CWD
2. **Test explicit absolute path** → Validates path
3. **Test explicit relative path** → Resolves relative to CWD
4. **Test invalid path** → Returns error code 1
5. **Test execution_dir passed to workflow** → Mock workflow receives it

### Test Structure
```python
# In test_implement.py
class TestImplementExecutionDir:
    """Tests for execution_dir in implement command."""
    
    def test_default_execution_dir(self, mock_workflow):
        """Default execution_dir should use CWD."""
        
    def test_explicit_execution_dir(self, tmp_path, mock_workflow):
        """Explicit execution_dir should be passed to workflow."""
        
    def test_invalid_execution_dir_returns_error(self):
        """Invalid execution_dir should return error code 1."""

# Similar for test_create_plan.py and test_create_pr.py
```

## Implementation Notes

### KISS Principles Applied
- Exact same pattern as Step 3
- Minimal changes to existing flow
- Clear parameter passing
- Consistent error handling

### Why This Design
1. **Consistency**: Same pattern across all commands
2. **Clarity**: Both directories logged together
3. **Separation**: Clear distinction between project and execution
4. **Preparation**: Ready for workflow layer updates in Step 7

### Logging Strategy (Decision #9)
**Important:** Log execution_dir once at command handler entry point only.

### Command-Specific Notes

**implement.py:**
- Most complex workflow
- Already has comprehensive error handling
- execution_dir will affect where Claude reads task tracker

**create_plan.py:**
- Generates implementation plans
- execution_dir affects where Claude finds issue templates

**create_pr.py:**
- Creates PR summaries
- execution_dir affects where Claude reads PR templates

## Verification Steps
1. Run tests for each command:
   ```bash
   pytest tests/cli/commands/test_implement.py -v
   pytest tests/cli/commands/test_create_plan.py -v
   pytest tests/cli/commands/test_create_pr.py -v
   ```
2. Test invalid path for each command
3. Run mypy on modified files
4. Run pylint on modified files
5. Verify existing tests still pass

## Dependencies
- Depends on: Step 1 (resolve_execution_dir), Steps 5 & 7 (LLM interface and workflows ready)
- Note: Reordered after workflow updates (Decision #2)

## Estimated Complexity
- Lines of code: ~45 lines (15 per command)
- Test lines: ~120 lines (reduced with parametrize - Decision #8)
- Complexity: Low (repetitive pattern application)

## Workflow Function Signatures (Will be updated in Step 7)

Note: These signatures will change in Step 7, but we prepare the calls now:

```python
# Current (Step 4 - these calls will temporarily cause type errors until Step 7)
run_implement_workflow(project_dir, provider, method, mcp_config, execution_dir)
create_plan(project_dir, issue_number, provider, method, mcp_config, execution_dir)  
create_pr(project_dir, provider, method, mcp_config, execution_dir)

# The workflow functions will be updated in Step 7 to accept execution_dir
```

**Important:** After this step, type checkers may complain about the extra parameter. This is expected and will be resolved in Step 7.
