# Step 3: isort Formatter Implementation

## LLM Prompt
```
Based on the Step 0 analysis findings, implement Step 3 using TDD: First write comprehensive unit and integration tests for isort formatting with CLI and stdout parsing for change detection. Then implement the isort formatter to pass the tests using tool output parsing patterns discovered in Step 0.
```

## WHERE
- `tests/formatters/test_isort_formatter.py` - **START HERE: Write unit and integration tests first (TDD)**
- `src/mcp_coder/formatters/isort_formatter.py` - isort implementation with inline config (implement after tests)

## WHAT
### Main Functions
```python
def format_with_isort(project_root: Path, target_dirs: Optional[List[str]] = None) -> FormatterResult:
    """Format imports using isort CLI and return detailed results"""

def _get_isort_config(project_root: Path) -> dict:
    """Read isort configuration inline from pyproject.toml"""
    
def _parse_isort_output(stdout: str) -> List[str]:
    """Parse isort stdout to find files that were modified"""
    
def _build_isort_command(config: dict, target_dirs: List[str]) -> List[str]:
    """Build isort command with configuration options"""
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
from typing import List, Optional
from . import FormatterResult
```

## ALGORITHM
```
1. Read isort configuration inline from pyproject.toml (with defaults)
2. Determine target directories (default to ["src", "tests"] if exist, else ["."]) 
3. Build isort CLI command with configuration options
4. Execute isort command using subprocess
5. Parse isort stdout for change indication patterns (from Step 0 analysis)
6. Return FormatterResult with success status and list of changed files
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

### Command Building
- Base command: `["isort"]`
- Add `--profile` from config
- Add `--line-length` from config
- Add `--float-to-top` from config if True
- Add target directories as final arguments

### Change Detection (Based on Step 0 Analysis)
- Parse isort stdout for change indication patterns
- Extract file paths that were modified
- Create list of changed file paths for FormatterResult
- Reliable detection based on actual tool output

### Return Values
- `FormatterResult` with:
  - `success: bool` - Based on isort exit code (0 = success)
  - `files_changed: List[str]` - Files that were modified
  - `formatter_name: "isort"`
  - `error_message: Optional[str]` - If isort failed

## Tests Required (TDD - Write These First!)
1. **Unit tests (mocked subprocess):**
   - Test command building with different configurations
   - Test isort output parsing with Step 0 analysis patterns
   - Test config reading with various pyproject.toml scenarios
   - Test target directory determination logic
   
2. **Integration tests (formatter_integration marker):**
   - Test sorting unsorted imports (expect change indication in output)
   - Test sorting already sorted imports (expect no change indication)
   - Test with float_to_top configuration
   - Test with profile="black" compatibility
   - Test with mixed import styles (relative, absolute, third-party)
   - Test error handling with syntax errors in imports
   - Test with custom isort configuration from pyproject.toml
   
3. **Configuration tests:**
   - Missing pyproject.toml file (use defaults)
   - Missing tool.isort section (use defaults)
   - Custom profile and line_length settings
   - Invalid configuration values (graceful handling)
   
4. **Real-world scenarios (based on Step 0 findings):**
   - Multiple files with mixed import organization needs
   - Files with already sorted imports
   - Various isort stdout/stderr patterns
   - Integration with Black line-length settings
