# Step 1: Move `get_cache_refresh_minutes()` to utils/user_config.py

## LLM Prompt
```
Read pr_info/steps/summary.md for context on issue #358.

Implement Step 1: Move `get_cache_refresh_minutes()` from 
`cli/commands/coordinator/core.py` to `utils/user_config.py`.

This function belongs in the infrastructure layer since it reads 
user configuration. Moving it first allows the vscodeclaude module 
to import it directly without circular dependencies.
```

---

## WHERE

### Files to Modify
- `src/mcp_coder/utils/user_config.py` - Add function
- `src/mcp_coder/cli/commands/coordinator/core.py` - Remove function, add import
- `src/mcp_coder/cli/commands/coordinator/__init__.py` - Update re-export

### Test Files to Update
- `tests/utils/test_user_config.py` - Add tests for moved function
- `tests/cli/commands/coordinator/test_core.py` - Update patches

---

## WHAT

### Function to Move
```python
def get_cache_refresh_minutes() -> int:
    """Get cache refresh threshold from config with default fallback.

    Returns:
        Cache refresh threshold in minutes (default: 1440 = 24 hours)
    """
```

### Remove from coordinator
Remove the function entirely from `core.py`. Do NOT add a re-import - consumers will import directly from `utils.user_config`.

---

## HOW

1. **Copy function** to `utils/user_config.py`
2. **Remove late-binding** - Replace `_get_coordinator().get_config_values` with direct `get_config_values` call
3. **Update coordinator/core.py** - Remove function entirely (no re-import)
4. **Update coordinator/__init__.py** - Remove `get_cache_refresh_minutes` from exports
5. **Update test patches** - Point to new location

---

## ALGORITHM (Simplified Function)

```python
def get_cache_refresh_minutes() -> int:
    config = get_config_values([("coordinator", "cache_refresh_minutes", None)])
    value = config[("coordinator", "cache_refresh_minutes")]
    if value is None:
        return 1440  # Default: 24 hours
    try:
        result = int(value)
        return result if result > 0 else 1440
    except (ValueError, TypeError):
        return 1440
```

---

## DATA

### Input
- None (reads from user config file)

### Output
- `int`: Cache refresh threshold in minutes (default 1440)

### Config Key
- Section: `coordinator`
- Key: `cache_refresh_minutes`

---

## Test Cases

```python
# tests/utils/test_user_config.py

def test_get_cache_refresh_minutes_default():
    """Returns 1440 when config not set."""
    
def test_get_cache_refresh_minutes_from_config():
    """Returns configured value when set."""
    
def test_get_cache_refresh_minutes_invalid_value():
    """Returns 1440 for non-integer values."""
    
def test_get_cache_refresh_minutes_negative_value():
    """Returns 1440 for negative values."""
```
