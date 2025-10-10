# Step 1: Setup and Argument Parsing

## Objective

Create the batch wrapper and implement argument parsing with project directory validation.

## Files to Create/Modify

### Create
- `workflows/create_plan.bat`

### Modify  
- `workflows/create_plan.py` (new file with initial structure)

## Implementation Details

### WHERE
- `workflows/create_plan.bat` - Batch wrapper
- `workflows/create_plan.py` - Main workflow script (argument parsing only)

### WHAT

#### create_plan.bat
Set up Python environment and call create_plan.py with proper encoding settings.

#### create_plan.py Functions

```python
def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments including project directory and log level."""
    
def resolve_project_dir(project_dir_arg: Optional[str]) -> Path:
    """Convert project directory argument to absolute Path, with validation."""
```

### HOW

**create_plan.bat:**
- Set console codepage to UTF-8
- Set Python environment variables for UTF-8 encoding
- Set PYTHONPATH to include src directory
- Call Python script with all arguments passed through

**create_plan.py:**
- Import standard libraries: `argparse`, `sys`, `logging`, `Path`
- Import from `mcp_coder.utils.log_utils`: `setup_logging`
- Follow exact same pattern as `create_pr.py`

### ALGORITHM

**parse_arguments():**
```
1. Create ArgumentParser with description
2. Add positional argument 'issue_number' (type=int, required)
3. Add optional '--project-dir' argument (metavar="PATH")
4. Add optional '--log-level' argument (choices, default="INFO")
5. Add optional '--llm-method' argument (choices, default="claude_code_cli")
6. Return parsed arguments
```

**resolve_project_dir():**
```
1. If project_dir_arg is None, use Path.cwd()
2. Else create Path from project_dir_arg
3. Resolve to absolute path
4. Validate: exists, is_dir, is accessible, contains .git
5. Return validated Path or exit with error
```

### DATA

**parse_arguments() returns:**
```python
argparse.Namespace(
    issue_number: int,
    project_dir: Optional[str],
    log_level: str,
    llm_method: str
)
```

**resolve_project_dir() returns:**
```python
Path  # Absolute, validated path to project directory
```

## Testing

Create `tests/workflows/create_plan/test_argument_parsing.py`:

```python
def test_parse_arguments_with_issue_number()
def test_parse_arguments_with_all_options()
def test_parse_arguments_missing_issue_number()
def test_resolve_project_dir_current_directory()
def test_resolve_project_dir_explicit_path()
def test_resolve_project_dir_invalid_path()
def test_resolve_project_dir_not_git_repository()
```

## Acceptance Criteria

- [ ] Batch file sets UTF-8 encoding correctly
- [ ] Batch file sets PYTHONPATH to include src directory
- [ ] Batch file passes all arguments to Python script
- [ ] Issue number is required positional argument
- [ ] Optional arguments default correctly
- [ ] Project directory validation works (exists, is_dir, has .git)
- [ ] Invalid paths exit with clear error messages
- [ ] All tests pass

## LLM Prompt for Implementation

```
Please implement Step 1 of the create_plan workflow.

Reference the summary at pr_info/steps/summary.md for overall context.

Create workflows/create_plan.bat following the pattern from workflows/create_pr.bat.
Create workflows/create_plan.py with argument parsing following the pattern from workflows/create_pr.py.

Key requirements:
- Issue number is a required positional argument
- Default llm_method should be 'claude_code_cli'
- Follow exact same validation patterns as create_pr.py
- Reuse resolve_project_dir() pattern with all validations

Implement the tests as specified.
```
