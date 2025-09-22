# Step 3: Black Formatter Implementation

## LLM Prompt
```
Based on the Code Formatters Implementation Summary, implement Step 3: Create the Black formatter that can format Python files, detect changes, and provide detailed feedback. Use the simplified approach of running Black directly and comparing before/after states.
```

## WHERE
- `src/mcp_coder/formatters/black_formatter.py` - Black formatting implementation
- `src/mcp_coder/formatters/utils.py` - Common formatting utilities
- `tests/formatters/test_black_formatter.py` - Unit and integration tests
- `tests/formatters/test_data/sample_code/` - Sample Python files for testing

## WHAT
### Main Functions
```python
def format_with_black(project_root: Path, target_dirs: Optional[List[str]] = None) -> FormatterResult:
    """Format code using Black and return detailed results"""

def _capture_file_states(directories: List[Path]) -> Dict[Path, str]:
    """Capture content hashes of Python files before formatting"""
    
def _detect_changes(before_states: Dict[Path, str], directories: List[Path]) -> List[FileChange]:
    """Compare file states to detect what changed during formatting"""
    
def _build_black_command(config: FormatterConfig) -> List[str]:
    """Build Black command with configuration options"""
```

## HOW
### Integration Points
- Use `execute_command` from `subprocess_runner.py`
- Import `FormatterConfig`, `FormatterResult`, `FileChange` from models
- Use `get_black_config` from config_reader
- Import `hashlib` for content hashing

### Dependencies
```python
import hashlib
import time
from pathlib import Path
from typing import Dict, List, Optional
from ..utils.subprocess_runner import execute_command
from .models import FormatterConfig, FormatterResult, FileChange
from .config_reader import get_black_config
```

## ALGORITHM
```
1. Load Black configuration from pyproject.toml
2. Capture content hashes of all Python files in target directories
3. Build and execute Black command using subprocess_runner
4. Compare file states to detect changes
5. Generate FileChange objects for modified files with diffs
6. Return FormatterResult with success status and change details
```

## DATA
### Command Building
- Base command: `["black"]`
- Add `--line-length` from config
- Add `--target-version` from config  
- Add target directories as arguments

### File Detection
- Find `.py` files recursively in target directories
- Calculate SHA-256 hash of file content for comparison
- Generate unified diff for changed files

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
   - Test formatting unformatted Python code
   - Test formatting already formatted code (no changes)
   - Test with missing target directories
   - Test with invalid Python syntax
   - Test with custom Black configuration
   - Test error handling when Black fails
