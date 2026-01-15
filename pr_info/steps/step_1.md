# Step 1: Implement Simplified find_data_file with importlib.resources

## LLM Prompt
```
Read pr_info/steps/summary.md for context on Issue #285.
Implement Step 1: Rewrite find_data_file() to use importlib.resources.files().

Requirements:
- Use importlib.resources.files() as primary mechanism
- Keep development_base_dir parameter for backwards compatibility (log deprecation warning if used)
- Return Path for backwards compatibility
- Include verbose logging (~10+ statements) for troubleshooting
- Detailed error message with searched location
- ~50-80 lines total
```

## WHERE: File Paths

| File | Action |
|------|--------|
| `src/mcp_coder/utils/data_files.py` | MODIFY - rewrite `find_data_file` function |

## WHAT: Function Signature (unchanged)

```python
def find_data_file(
    package_name: str,
    relative_path: str,
    development_base_dir: Optional[Path] = None,
) -> Path:
    """Find a data file using importlib.resources (Python 3.9+ standard library)."""
```

## HOW: Integration Points

### Imports to Change
```python
# REMOVE these imports:
# - importlib.util
# - site
# - os (if no longer needed)

# ADD this import:
from importlib.resources import files
```

### Keep Existing
- `logging` import
- `Path` from pathlib
- `Optional` from typing
- Logger setup: `logger = logging.getLogger(__name__)`

## ALGORITHM: Core Logic (Pseudocode)

```python
def find_data_file(package_name, relative_path, development_base_dir=None):
    # 1. Log search start with parameters
    # 2. If development_base_dir provided, log deprecation warning
    # 3. Try importlib.resources.files(package_name).joinpath(relative_path)
    # 4. Convert Traversable to Path, check exists
    # 5. If exists: log success, return Path
    # 6. If not exists: raise FileNotFoundError with detailed message
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

### Deprecation Warning for development_base_dir

```python
if development_base_dir is not None:
    logger.warning(
        "development_base_dir parameter is deprecated. "
        "importlib.resources handles editable installs automatically. "
        "This parameter will be removed in a future version."
    )
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

## Verification

After implementation:
1. Run: `pytest tests/utils/test_data_files.py -v`
2. Verify `prompt_manager.py` still works: `pytest tests/test_prompt_manager.py -v`
