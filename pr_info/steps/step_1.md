# Step 1: Add Path Resolution Utility for Execution Directory

## LLM Prompt
```
You are implementing Step 1 of the execution-dir feature.

Reference documents:
- Summary: pr_info/steps/summary.md
- This step: pr_info/steps/step_1.md

Task: Create a utility function to resolve and validate execution directory paths.

Follow Test-Driven Development:
1. Read this step document completely
2. Implement tests first
3. Implement the utility function
4. Verify all tests pass

Apply KISS principle - keep the implementation simple and focused.
```

## Objective
Create a reusable utility function to resolve execution directory paths with proper validation.

## WHERE
**New utility function:**
- File: `src/mcp_coder/cli/utils.py`
- Add function: `resolve_execution_dir()`

**Test file:**
- File: `tests/cli/test_utils.py`
- Test class: `TestResolveExecutionDir`

## WHAT

### Main Function Signature
```python
def resolve_execution_dir(execution_dir: str | None) -> Path:
    """
    Resolve execution directory path to absolute Path object.
    
    Args:
        execution_dir: Optional execution directory path
                      - None: Returns current working directory
                      - Absolute path: Validates and returns as Path
                      - Relative path: Resolves relative to CWD
    
    Returns:
        Path: Absolute path to execution directory
    
    Raises:
        ValueError: If specified directory doesn't exist
    
    Examples:
        >>> resolve_execution_dir(None)
        PosixPath('/current/working/dir')
        
        >>> resolve_execution_dir('/absolute/path')
        PosixPath('/absolute/path')
        
        >>> resolve_execution_dir('./relative')
        PosixPath('/current/working/dir/relative')
    """
```

## HOW

### Integration Points
1. **Import at top of file:**
   ```python
   from pathlib import Path
   ```

2. **Usage pattern in command handlers:**
   ```python
   from ..utils import resolve_execution_dir
   
   execution_dir = resolve_execution_dir(args.execution_dir)
   ```

## ALGORITHM

```
FUNCTION resolve_execution_dir(execution_dir):
    IF execution_dir is None:
        RETURN Path.cwd()
    
    path = Path(execution_dir)
    
    IF NOT path.is_absolute():
        path = Path.cwd() / path
    
    IF NOT path.exists():
        RAISE ValueError("Directory does not exist")
    
    RETURN path.resolve()
```

## DATA

### Input
- `execution_dir`: `str | None`
  - `None`: Use current working directory
  - `str`: Absolute or relative path

### Output
- `Path`: Resolved absolute path object

### Error Cases
- Raises `ValueError` with message: `"Execution directory does not exist: {path}"` when path is invalid

## Test Requirements

### Test Cases
1. **Test None input** → Returns `Path.cwd()`
2. **Test absolute path** → Returns validated absolute path
3. **Test relative path** → Resolves to CWD + relative path
4. **Test non-existent path** → Raises `ValueError`
5. **Test existing directory** → Returns resolved path
6. **Test symlinks** → Resolves to real path

### Test Structure
```python
class TestResolveExecutionDir:
    """Tests for resolve_execution_dir utility function."""
    
    def test_none_returns_cwd(self):
        """None input should return current working directory."""
        
    def test_absolute_path_validation(self, tmp_path):
        """Absolute paths should be validated and returned."""
        
    def test_relative_path_resolution(self, tmp_path, monkeypatch):
        """Relative paths should resolve relative to CWD."""
        
    def test_nonexistent_path_raises_error(self):
        """Non-existent paths should raise ValueError."""
        
    def test_existing_directory_resolves(self, tmp_path):
        """Existing directories should resolve correctly."""
```

## Implementation Notes

### KISS Principles Applied
- Single responsibility: only path resolution
- No complex logic - straightforward validation
- Reuses Python's `pathlib` for path operations
- Clear error messages

### Why This Design
1. **Centralized validation**: All commands use same logic
2. **Type safety**: Returns `Path` object consistently
3. **Clear semantics**: `None` = CWD is explicit and intuitive
4. **Testable**: Pure function with no side effects

## Verification Steps
1. Run tests: `pytest tests/cli/test_utils.py::TestResolveExecutionDir -v`
2. Verify all 6 test cases pass
3. Check code coverage: Should be 100% for this function
4. Run mypy: `mypy src/mcp_coder/cli/utils.py`
5. Run pylint: Should have no errors

## Dependencies
- Standard library: `pathlib.Path`
- No external dependencies

## Estimated Complexity
- Lines of code: ~15 lines
- Test lines: ~60 lines
- Complexity: Low (straightforward path validation)
