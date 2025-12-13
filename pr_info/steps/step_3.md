# Step 3: Refactor `get_config_value()` to Use `load_config()`

## LLM Prompt

```
Read pr_info/steps/summary.md for context, then implement Step 3.

Refactor `get_config_value()` in `user_config.py` to use `load_config()` internally.
This is a behavior change: parse errors now raise ValueError instead of returning None.
Update existing tests to reflect this change.
```

## WHERE

- **Test file**: `tests/utils/test_user_config.py`
- **Implementation file**: `src/mcp_coder/utils/user_config.py`

## WHAT

### Function Signature (unchanged)

```python
@log_function_call
def get_config_value(
    section: str, key: str, env_var: Optional[str] = None
) -> Optional[str]:
    """Read a configuration value from environment or config file.
    
    [existing docstring, but update the Note section]
    
    Raises:
        ValueError: If config file exists but has invalid TOML syntax.
    """
```

## HOW

### Changes Required

1. Replace direct `tomllib.load()` call with `load_config()`
2. Remove the `try/except (tomllib.TOMLDecodeError, OSError, IOError)` block
3. Let `ValueError` from `load_config()` propagate
4. Keep the logic for navigating nested sections and returning None for missing keys

### Before (current implementation)

```python
try:
    with open(config_path, "rb") as f:
        config_data = tomllib.load(f)
    # ... navigate sections ...
except (tomllib.TOMLDecodeError, OSError, IOError):
    return None
```

### After (new implementation)

```python
config_data = load_config()
if not config_data:
    return None
# ... navigate sections (unchanged) ...
```

## ALGORITHM

```
1. Check environment variable first (unchanged)
2. Call load_config() - may raise ValueError on parse error
3. If empty dict returned, return None
4. Navigate nested sections using dot notation (unchanged)
5. Return value or None if not found (unchanged)
```

## DATA

### Behavior Change

| Scenario | Before | After |
|----------|--------|-------|
| File missing | `None` | `None` |
| Valid TOML, key exists | value | value |
| Valid TOML, key missing | `None` | `None` |
| Invalid TOML | `None` | `ValueError` raised |
| File read error | `None` | `ValueError` raised |

## TESTS TO UPDATE

### Existing Test: `test_get_config_value_invalid_toml`

**Before**: Expects `None` returned
**After**: Expects `ValueError` raised

```python
def test_get_config_value_invalid_toml_raises(self, mock_get_path: MagicMock) -> None:
    """Test that ValueError is raised when TOML file is invalid."""
    # Setup
    mock_path = MagicMock(spec=Path)
    mock_path.exists.return_value = True
    mock_get_path.return_value = mock_path

    invalid_toml = b"[invalid toml content without closing bracket"

    with patch("builtins.open", mock_open(read_data=invalid_toml)):
        with pytest.raises(ValueError) as exc_info:
            get_config_value("tokens", "github")
        
        # Verify error message includes file path
        assert str(mock_path) in str(exc_info.value)
```

### Existing Test: `test_get_config_value_io_error`

**Before**: Expects `None` returned
**After**: Expects `ValueError` raised

```python
def test_get_config_value_io_error_raises(self, mock_get_path: MagicMock) -> None:
    """Test that ValueError is raised when file cannot be read."""
    # ... similar pattern ...
```

## IMPLEMENTATION NOTES

1. This is an intentional behavior change per the issue requirements
2. A broken config file should not silently fail
3. The existing coordinator.py error handling already catches ValueError
4. Remove unused `tomllib` import from the function (moved to `load_config()`)
