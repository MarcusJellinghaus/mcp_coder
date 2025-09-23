# Step 2: Black Formatter Implementation

## LLM Prompt
```
Based on the Step 0 analysis findings, implement Step 2 using TDD: First write comprehensive unit and integration tests for Black formatting using proven exit code change detection (0=no changes, 1=changes needed). Then implement the Black formatter using the two-phase approach (check first, format if needed) and inline config reading patterns discovered in Step 0.
```

## WHERE
- `tests/formatters/test_black_formatter.py` - **START HERE: Write unit and integration tests first (TDD)**
- `src/mcp_coder/formatters/black_formatter.py` - Black implementation with inline config (implement after tests)

## WHAT
### Main Functions
```python
def format_with_black(project_root: Path, target_dirs: Optional[List[str]] = None) -> FormatterResult:
    """Format code using proven Black CLI patterns with exit code detection"""

def _get_black_config(project_root: Path) -> dict:
    """Read Black configuration inline using validated tomllib patterns"""
    
def _check_black_changes(file_path: str, config: dict) -> bool:
    """Check if Black formatting needed using --check (exit code pattern)"""
    
def _apply_black_formatting(file_path: str, config: dict) -> bool:
    """Apply Black formatting and return success status"""
```

## HOW
### Integration Points
- Use `execute_command` from `subprocess_runner.py` for running Black CLI
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
1. Read Black configuration inline using validated tomllib pattern
2. Determine target files/directories to process
3. For each file:
   a. Check if formatting needed: black --check {file} (exit 0=no changes, 1=changes needed)
   b. If changes needed (exit 1): apply formatting: black {file}
   c. If error (exit 123+): collect error message from stderr
4. Collect all files that were actually changed
5. Return FormatterResult with success status and changed file list
```

## DATA
### Black Configuration Defaults
```python
{
    "line-length": 88,
    "target-version": ["py311"]
}
```

### Target Directory Defaults
- Check if "src" directory exists, include if present
- Check if "tests" directory exists, include if present  
- If neither exists, default to ["."]

### Command Building (Analysis-Proven Patterns)
- Check command: `["black", "--check", file_path]` + config options
- Format command: `["black", file_path]` + config options
- Config options: `--line-length`, `--target-version` from pyproject.toml
- Let Black handle file discovery when given directories

### Change Detection (Based on Step 0 Analysis)
- Use exit codes for reliable change detection (no parsing needed):
  - Exit 0: No changes needed
  - Exit 1: Changes were needed/applied
  - Exit 123+: Syntax errors or other failures
- Two-phase approach: check first, then format only if needed
- Track files that actually get formatted (exit 1 → format → success)
- Much more reliable than output parsing or file modification tracking

### Return Values
- `FormatterResult` with:
  - `success: bool` - Based on Black exit code (0 = success)
  - `files_changed: List[str]` - Files that were modified
  - `formatter_name: "black"`
  - `error_message: Optional[str]` - If Black failed

## Tests Required (TDD - Write 6 Tests First!)
1. **Core formatting scenarios (3 tests)**
   - Unformatted code: Test format_with_black() on code needing formatting (exit 1 → success)
   - Already formatted: Test on properly formatted code (exit 0 → no changes)
   - Syntax error: Test error handling with malformed code (exit 123 → error)

2. **Configuration integration (2 tests)**
   - Default config: Test with missing pyproject.toml (use Black defaults)
   - Custom config: Test with custom line-length and target-version from pyproject.toml

3. **Real-world analysis scenario (1 test)**
   - Analysis code sample: Use actual unformatted code from Step 0 findings to verify patterns
