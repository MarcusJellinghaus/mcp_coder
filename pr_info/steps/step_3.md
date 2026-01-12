# Step 3: Refactor data_files.py

## LLM Prompt
```
Read pr_info/steps/summary.md for context, then implement Step 3.
Replace structlog with standard logging in data_files.py.
Convert all structured_logger calls to logger calls with extra={}.
Merge consecutive log calls only where obviously cleaner.
```

## WHERE
- **File**: `src/mcp_coder/utils/data_files.py`

## WHAT

### Import Changes
| Line | Before | After |
|------|--------|-------|
| 17 | `import structlog` | (remove) |
| 20 | `structured_logger = structlog.get_logger(__name__)` | (remove) |

Keep: `logger = logging.getLogger(__name__)` (line 19)

### Log Call Conversion Pattern

**Before** (structlog kwargs style):
```python
structured_logger.debug(
    "METHOD 1/5: Searching development environment",
    method="development",
    base_dir=str(development_base_dir),
)
```

**After** (standard logging extra style):
```python
logger.debug(
    "METHOD 1/5: Searching development environment",
    extra={"method": "development", "base_dir": str(development_base_dir)},
)
```

## HOW

### Conversion Rules

1. **Simple kwargs to extra**: `structured_logger.debug(msg, key=val)` → `logger.debug(msg, extra={"key": val})`

2. **Multiple kwargs**: `structured_logger.debug(msg, a=1, b=2)` → `logger.debug(msg, extra={"a": 1, "b": 2})`

3. **Level changes**: Keep same log levels (debug, info, error)

4. **Message unchanged**: Keep the same log message strings

### Merging Policy (Decision 4)

**Rule: Merge only identical messages on literally adjacent lines.**

Only merge where two consecutive calls have the exact same message string:
```python
# Before - identical messages on adjacent lines (MERGE)
structured_logger.debug("Starting search", package=pkg)
structured_logger.debug("Starting search", path=path)

# After - merged
logger.debug("Starting search", extra={"package": pkg, "path": path})
```

Do NOT merge:
- Calls with different messages (even if related)
- Calls that represent different steps or phases
- Calls separated by any other code

This preserves debuggability and keeps the diff minimal.

## ALGORITHM

```python
# Conversion pseudocode for each log call:
for each structured_logger.LEVEL(message, **kwargs):
    if kwargs is empty:
        logger.LEVEL(message)
    else:
        logger.LEVEL(message, extra={**kwargs})
```

## DATA

No data structure changes. Log output format changes from structlog to standard logging.

### Approximate Call Count by Type
- `structured_logger.debug()` - ~40 calls
- `structured_logger.info()` - ~3 calls  
- `structured_logger.error()` - ~2 calls

## FUNCTIONS AFFECTED

All log calls are in these functions:
1. `find_data_file()` - Main function, ~43 log calls
2. `get_package_directory()` - ~2 log calls

## IMPLEMENTATION CHECKLIST

- [ ] Remove `import structlog` line
- [ ] Remove `structured_logger = structlog.get_logger(__name__)` line
- [ ] Convert all `structured_logger.debug()` to `logger.debug()` with `extra={}`
- [ ] Convert all `structured_logger.info()` to `logger.info()` with `extra={}`
- [ ] Convert all `structured_logger.error()` to `logger.error()` with `extra={}`
- [ ] Verify no remaining references to `structured_logger`
- [ ] Run pylint: `pylint src/mcp_coder/utils/data_files.py`

## EXAMPLE CONVERSIONS

### Example 1: Simple debug call
```python
# Before
structured_logger.debug(
    "SEARCH STARTED: Looking for data file using 5 methods",
    package_name=package_name,
    relative_path=relative_path,
    development_base_dir=(
        str(development_base_dir) if development_base_dir else None
    ),
    methods="1=Development, 2=ImportLib, 3=Module __file__, 4=Site-packages, 5=Virtual Env",
)

# After
logger.debug(
    "SEARCH STARTED: Looking for data file using 5 methods",
    extra={
        "package_name": package_name,
        "relative_path": relative_path,
        "development_base_dir": (
            str(development_base_dir) if development_base_dir else None
        ),
        "methods": "1=Development, 2=ImportLib, 3=Module __file__, 4=Site-packages, 5=Virtual Env",
    },
)
```

### Example 2: Error call
```python
# Before
structured_logger.error(
    "SEARCH COMPLETE: Data file not found in any location",
    package_name=package_name,
    relative_path=relative_path,
    search_locations=search_locations,
    search_results=search_results,
    development_base_dir=(
        str(development_base_dir) if development_base_dir else None
    ),
)

# After
logger.error(
    "SEARCH COMPLETE: Data file not found in any location",
    extra={
        "package_name": package_name,
        "relative_path": relative_path,
        "search_locations": search_locations,
        "search_results": search_results,
        "development_base_dir": (
            str(development_base_dir) if development_base_dir else None
        ),
    },
)
```
