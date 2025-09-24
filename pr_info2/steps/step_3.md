# Step 3: Clean Up Utils Module and Remove File Discovery

## LLM Prompt
```
Based on the refactor summary in `pr_info2/steps/summary.md` and the completed directory-based formatters from Steps 1-2, implement Step 3 using TDD: First update the utils tests to remove `find_python_files()` test coverage. Then clean up the utils module by removing the now-unnecessary file discovery function while preserving the still-needed configuration and directory utility functions.
```

## WHERE
- `tests/formatters/test_utils.py` - **START HERE: Remove file discovery tests (TDD)**
- `src/mcp_coder/formatters/utils.py` - Remove `find_python_files()` function after tests

## WHAT
### Functions to Remove
```python
# REMOVE THIS FUNCTION
def find_python_files(directory: Path) -> List[Path]:
    """This function is no longer needed"""
```

### Functions to Keep (Unchanged)
```python
def get_default_target_dirs(project_root: Path) -> List[str]:
    """Keep - still needed for directory selection logic"""

def read_tool_config(project_root: Path, tool_name: str, defaults: Dict[str, Any]) -> Dict[str, Any]:
    """Keep - still needed for configuration reading"""
```

## HOW
### Integration Points
- Update `black_formatter.py` and `isort_formatter.py` imports (already done in Steps 1-2)
- Remove any remaining imports of `find_python_files` from other modules
- Keep all configuration-related functionality intact
- Verify no other modules depend on `find_python_files()`

### Dependencies (Cleaned Up)
```python
# In utils.py - Remove unused imports related to file discovery
import tomllib  # Keep
from pathlib import Path  # Keep
from typing import Any, Dict, List  # Keep (but List may be unused now)
```

## ALGORITHM
```
1. Remove find_python_files() function entirely
2. Remove any imports only used by find_python_files() 
3. Keep get_default_target_dirs() and read_tool_config() unchanged
4. Update module docstring to reflect simplified purpose
5. Verify no circular imports or missing dependencies
```

## DATA
### Module Structure (After Cleanup)
```python
"""Shared utilities for formatter implementations - directory and config utilities only."""

def get_default_target_dirs(project_root: Path) -> List[str]:
    """Get default target directories for formatting (src, tests, or current)"""
    # Implementation unchanged

def read_tool_config(project_root: Path, tool_name: str, defaults: Dict[str, Any]) -> Dict[str, Any]:
    """Read tool configuration from pyproject.toml with defaults"""
    # Implementation unchanged
```

### Removed Functions
- `find_python_files()` - No longer needed, replaced by directory-based tool execution
- Any helper functions only used by file discovery
- Related imports (if any)

## Tests Required (TDD - Focused Testing)
1. **Verify removal test (1 test)**
   - Test that `find_python_files` is no longer available for import
   - Ensure clean removal without breaking other functionality

2. **Essential utils test (1 test)**
   - Test `get_default_target_dirs()` and `read_tool_config()` still work
   - Verify core utilities remain functional after cleanup

3. **Import validation test (1 test)**
   - Ensure no test files still try to import `find_python_files`
   - Check that utils module imports are clean

## Verification Steps
1. Run `pylint` to check for unused imports
2. Run `pytest` to ensure no broken imports or missing dependencies
3. Verify formatters still work with simplified utils module
4. Check that utils module has clear, focused responsibility
