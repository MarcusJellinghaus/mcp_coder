# Step 1: Implement Simplified find_data_file with importlib.resources

## LLM Prompt
```
Read pr_info/steps/summary.md and pr_info/steps/Decisions.md for context on Issue #285.
Implement Step 1: Rewrite find_data_file() to use importlib.resources.files().

Requirements:
- Use importlib.resources.files() as primary mechanism
- Remove development_base_dir parameter entirely (Decision #6)
- Return Path for backwards compatibility
- Use Path(str(resource)) for Traversable to Path conversion (Decision #1)
- Catch ModuleNotFoundError and convert to FileNotFoundError (Decision #2)
- Include verbose logging (~10+ statements) for troubleshooting (Decision #3)
- Detailed error message with searched location
- ~50 lines total
```

## WHERE: File Paths

| File | Action |
|------|--------|
| `src/mcp_coder/utils/data_files.py` | MODIFY - rewrite `find_data_file` function |

## WHAT: Function Signature (CHANGED - parameter removed)

```python
def find_data_file(
    package_name: str,
    relative_path: str,
) -> Path:
    """Find a data file using importlib.resources (Python 3.9+ standard library)."""
```

## HOW: Integration Points

### Imports to Change
```python
# REMOVE these imports:
# - importlib.util
# - site
# - os
# - sys

# ADD this import:
from importlib.resources import files
```

### Keep Existing
- `logging` import
- `Path` from pathlib
- `List` from typing (for find_package_data_files)
- Logger setup: `logger = logging.getLogger(__name__)`

## ALGORITHM: Core Logic (Pseudocode)

```python
def find_data_file(package_name, relative_path):
    # 1. Log search start with parameters
    # 2. Try importlib.resources.files(package_name)
    #    - Catch ModuleNotFoundError -> raise FileNotFoundError (Decision #2)
    # 3. joinpath(relative_path) to get resource
    # 4. Convert Traversable to Path using Path(str(resource)) (Decision #1)
    # 5. Check if path exists
    # 6. If exists: log success, return Path
    # 7. If not exists: raise FileNotFoundError with detailed message
```

## DATA: Return Values

| Scenario | Return/Raise |
|----------|--------------|
| File found | `Path` object pointing to the file |
| File not found | `FileNotFoundError` with package name, relative path, and searched location |
| Package not found | `FileNotFoundError` with helpful message about package installation |

## Implementation Details

### Verbose Logging Requirements (~10+ statements)

```python
logger.debug("SEARCH STARTED: Looking for data file", extra={...})
logger.debug("Using importlib.resources.files() for package lookup", extra={...})
logger.debug("Resource traversable obtained", extra={...})
logger.debug("Constructed path from resource", extra={...})
logger.debug("Checking if path exists", extra={...})
logger.debug("SUCCESS: Found data file at %s", path)
# OR
logger.debug("FAILED: Path does not exist", extra={...})
logger.error("SEARCH COMPLETE: Data file not found", extra={...})
```

### Error Message Format

```python
raise FileNotFoundError(
    f"Data file '{relative_path}' not found for package '{package_name}'. "
    f"Searched location: {searched_path}. "
    f"Ensure the package is installed (pip install -e . for development) "
    f"and the file is declared in pyproject.toml under [tool.setuptools.package-data]."
)
```

## Additional Changes Required

### Update `find_package_data_files` (same file)

Remove `development_base_dir` parameter from this function too (Decision #12):

```python
def find_package_data_files(
    package_name: str,
    relative_paths: List[str],
) -> List[Path]:
```

### Update `prompt_manager.py` caller

Remove `development_base_dir=None` argument from two calls at lines 476 and 491:

```python
# Before:
resolved_file = find_data_file(
    package_name=package_name,
    relative_path=relative_path,
    development_base_dir=None,  # Remove this line
)

# After:
resolved_file = find_data_file(
    package_name=package_name,
    relative_path=relative_path,
)
```

## Verification

After implementation, use MCP tools:
1. Run: `mcp__code-checker__run_pytest_check` with `extra_args=["tests/utils/test_data_files.py", "-v"]`
2. Run: `mcp__code-checker__run_pytest_check` with `extra_args=["tests/test_prompt_manager.py", "-v"]`
3. Run: `mcp__code-checker__run_mypy_check` with `target_directories=["src/mcp_coder/utils"]`
