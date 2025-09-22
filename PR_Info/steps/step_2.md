# Step 2: Configuration Reader Implementation

## LLM Prompt
```
Based on the Code Formatters Implementation Summary, implement Step 2: Create a configuration reader that parses pyproject.toml to extract Black and isort settings. This should provide a clean interface for accessing tool configurations with proper defaults.
```

## WHERE
- `src/mcp_coder/formatters/config_reader.py` - Configuration parsing logic
- `tests/formatters/test_config_reader.py` - Unit tests for config parsing
- `tests/formatters/test_data/` - Test pyproject.toml files

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

## Tests Required
1. Test parsing valid pyproject.toml with both tool sections
2. Test parsing with missing tool sections (should use defaults)
3. Test parsing with missing pyproject.toml file
4. Test parsing with malformed TOML
5. Test default configuration application
6. Test target directory detection (only existing directories)
7. Test integration with actual project pyproject.toml
