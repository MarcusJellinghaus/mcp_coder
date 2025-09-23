# Step 4: Combined API Implementation

## LLM Prompt
```
Based on Steps 2 and 3 implementations using analysis-proven patterns, implement Step 4 using TDD: First write comprehensive unit and integration tests for the combined API functions, then implement the simple format_code() wrapper and clean exports in __init__.py. Include the analysis-identified line-length conflict warning feature.
```

## WHERE
- `tests/formatters/test_main_api.py` - **START HERE: Write unit and integration tests first (TDD)**
- `src/mcp_coder/formatters/__init__.py` - Main API exports and combined function (implement after tests)

## WHAT
### Main API Functions
```python
def format_code(project_root: Path, formatters: List[str] = None, target_dirs: List[str] = None) -> Dict[str, FormatterResult]:
    """Run multiple formatters using analysis-proven patterns and return combined results"""
    
def format_with_black(project_root: Path, target_dirs: List[str] = None) -> FormatterResult:
    """Format code with Black (re-export from black_formatter with exit code detection)"""
    
def format_with_isort(project_root: Path, target_dirs: List[str] = None) -> FormatterResult:
    """Sort imports with isort (re-export from isort_formatter with exit code detection)"""

def _check_line_length_conflict(project_root: Path):
    """Warn about most common config conflict identified in analysis (~10 lines)"""
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
from typing import Dict, List, Optional, Any
from .black_formatter import format_with_black
from .isort_formatter import format_with_isort
```

## ALGORITHM (Based on Analysis Insights)
```
1. Define FormatterResult dataclass in __init__.py (using exit code patterns)
2. Import and re-export individual formatter functions (both use same patterns)
3. Implement simple format_code() that calls both formatters sequentially
4. Add line-length conflict warning function (analysis-identified issue)
5. Provide clean public API with proper exports
6. Include comprehensive tests for combined functionality using analysis scenarios
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

### Line-Length Conflict Warning (Analysis-Based)
```python
def _check_line_length_conflict(project_root: Path):
    """Warn about most common configuration conflict identified in Step 0 analysis"""
    try:
        with open(project_root / "pyproject.toml", "rb") as f:
            data = tomllib.load(f)
        
        black_config = data.get("tool", {}).get("black", {})
        isort_config = data.get("tool", {}).get("isort", {})
        
        black_length = black_config.get("line-length", 88)  # Black default
        isort_length = isort_config.get("line_length", 88)   # isort uses underscore
        
        if black_length != isort_length:
            print(f"⚠️  Line length mismatch: Black={black_length}, isort={isort_length}")
            print("   Consider setting isort.line_length to match Black's line-length")
    except (FileNotFoundError, tomllib.TOMLDecodeError):
        pass  # No warning if config can't be read
```

### Target Directory Defaults
- Same logic as individual formatters
- Default to ["src", "tests"] if exist, otherwise ["."]
- Allow override via function parameter

## Tests Required (TDD - Write 6 Tests First!)
1. **Combined API core functionality (3 tests)**
   - Both formatters: Test `format_code()` running Black + isort sequentially
   - Individual selection: Test `format_code(formatters=["black"])` runs only Black
   - Error handling: Test when one formatter fails, other still runs

2. **API exports and imports (2 tests)**
   - Re-exports: Verify `format_with_black()` and `format_with_isort()` work from __init__.py
   - Public API: Test all expected functions/classes are importable

3. **Line-length conflict integration (1 test)**
   - Warning display: Test that `format_code()` shows warning when Black/isort line lengths differ
