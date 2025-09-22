# Step 4: isort Formatter Implementation

## LLM Prompt
```
Based on the Code Formatters Implementation Summary, implement Step 4 using TDD: First write comprehensive unit and integration tests for isort formatting using the Python API with direct change detection. Then implement the isort formatter to pass the tests using isort.api.sort_file() return values for change detection.
```

## WHERE
- `tests/formatters/test_isort_formatter.py` - **START HERE: Write unit and integration tests first (TDD)**
- `tests/formatters/test_data/sample_code/` - Add files with unsorted imports for testing
- `src/mcp_coder/formatters/isort_formatter.py` - isort implementation with API change detection (implement after tests)

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
- Use isort.api.sort_file() which returns change status directly (no complex change detection needed)
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
   - Test Python file discovery logic (reuse `_get_python_files` from Black formatter)
   - Test isort API integration (mocked)
   
2. **Integration tests (formatter_integration marker):**
   - **Use multiline strings for test file content** (like Black formatter tests)
   - **Create files dynamically in temp directories during tests**
   - Test sorting unsorted imports (verify `isort.api.sort_file()` returns True)
   - Test sorting already sorted imports (verify returns False)
   - Test with float_to_top configuration
   - Test with profile="black" compatibility
   - Test with mixed import styles (relative, absolute, third-party)
   - Test error handling with syntax errors in imports
   - Test with custom isort configuration from pyproject.toml
   - Test isort.Config object creation from FormatterConfig
   - Test file-by-file processing and change aggregation

### Test File Content Examples (Use as multiline strings in tests)
```python
# Unformatted imports content:
UNFORMATTED_IMPORTS = '''
import os
from pathlib import Path
import sys
from typing import List, Dict
import re
from collections import defaultdict
'''

# Well-formatted imports content:
FORMATTED_IMPORTS = '''
from collections import defaultdict
import os
from pathlib import Path
import re
import sys
from typing import Dict, List
'''

# Create files in tests like:
pyproject_content = '''[tool.isort]
profile = "black"
line_length = 88'''
(tmp_path / "pyproject.toml").write_text(pyproject_content)
test_file = src_dir / "test.py"
test_file.write_text(UNFORMATTED_IMPORTS)
```
