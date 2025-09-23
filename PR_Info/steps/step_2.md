# Step 2: Black Formatter Implementation

## LLM Prompt
```
Based on the Step 0 analysis findings, implement Step 2 using TDD: First write comprehensive unit and integration tests for Black formatting with CLI and stdout parsing for change detection. Then implement the Black formatter to pass the tests using tool output parsing patterns discovered in Step 0.
```

## WHERE
- `tests/formatters/test_black_formatter.py` - **START HERE: Write unit and integration tests first (TDD)**
- `src/mcp_coder/formatters/black_formatter.py` - Black implementation with inline config (implement after tests)

## WHAT
### Main Functions
```python
def format_with_black(project_root: Path, target_dirs: Optional[List[str]] = None) -> FormatterResult:
    """Format code using Black CLI and return detailed results"""

def _get_black_config(project_root: Path) -> dict:
    """Read Black configuration inline from pyproject.toml"""
    
def _parse_black_output(stdout: str) -> List[str]:
    """Parse Black stdout to find files that were reformatted"""
    
def _build_black_command(config: dict, target_dirs: List[str]) -> List[str]:
    """Build Black command with configuration options"""
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
from typing import List, Optional
from . import FormatterResult
```

## ALGORITHM
```
1. Read Black configuration inline from pyproject.toml (with defaults)
2. Determine target directories (default to ["src", "tests"] if exist, else ["."]) 
3. Build Black CLI command with configuration options
4. Execute Black command using subprocess
5. Parse Black stdout for "reformatted file.py" patterns (from Step 0 analysis)
6. Return FormatterResult with success status and list of changed files
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

### Command Building
- Base command: `["black"]`
- Add `--line-length` from config
- Add `--target-version` from config  
- Add target directories as final arguments

### Change Detection (Based on Step 0 Analysis)
- Parse Black stdout for lines containing "reformatted"
- Extract file paths from formatted output lines
- Create list of changed file paths for FormatterResult
- Much simpler and more accurate than file modification tracking

### Return Values
- `FormatterResult` with:
  - `success: bool` - Based on Black exit code (0 = success)
  - `files_changed: List[str]` - Files that were modified
  - `formatter_name: "black"`
  - `error_message: Optional[str]` - If Black failed

## Tests Required (TDD - Write These First!)
1. **Unit tests (mocked subprocess):**
   - Test command building with different configurations
   - Test Black output parsing with Step 0 analysis patterns
   - Test config reading with various pyproject.toml scenarios
   - Test target directory determination logic
   
2. **Integration tests (formatter_integration marker):**
   - Test formatting unformatted Python code (expect "reformatted" output)
   - Test formatting already formatted code (expect no "reformatted" output)
   - Test with missing target directories
   - Test with invalid Python syntax (Black error handling)
   - Test with custom Black configuration from pyproject.toml
   - Test error handling when Black command fails
   
3. **Configuration tests:**
   - Missing pyproject.toml file (use defaults)
   - Missing tool.black section (use defaults)
   - Custom line-length and target-version settings
   - Invalid configuration values (graceful handling)
   
4. **Real-world scenarios (based on Step 0 findings):**
   - Multiple files with mixed formatting needs
   - Files that don't need formatting
   - Syntax error handling
   - Various Black stdout/stderr patterns
