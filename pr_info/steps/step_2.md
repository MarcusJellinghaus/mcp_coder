# Step 2: Add `load_config()` Function

## LLM Prompt

```
Read pr_info/steps/summary.md for context, then implement Step 2.

Add a `load_config()` function in `user_config.py` that loads the full config 
dictionary and raises ValueError with formatted message on parse errors.
Follow TDD - write tests first.
```

## WHERE

- **Test file**: `tests/utils/test_user_config.py`
- **Implementation file**: `src/mcp_coder/utils/user_config.py`

## WHAT

### Function Signature

```python
@log_function_call
def load_config() -> dict[str, Any]:
    """Load user configuration from TOML file.
    
    Returns:
        Configuration dictionary. Empty dict if file doesn't exist.
        
    Raises:
        ValueError: If config file exists but has invalid TOML syntax.
                   Error message includes file path, line content, and pointer.
    """
```

## HOW

### Integration Points

- Public function (no underscore prefix)
- Uses `@log_function_call` decorator for consistency
- Calls `get_config_file_path()` to locate config
- Calls `_format_toml_error()` on parse failure
- Will be used by `get_config_value()` (Step 3) and `coordinator.py` (Step 4)

### Imports to Add

```python
from typing import Any  # For return type annotation
```

### Export

Add to module's public API if there's an `__all__` list.

## ALGORITHM

```
1. Get config file path using get_config_file_path()
2. If file doesn't exist, return empty dict
3. Try to open and parse with tomllib.load()
4. On TOMLDecodeError: raise ValueError with _format_toml_error() message
5. Return parsed config dict
```

## DATA

### Input

None (reads from standard config location)

### Output

- Success: `dict[str, Any]` - Full config dictionary
- File missing: `{}` - Empty dictionary
- Parse error: Raises `ValueError` with formatted message

### Example Return Value

```python
{
    "github": {"token": "ghp_xxx"},
    "jenkins": {"server_url": "https://jenkins.example.com"},
    "coordinator": {
        "repos": {
            "mcp_coder": {"repo_url": "https://..."}
        }
    }
}
```

## TESTS TO WRITE

### Test Class: `TestLoadConfig`

```python
class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_config_returns_dict(self, tmp_path, monkeypatch):
        """Successfully loads valid TOML config."""
        
    def test_load_config_returns_empty_dict_if_missing(self, tmp_path, monkeypatch):
        """Returns empty dict when config file doesn't exist."""
        
    def test_load_config_raises_on_invalid_toml(self, tmp_path, monkeypatch):
        """Raises ValueError on TOML parse error."""
        
    def test_load_config_error_includes_file_path(self, tmp_path, monkeypatch):
        """ValueError message includes the config file path."""
        
    def test_load_config_error_includes_line_content(self, tmp_path, monkeypatch):
        """ValueError message includes the error line content."""
        
    def test_load_config_preserves_nested_structure(self, tmp_path, monkeypatch):
        """Correctly loads nested TOML sections."""
```

## IMPLEMENTATION NOTES

1. Use `from e` when re-raising to preserve exception chain
2. The `@log_function_call` decorator provides debug logging
3. Return empty dict (not None) for missing file - simpler for callers
4. IOError during file read should also raise ValueError with context
