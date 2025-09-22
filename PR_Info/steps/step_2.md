# Step 2: Configuration Reader Implementation

## LLM Prompt
```
Based on the Code Formatters Implementation Summary, implement Step 2 using TDD: First write comprehensive unit tests for configuration reading from pyproject.toml, including edge cases and line-length conflict warnings. Then implement minimal config reader functions to pass the tests.
```

## WHERE
- `tests/formatters/test_config_reader.py` - **START HERE: Write unit tests first (TDD)**
- `tests/formatters/test_data/` - Test pyproject.toml files for various scenarios
- `src/mcp_coder/formatters/config_reader.py` - Minimal configuration parsing (implement after tests)

## WHAT
### Main Functions
```python
def read_formatter_config(project_root: Path, formatter_name: str) -> FormatterConfig:
    """Read configuration for a specific formatter from pyproject.toml"""

def get_black_config(project_root: Path) -> FormatterConfig:
    """Get Black-specific configuration with defaults"""
    
def get_isort_config(project_root: Path) -> FormatterConfig:
    """Get isort-specific configuration with defaults"""

def parse_pyproject_toml(toml_path: Path) -> Dict[str, Any]:
    """Parse pyproject.toml file safely"""
```

## HOW
### Integration Points
- Import `tomllib` (Python 3.11+ standard library)
- Use `FormatterConfig` from models.py
- Handle missing files gracefully with defaults

### Dependencies
```python
import tomllib
from pathlib import Path
from typing import Dict, Any, List
from .models import FormatterConfig
```

## ALGORITHM
```
1. Check if pyproject.toml exists, use defaults if missing
2. Parse TOML file using tomllib
3. Extract tool-specific section (tool.black, tool.isort)
4. Apply defaults for missing configuration keys
5. Return FormatterConfig with parsed settings and target directories
```

## DATA
### Default Configurations
**Black defaults:**
```python
{
    "line-length": 88,
    "target-version": ["py311"],
    "target_directories": ["src", "tests"]
}
```

**isort defaults:**
```python
{
    "profile": "black", 
    "line_length": 88,
    "float_to_top": True,
    "target_directories": ["src", "tests"]
}
```

### Return Values
- `FormatterConfig` objects with tool-specific settings
- Empty dict if pyproject.toml missing or malformed
- Default target directories: `["src", "tests"]` (only existing ones)

### Configuration Validation
- **Simple warning implementation**: Check if `tool.black.line-length` != `tool.isort.line_length`
- Log warning message if conflict detected (~10 lines of code)
- No complex conflict resolution - just inform users of potential issues
- **Decision**: Implement as decided - helpful user feedback without complexity

## Tests Required (TDD - Write These First!)
1. **Valid pyproject.toml parsing**
   - Both tool.black and tool.isort sections present
   - Various configuration combinations
   - Custom line lengths, target versions, profiles

2. **Missing sections handling**
   - Missing tool.black section (use defaults)
   - Missing tool.isort section (use defaults)
   - Empty tool sections

3. **Missing pyproject.toml file**
   - Should return defaults gracefully
   - No errors thrown

4. **Line-length conflict warning** 
   - Different line-length values between Black/isort
   - Same line-length values (no warning)
   - Missing line-length in one tool (no warning)

5. **Target directory handling**
   - Default ["src", "tests"] when directories exist
   - Custom target directories from config
   - Non-existent directories filtered out

6. **Error handling**
   - Malformed TOML files
   - Invalid configuration values
   - Graceful degradation to defaults
