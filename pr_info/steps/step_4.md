# Step 4: Update `coordinator.py` to Use `load_config()`

## LLM Prompt

```
Read pr_info/steps/summary.md for context, then implement Step 4.

Update `coordinator.py` to use `load_config()` from `user_config.py` instead of 
direct `tomllib.load()` call. This ensures consistent error handling across the codebase.
```

## WHERE

- **Implementation file**: `src/mcp_coder/cli/commands/coordinator.py`
- **Test file**: `tests/cli/commands/test_coordinator.py` (verify existing tests still pass)

## WHAT

### Change Location

In `execute_coordinator_run()` function, around lines 545-551:

**Before:**
```python
elif args.all:
    # All repositories mode - extract from config
    import tomllib

    config_path = get_config_file_path()
    with open(config_path, "rb") as f:
        config_data = tomllib.load(f)

    repos_section = config_data.get("coordinator", {}).get("repos", {})
```

**After:**
```python
elif args.all:
    # All repositories mode - extract from config
    from ...utils.user_config import load_config

    config_data = load_config()

    repos_section = config_data.get("coordinator", {}).get("repos", {})
```

## HOW

### Import Changes

**Remove from function body:**
```python
import tomllib
```

**Add to function body (or move to module-level imports):**
```python
from ...utils.user_config import load_config
```

**Option**: Move import to module-level with existing imports:
```python
from ...utils.user_config import (
    create_default_config,
    get_config_file_path,
    get_config_value,
    load_config,  # ADD THIS
)
```

### Error Handling

The existing `except ValueError as e:` block at line 580 already handles ValueError:
```python
except ValueError as e:
    # User-facing errors (config issues)
    print(f"Error: {e}", file=sys.stderr)
    logger.error(f"Configuration error: {e}")
    return 1
```

This will now catch the formatted error message from `load_config()`.

## ALGORITHM

```
1. Remove direct tomllib import
2. Import load_config from user_config
3. Replace tomllib.load() call with load_config()
4. Remove get_config_file_path() call (load_config handles it)
5. Rest of logic unchanged - repos_section extraction works the same
```

## DATA

### Behavior Change

| Scenario | Before | After |
|----------|--------|-------|
| Valid config | Works | Works (unchanged) |
| Invalid TOML | Generic tomllib error | Formatted error with file path and context |
| Missing config | FileNotFoundError | Empty dict (handled by "No repositories" check) |

### Error Output Change

**Before:**
```
Error: Illegal character '\n' (at line 25, column 49)
Configuration error: Illegal character '\n' (at line 25, column 49)
```

**After:**
```
Error:   File "C:\Users\me\.mcp_coder\config.toml", line 25
    executor_os = "linux
                       ^
TOML parse error: Illegal character '\n'
Configuration error: ...
```

## TESTS

No new tests needed - this is integration of existing functionality.

### Verify Existing Tests Pass

Run: `pytest tests/cli/commands/test_coordinator.py -v`

The existing tests mock `get_config_value()` and don't test the `--all` path with invalid TOML, so they should continue to pass.

## IMPLEMENTATION NOTES

1. Prefer module-level import for consistency with other imports
2. Remove unused `config_path` variable (no longer needed)
3. The error handling is already in place - no changes needed there
4. Test manually with a broken config file to verify the improved error message
