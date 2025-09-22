# Step 5: Common Utilities and Main API

## LLM Prompt
```
Based on the Code Formatters Implementation Summary, implement Step 5: Create common utilities shared by formatters and implement the main API functions that provide a unified interface for code formatting operations.
```

## WHERE
- `src/mcp_coder/formatters/utils.py` - Shared utility functions
- `src/mcp_coder/formatters/__init__.py` - Main API and exports
- `tests/formatters/test_utils.py` - Unit tests for utilities
- `tests/formatters/test_main_api.py` - Integration tests for main API

## WHAT
### Utility Functions (utils.py)
```python
def get_python_files(directories: List[Path]) -> List[Path]:
    """Recursively find all .py files in given directories"""
```

### Main API Functions (__init__.py)
```python
def format_code(project_root: Path, formatters: List[str] = None, target_dirs: List[str] = None) -> Dict[str, FormatterResult]:
    """Run multiple formatters and return combined results"""
    
def format_with_black(project_root: Path, target_dirs: List[str] = None) -> FormatterResult:
    """Format code with Black (re-export from black_formatter)"""
    
def format_with_isort(project_root: Path, target_dirs: List[str] = None) -> FormatterResult:
    """Sort imports with isort (re-export from isort_formatter)"""
```

## HOW
### Integration Points
- Import all formatter implementations  
- Import all data models for public API
- Use `difflib.unified_diff` for diff generation
- Handle Path objects consistently across all utilities

### Dependencies
```python
# utils.py
from pathlib import Path
from typing import List

# __init__.py  
from .models import FormatterConfig, FormatterResult, FileChange
from .black_formatter import format_with_black
from .isort_formatter import format_with_isort
```

## ALGORITHM
### Python File Discovery
```
1. Recursively find all .py files in target directories
2. Filter out __pycache__ and other non-source directories
3. Return list of Path objects for Python source files
4. Handle missing directories gracefully
```

## DATA
### Python File List
```python
[Path("src/module.py"), Path("tests/test_module.py"), ...]
```

### Main API Return
```python
{
    "black": FormatterResult(...),
    "isort": FormatterResult(...),
}
```

## Tests Required
1. **Unit tests for utilities:**
   - Test Python file discovery in nested directories
   - Test filtering of non-Python files and cache directories
   - Test error handling for missing directories
   
2. **Integration tests for main API:**
   - Test `format_code()` with both formatters
   - Test individual formatter functions
   - Test with non-existent target directories
   - Test error handling (fail fast approach)

3. **Public API tests:**
   - Verify all expected functions/classes are exported
   - Test import statements work correctly
   - Test backwards compatibility of function signatures
