# Step 5: Main API Implementation

## LLM Prompt
```
Based on the Code Formatters Implementation Summary, implement Step 5 using TDD: First write comprehensive unit and integration tests for the main API functions, then implement the simple combined format_code() wrapper and clean exports in __init__.py. No separate utils.py needed.
```

## WHERE
- `tests/formatters/test_main_api.py` - **START HERE: Write unit and integration tests first (TDD)**
- `src/mcp_coder/formatters/__init__.py` - Main API exports and simple combined function (implement after tests)
- **Note**: No separate utils.py file needed - utilities are inlined in formatter files

## WHAT
### Utility Functions (Inlined)
```python
# This function is now inlined in black_formatter.py and isort_formatter.py
# No separate utils.py file needed
def _get_python_files(directories: List[Path]) -> List[Path]:
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
- Import all formatter implementations for re-export
- Import all data models for public API
- Simple combined function calls individual formatters
- Clean, minimal API surface

### Dependencies
```python
# __init__.py only
from .models import FormatterConfig, FormatterResult, FileChange
from .black_formatter import format_with_black
from .isort_formatter import format_with_isort
from typing import Dict, List, Optional
from pathlib import Path
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

## Tests Required (TDD - Write These First!)
1. **Combined API function tests:**
   - Test `format_code()` with both formatters (default behavior)
   - Test `format_code()` with specific formatters list
   - Test `format_code()` with custom target directories
   - Test aggregated results from multiple formatters
   - Test error handling when one formatter fails
   
2. **Individual formatter re-export tests:**
   - Test `format_with_black()` import and execution
   - Test `format_with_isort()` import and execution
   - Verify functions work identically to direct imports

3. **Public API and exports:**
   - Verify all expected functions/classes are exported
   - Test import statements work correctly (`from mcp_coder.formatters import ...`)
   - Test that all models are accessible
   - Test that __all__ list is complete and accurate
