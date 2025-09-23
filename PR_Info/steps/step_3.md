# Step 3: isort Formatter Implementation

## LLM Prompt
```
Based on the Step 0 analysis findings, implement Step 3 using TDD: First write comprehensive unit and integration tests for isort formatting using proven exit code change detection (0=no changes, 1=changes needed). Then implement the isort formatter using the same two-phase approach as Black and inline config reading patterns discovered in Step 0.
```

## WHERE
- `tests/formatters/test_isort_formatter.py` - **START HERE: Write unit and integration tests first (TDD)**
- `src/mcp_coder/formatters/isort_formatter.py` - isort implementation with inline config (implement after tests)

## WHAT
### Main Functions
```python
def format_with_isort(project_root: Path, target_dirs: Optional[List[str]] = None) -> FormatterResult:
    """Format imports using proven isort CLI patterns with exit code detection"""

def _get_isort_config(project_root: Path) -> dict:
    """Read isort configuration inline using validated tomllib patterns"""
    
def _check_isort_changes(file_path: str, config: dict) -> bool:
    """Check if isort formatting needed using --check-only (exit code pattern)"""
    
def _apply_isort_formatting(file_path: str, config: dict) -> bool:
    """Apply isort formatting and return success status"""
```

## HOW
### Integration Points
- Use `subprocess` for running isort CLI
- Import `FormatterResult` from `__init__.py`
- Use findings from Step 0 analysis for parsing patterns
- Apply inline configuration reading approach

### Dependencies
```python
import subprocess
import tomllib
from pathlib import Path
from typing import List, Optional, Dict, Any
from . import FormatterResult
```

## ALGORITHM (Based on Step 0 Analysis)
```
1. Read isort configuration inline using validated tomllib pattern
2. Determine target files/directories to process
3. For each file:
   a. Check if sorting needed: isort --check-only {file} (exit 0=no changes, 1=changes needed)
   b. If changes needed (exit 1): apply sorting: isort {file}
   c. If error (exit 1 with stderr): collect error message
4. Collect all files that were actually changed
5. Return FormatterResult with success status and changed file list
```

## DATA
### isort Configuration Defaults
```python
{
    "profile": "black",
    "line_length": 88,
    "float_to_top": True
}
```

### Command Building (Analysis-Proven Patterns)
- Check command: `["isort", "--check-only", file_path]` + config options
- Sort command: `["isort", file_path]` + config options
- Config options: `--profile`, `--line-length`, `--float-to-top` from pyproject.toml
- Let isort handle file discovery when given directories

### Change Detection (Based on Step 0 Analysis)
- Use exit codes for reliable change detection (same pattern as Black):
  - Exit 0: No changes needed
  - Exit 1: Changes were needed/applied (or errors in some cases)
  - Check stderr to distinguish between changes and errors
- Two-phase approach: check first, then sort only if needed
- Track files that actually get sorted (exit 1 → sort → success)
- Consistent with Black formatter approach

### Return Values
- `FormatterResult` with:
  - `success: bool` - Based on isort exit code (0 = success)
  - `files_changed: List[str]` - Files that were modified
  - `formatter_name: "isort"`
  - `error_message: Optional[str]` - If isort failed

## Tests Required (TDD - Write These First!)
1. **Unit tests (mocked subprocess) based on analysis patterns:**
   - Test check command building with different configurations
   - Test sort command building with config options
   - Test exit code interpretation (0, 1 scenarios plus stderr analysis)
   - Test config reading with various pyproject.toml scenarios
   
2. **Integration tests (formatter_integration marker) using analysis scenarios:**
   - Test sorting unsorted imports (expect exit 1 → sort → success)
   - Test already sorted imports (expect exit 0 → no changes)
   - Test with syntax errors in imports (expect exit 1 + stderr)
   - Test with profile="black" compatibility
   - Test two-phase approach: check then sort only if needed
   
3. **Configuration tests using validated patterns:**
   - Missing pyproject.toml file (use defaults)
   - Missing tool.isort section (use defaults)
   - Custom profile and line_length settings
   - Black compatibility settings (profile="black")
   
4. **Real-world scenarios from Step 0 analysis:**
   - Use actual unsorted import samples from analysis
   - Test with import code that triggers different exit codes
   - Test error scenarios documented in analysis
   - Verify exit code patterns match analysis findings
   - Test line-length compatibility with Black settings
