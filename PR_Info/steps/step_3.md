# Step 3: Black Formatter Implementation

## LLM Prompt
```
Based on the Code Formatters Implementation Summary, implement Step 3 using TDD: First write comprehensive unit and integration tests for Black formatting with stdout parsing for change detection. Then implement the Black formatter to pass the tests using simplified tool output parsing instead of file modification times.
```

## WHERE
- `tests/formatters/test_black_formatter.py` - **START HERE: Write unit and integration tests first (TDD)**
- `tests/formatters/test_data/sample_code/` - Sample Python files for testing (unformatted code)
- `src/mcp_coder/formatters/black_formatter.py` - Black implementation with stdout parsing (implement after tests)
- **Note**: Inline `get_python_files()` utility directly in this file (no separate utils.py)

## WHAT
### Main Functions
```python
def format_with_black(project_root: Path, target_dirs: Optional[List[str]] = None) -> FormatterResult:
    """Format code using Black and return detailed results"""

# Note: _get_python_files will be moved to utils.py in step 5
    
def _parse_black_output(stdout: str) -> List[Path]:
    """Parse Black stdout to find files that were reformatted"""
    # Parse lines like 'reformatted /path/to/file.py'
    
def _build_black_command(config: FormatterConfig) -> List[str]:
    """Build Black command with configuration options"""
```

## HOW
### Integration Points
- Use `execute_command` from `subprocess_runner.py`
- Import `FormatterConfig`, `FormatterResult`, `FileChange` from models
- Use `get_black_config` from config_reader
- No content hashing needed (using modification time approach)

### Dependencies
```python
import re
from pathlib import Path
from typing import List, Optional
from ..utils.subprocess_runner import execute_command
from .models import FormatterConfig, FormatterResult, FileChange
from .config_reader import get_black_config
```

## ALGORITHM
```
1. Load Black configuration from pyproject.toml
2. Get list of Python files in target directories (inline utility function)
3. Build and execute Black command using subprocess_runner
4. Parse Black's stdout for 'reformatted file.py' lines
5. Create FileChange objects for reformatted files
6. Return FormatterResult with success status and parsed change list
```

## DATA
### Command Building
- Base command: `["black"]`
- Add `--line-length` from config
- Add `--target-version` from config  
- Add target directories as arguments

### Change Detection (Updated Approach)
- Parse Black stdout for lines containing 'reformatted'
- Extract file paths from formatted output lines
- Create FileChange objects for each reformatted file
- Much simpler than file modification time tracking
- More accurate since it comes directly from Black

### Return Values
- `FormatterResult` with:
  - `success: bool` - Based on Black exit code
  - `files_changed: List[FileChange]` - Files that were modified
  - `execution_time_ms: int` - Time taken for formatting
  - `formatter_name: "black"`
  - `error_message: Optional[str]` - If Black failed

## Tests Required
1. **Unit tests (mocked):**
   - Test command building with different configurations
   - Test file state capturing logic
   - Test change detection logic
   
2. **Integration tests (formatter_integration marker):**
   - Test formatting unformatted Python code (parse 'reformatted' output)
   - Test formatting already formatted code (no 'reformatted' output)
   - Test with missing target directories
   - Test with invalid Python syntax (Black error handling)
   - Test with custom Black configuration from pyproject.toml
   - Test stdout parsing with various Black output formats
   - Test error handling when Black command fails
