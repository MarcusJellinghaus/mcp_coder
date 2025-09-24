# Step 1: Refactor Black Formatter to Directory-Based Approach

## LLM Prompt
```
Based on the refactor summary in `pr_info2/steps/summary.md`, implement Step 1 using TDD: First update the Black formatter tests to expect directory-based formatting calls instead of file-by-file processing. Then refactor the Black formatter implementation to pass directories directly to Black CLI and parse output to determine changed files, eliminating the custom `find_python_files()` usage.
```

## WHERE
- `tests/formatters/test_black_formatter.py` - **START HERE: Update tests first (TDD)**
- `src/mcp_coder/formatters/black_formatter.py` - Refactor implementation after tests

## WHAT
### Main Functions (Updated Signatures)
```python
def format_with_black(project_root: Path, target_dirs: Optional[List[str]] = None) -> FormatterResult:
    """Format code using directory-based Black CLI approach"""

def _format_black_directory(target_path: Path, config: Dict[str, Any]) -> List[str]:
    """Format directory and return list of changed files from parsed output"""

def _parse_black_output(stdout: str) -> List[str]:
    """Parse Black output to extract list of files that were reformatted"""
```

## HOW
### Integration Points
- Remove imports: `from .utils import find_python_files`
- Keep imports: `execute_command`, `FormatterResult`, `get_default_target_dirs`, `read_tool_config`
- Update test mocks to expect directory commands instead of file commands
- Maintain same public API contract (`FormatterResult` unchanged)

### Dependencies (Updated)
```python
from pathlib import Path
from typing import Any, Dict, List, Optional
from mcp_coder.utils.subprocess_runner import execute_command
from .models import FormatterResult
from .utils import get_default_target_dirs, read_tool_config  # Remove find_python_files
```

## ALGORITHM
```
1. For each target directory:
   a. Run: black {directory} (single command)
   b. Parse stdout to extract list of reformatted files
   c. Add parsed files to changed_files list
2. Return FormatterResult with success and changed_files
```

## DATA
### Command Patterns (Simplified)
```python
# Single format command for directory
format_cmd = ["black", str(target_path)] + config_options
```

### Output Parsing Pattern
```python
def _parse_black_output(stdout: str) -> List[str]:
    """Parse 'reformatted {filename}' lines from Black stdout"""
    changed_files = []
    for line in stdout.strip().split('\n'):
        if line.startswith('reformatted '):
            # Extract filename from "reformatted /path/to/file.py"
            filename = line[12:]  # Remove "reformatted " prefix
            changed_files.append(filename)
    return changed_files
```

### Return Values (Unchanged)
- `FormatterResult` with same structure:
  - `success: bool` - Based on Black exit code success
  - `files_changed: List[str]` - Files that were modified (from parsed output)
  - `formatter_name: "black"`
  - `error_message: Optional[str]` - If Black command failed

## Tests Required (TDD - Focused Testing)
1. **Core formatting test (1 test)**
   - Test single-phase directory-based Black execution
   - Mock `execute_command` with directory paths
   - Verify output parsing extracts changed files correctly

2. **Configuration test (1 test)**
   - Test config reading and options passed to directory command
   - Verify line-length and other settings applied

3. **Error handling test (1 test)**
   - Test command failure scenarios (syntax errors, permissions)
   - Verify proper error reporting in FormatterResult

4. **Output parsing test (1 test)**
   - Test `_parse_black_output()` with various Black stdout formats
   - Handle edge cases: no changes, multiple files, paths with spaces
