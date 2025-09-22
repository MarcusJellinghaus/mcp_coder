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
def capture_file_states(directories: List[Path]) -> Dict[Path, str]:
    """Capture SHA-256 hashes of Python files for change detection"""

def detect_changes(before_states: Dict[Path, str], directories: List[Path]) -> List[FileChange]:
    """Compare file states and generate FileChange objects with diffs"""
    
def get_python_files(directories: List[Path]) -> List[Path]:
    """Recursively find all .py files in given directories"""
    
def generate_unified_diff(file_path: Path, before_content: str, after_content: str) -> str:
    """Generate unified diff between before and after content"""
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
import hashlib
import difflib
from pathlib import Path
from typing import Dict, List
from .models import FileChange

# __init__.py  
from .models import FormatterConfig, FormatterResult, FileChange
from .black_formatter import format_with_black
from .isort_formatter import format_with_isort
```

## ALGORITHM
### File State Capture
```
1. Recursively find all .py files in target directories
2. Read each file's content and calculate SHA-256 hash
3. Return dict mapping file paths to content hashes
4. Handle file read errors gracefully
```

### Change Detection
```
1. Get current file states for same directories
2. Compare hashes to identify changed files
3. For changed files, read before/after content and generate diff
4. Create FileChange objects with diff information
5. Return list of all changes detected
```

## DATA
### File State Dictionary
```python
{Path("src/module.py"): "abc123def456...", ...}
```

### Unified Diff Format
- Standard unified diff with 3 lines context
- Include file paths in diff headers
- Handle binary files and encoding issues

### Main API Return
```python
{
    "black": FormatterResult(...),
    "isort": FormatterResult(...),
}
```

## Tests Required
1. **Unit tests for utilities:**
   - Test file state capture with various file types
   - Test change detection with modified/unchanged files
   - Test Python file discovery in nested directories
   - Test diff generation with various change types
   - Test error handling for unreadable files
   
2. **Integration tests for main API:**
   - Test `format_code()` with both formatters
   - Test `format_code()` with single formatter
   - Test with non-existent target directories
   - Test with empty directories
   - Test formatter execution order and independence
   - Test error aggregation from multiple formatters

3. **Public API tests:**
   - Verify all expected functions/classes are exported
   - Test import statements work correctly
   - Test backwards compatibility of function signatures
