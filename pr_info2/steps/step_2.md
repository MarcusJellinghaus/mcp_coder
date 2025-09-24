# Step 2: Refactor isort Formatter to Directory-Based Approach

## LLM Prompt
```
Based on the refactor summary in `pr_info2/steps/summary.md` and following the same pattern as Step 1, implement Step 2 using TDD: First update the isort formatter tests to expect directory-based formatting calls. Then refactor the isort formatter implementation to pass directories directly to isort CLI and parse output to determine changed files, eliminating the custom `find_python_files()` usage.
```

## WHERE
- `tests/formatters/test_isort_formatter.py` - **START HERE: Update tests first (TDD)**
- `src/mcp_coder/formatters/isort_formatter.py` - Refactor implementation after tests

## WHAT
### Main Functions (Updated Signatures)
```python
def format_with_isort(project_root: Path, target_dirs: Optional[List[str]] = None) -> FormatterResult:
    """Format imports using directory-based isort CLI approach"""

def _format_isort_directory(target_path: Path, config: Dict[str, Any]) -> List[str]:
    """Format directory imports and return list of changed files from parsed output"""

def _parse_isort_output(stdout: str) -> List[str]:
    """Parse isort output to extract list of files that were fixed"""
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
   a. Run: isort {directory} (single command)
   b. Parse stdout to extract list of fixed files
   c. Add parsed files to changed_files list
2. Return FormatterResult with success and changed_files
```

## DATA
### Command Patterns (Simplified)
```python
# Single format command for directory
format_cmd = ["isort", str(target_path)] + config_options
```

### Output Parsing Pattern
```python
def _parse_isort_output(stdout: str) -> List[str]:
    """Parse 'Fixing {filename}' lines from isort stdout"""
    changed_files = []
    for line in stdout.strip().split('\n'):
        if line.startswith('Fixing '):
            # Extract filename from "Fixing /path/to/file.py"
            filename = line[7:]  # Remove "Fixing " prefix
            changed_files.append(filename)
    return changed_files
```

### Return Values (Unchanged)
- `FormatterResult` with same structure:
  - `success: bool` - Based on isort exit code success
  - `files_changed: List[str]` - Files that were modified (from parsed output)
  - `formatter_name: "isort"`
  - `error_message: Optional[str]` - If isort command failed

## Tests Required (TDD - Focused Testing)
1. **Core import sorting test (1 test)**
   - Test single-phase directory-based isort execution
   - Mock `execute_command` with directory paths
   - Verify output parsing extracts changed files correctly

2. **Configuration test (1 test)**
   - Test config reading and options passed to directory command
   - Verify line-length and profile settings applied

3. **Error handling test (1 test)**
   - Test command failure scenarios (syntax errors, permissions)
   - Verify proper error reporting in FormatterResult

4. **Output parsing test (1 test)**
   - Test `_parse_isort_output()` with various isort stdout formats
   - Handle edge cases: no changes, multiple files, paths with spaces
