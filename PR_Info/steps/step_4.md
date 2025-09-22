# Step 4: isort Formatter Implementation

## LLM Prompt
```
Based on the Code Formatters Implementation Summary, implement Step 4: Create the isort formatter using isort's Python API for efficient import sorting. This should integrate with pyproject.toml configuration and provide the same detailed feedback as the Black formatter.
```

## WHERE
- `src/mcp_coder/formatters/isort_formatter.py` - isort formatting implementation  
- `tests/formatters/test_isort_formatter.py` - Unit and integration tests
- Update `tests/formatters/test_data/sample_code/` - Add files with unsorted imports

## WHAT
### Main Functions
```python
def format_with_isort(project_root: Path, target_dirs: Optional[List[str]] = None) -> FormatterResult:
    """Format imports using isort API and return detailed results"""

def _apply_isort_to_files(py_files: List[Path], isort_config) -> List[FileChange]:
    """Apply isort to files using isort.api.sort_file() and detect changes"""
    
def _convert_config_to_isort_settings(config: FormatterConfig):
    """Convert FormatterConfig to isort.Config object"""
```

## HOW
### Integration Points
- Import `isort.api` and `isort.Config` for programmatic access
- Use same change detection pattern as Black formatter
- Reuse `_capture_file_states` and `_detect_changes` from utils.py
- Use `get_isort_config` from config_reader

### Dependencies
```python
import isort
import isort.api
from pathlib import Path
from typing import List, Optional
from .models import FormatterConfig, FormatterResult, FileChange
from .config_reader import get_isort_config
```

## ALGORITHM
```
1. Load isort configuration from pyproject.toml  
2. Convert config to isort.Config object
3. Find all Python files in target directories
4. Apply isort.api.sort_file() to each file (returns whether file changed)
5. Collect FileChange objects for files that were modified
6. Return FormatterResult with success status and change list
```

## DATA
### isort Configuration Mapping
- `profile` → `isort.Config(profile=value)`
- `line_length` → `isort.Config(line_length=value)`
- `float_to_top` → `isort.Config(float_to_top=value)`
- Additional settings from pyproject.toml as needed

### isort API Usage
```python
# Sort file and detect if it changed
changed = isort.api.sort_file(file_path, config=isort_config)
# Returns True if file was modified, False if no changes needed
```

### Return Values
- `FormatterResult` with:
  - `success: True` (isort API rarely fails, handles errors gracefully)
  - `files_changed: List[FileChange]` - Files with import changes
  - `execution_time_ms: int` - Time taken for sorting
  - `formatter_name: "isort"`
  - `error_message: Optional[str]` - If unexpected errors occur

## Tests Required
1. **Unit tests (mocked):**
   - Test configuration conversion to isort settings
   - Test Python file discovery logic
   - Test change detection with mock files
   
2. **Integration tests (formatter_integration marker):**
   - Test sorting unsorted imports
   - Test sorting already sorted imports (no changes)
   - Test with float_to_top configuration
   - Test with profile="black" compatibility
   - Test with mixed import styles (relative, absolute, third-party)
   - Test error handling with syntax errors in imports
   - Test with custom isort configuration from pyproject.toml
