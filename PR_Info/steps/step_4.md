# Step 4: Combined API Implementation

## LLM Prompt
```
Based on Steps 2 and 3 implementations, implement Step 4 using TDD: First write comprehensive unit and integration tests for the combined API functions, then implement the simple format_code() wrapper and clean exports in __init__.py. Include line-length conflict warning feature.
```

## WHERE
- `tests/formatters/test_main_api.py` - **START HERE: Write unit and integration tests first (TDD)**
- `src/mcp_coder/formatters/__init__.py` - Main API exports and combined function (implement after tests)

## WHAT
### Main API Functions
```python
def format_code(project_root: Path, formatters: List[str] = None, target_dirs: List[str] = None) -> Dict[str, FormatterResult]:
    """Run multiple formatters and return combined results"""
    
def format_with_black(project_root: Path, target_dirs: List[str] = None) -> FormatterResult:
    """Format code with Black (re-export from black_formatter)"""
    
def format_with_isort(project_root: Path, target_dirs: List[str] = None) -> FormatterResult:
    """Sort imports with isort (re-export from isort_formatter)"""

def _check_line_length_conflict(project_root: Path):
    """Warn if Black and isort have different line lengths (~10 lines)"""
```

## HOW
### Integration Points
- Import both formatter implementations for re-export
- Import FormatterResult for type annotations
- Simple combined function calls individual formatters
- Clean, minimal API surface with line-length conflict warning

### Dependencies
```python
import tomllib
from pathlib import Path
from typing import Dict, List, Optional
from .black_formatter import format_with_black
from .isort_formatter import format_with_isort
```

## ALGORITHM
```
1. Define FormatterResult dataclass in __init__.py
2. Import and re-export individual formatter functions
3. Implement simple format_code() that calls both formatters
4. Add line-length conflict warning function
5. Provide clean public API with proper exports
6. Include comprehensive tests for combined functionality
```

## DATA
### FormatterResult Definition
```python
@dataclass
class FormatterResult:
    success: bool
    files_changed: List[str]
    formatter_name: str
    error_message: Optional[str] = None
```

### Combined API Return
```python
{
    "black": FormatterResult(...),
    "isort": FormatterResult(...),
}
```

### Line-Length Conflict Warning
```python
def _check_line_length_conflict(project_root: Path):
    """Simple warning when Black/isort line lengths differ"""
    try:
        with open(project_root / "pyproject.toml", "rb") as f:
            data = tomllib.load(f)
        
        black_length = data.get("tool", {}).get("black", {}).get("line-length", 88)
        isort_length = data.get("tool", {}).get("isort", {}).get("line_length", 88)
        
        if black_length != isort_length:
            print(f"WARNING: Black line-length ({black_length}) != isort line_length ({isort_length})")
    except (FileNotFoundError, tomllib.TOMLDecodeError):
        pass  # No warning if config can't be read
```

### Target Directory Defaults
- Same logic as individual formatters
- Default to ["src", "tests"] if exist, otherwise ["."]
- Allow override via function parameter

## Tests Required (TDD - Write These First!)
1. **Combined API function tests:**
   - Test `format_code()` with both formatters (default behavior)
   - Test `format_code()` with specific formatters list (["black"] only, ["isort"] only)
   - Test `format_code()` with custom target directories
   - Test aggregated results from multiple formatters
   - Test error handling when one formatter fails
   
2. **Individual formatter re-export tests:**
   - Test `format_with_black()` import and execution
   - Test `format_with_isort()` import and execution
   - Verify functions work identically to direct imports

3. **Line-length conflict warning tests:**
   - Test warning when Black/isort line lengths differ
   - Test no warning when line lengths match
   - Test no warning when config file missing
   - Test no warning when one tool section missing

4. **Public API and exports:**
   - Verify all expected functions/classes are exported
   - Test import statements work correctly (`from mcp_coder.formatters import ...`)
   - Test that FormatterResult is accessible
   - Test that __all__ list is complete and accurate

5. **Integration tests (formatter_integration marker):**
   - Test complete workflow: both formatters on real files
   - Test combined formatting with line-length conflicts
   - Test target directory handling in combined mode
   - Test error scenarios with both formatters
