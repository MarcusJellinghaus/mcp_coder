# Step 3: Add Batch `get_config_values()` Function

## LLM Prompt

```
Implement Step 3 of Issue #228 (see pr_info/steps/summary.md for context).

Add new `get_config_values()` batch function and remove `get_config_value()`.
Follow TDD - write tests first, then implement.

Requirements:
- Single function to get multiple config values in one disk read
- Preserve environment variable priority per key
- Remove old `get_config_value()` function
- Decorate with `@log_function_call(sensitive_fields=["token", "api_token"])`
```

## WHERE: File Paths

- **Test file**: `tests/utils/test_user_config.py`
- **Implementation**: `src/mcp_coder/utils/user_config.py`

## WHAT: Main Functions

### New Function
```python
@log_function_call(sensitive_fields=["token", "api_token"])
def get_config_values(
    keys: list[tuple[str, str, str | None]]
) -> dict[tuple[str, str], str | None]:
    """Get multiple config values in one disk read.
    
    Retrieves configuration values from environment variables or config file,
    with environment variables taking priority. Reads the config file at most
    once, regardless of how many keys are requested.
    
    Args:
        keys: List of (section, key, env_var) tuples where:
            - section: The TOML section name (supports dot notation for nested
                      sections, e.g., 'coordinator.repos.mcp_coder')
            - key: The configuration key within the section
            - env_var: Optional environment variable name to check first.
                      Use None for auto-detection based on known mappings:
                      - ('github', 'token') -> GITHUB_TOKEN
                      - ('jenkins', 'server_url') -> JENKINS_URL
                      - ('jenkins', 'username') -> JENKINS_USER
                      - ('jenkins', 'api_token') -> JENKINS_TOKEN
    
    Returns:
        Dict mapping (section, key) tuples to their values (or None if not found).
        Access values using: result[(section, key)]
    
    Priority: Environment variable > Config file > None
    
    Raises:
        ValueError: If config file exists but has invalid TOML syntax.
    
    Examples:
        # Basic usage with auto-detected env vars
        config = get_config_values([
            ("github", "token", None),
            ("jenkins", "server_url", None),
        ])
        token = config[("github", "token")]
        
        # With explicit env var override
        config = get_config_values([
            ("custom", "setting", "MY_CUSTOM_VAR"),
        ])
        
        # Nested sections
        config = get_config_values([
            ("coordinator.repos.mcp_coder", "repo_url", None),
        ])
    """
```

### Functions to Remove
- `get_config_value()` - replaced by batch function

### Functions to Keep
- `_get_standard_env_var()` - still needed for env var mapping
- `get_config_file_path()` - still needed
- `load_config()` - still needed (add sensitive_fields decorator)
- `create_default_config()` - still needed
- `_format_toml_error()` - still needed

## HOW: Integration Points

1. Remove `@log_function_call` from `get_config_file_path()` (reduces log noise)
2. Add `@log_function_call(sensitive_fields=["token", "api_token"])` to `load_config()`
3. New function calls `load_config()` once for all keys

## ALGORITHM: Batch Config Reading (6 lines)

```
function get_config_values(keys):
    results = {}
    config_data = None  # Lazy load
    
    for (section, key, env_var) in keys:
        # Check env var first
        actual_env_var = env_var or _get_standard_env_var(section, key)
        if actual_env_var and os.getenv(actual_env_var):
            results[(section, key)] = os.getenv(actual_env_var)
            continue
        
        # Lazy load config (only if needed, only once)
        if config_data is None:
            config_data = load_config()
        
        # Navigate to value
        results[(section, key)] = _get_nested_value(config_data, section, key)
    
    return results
```

## DATA: Structures

**Input:**
```python
keys = [
    ("github", "token", None),           # Auto-detect env var
    ("jenkins", "server_url", None),     # Auto-detect env var  
    ("jenkins", "username", "JENKINS_USER"),  # Explicit env var
]
```

**Output:**
```python
{
    ("github", "token"): "ghp_xxx",
    ("jenkins", "server_url"): "https://jenkins.example.com",
    ("jenkins", "username"): "admin",
}
```

## Test Cases to Implement

### Test 1: Basic batch retrieval
```python
def test_get_config_values_returns_multiple_values(tmp_path, monkeypatch):
    """Test batch retrieval of multiple config values."""
    config_file = tmp_path / "config.toml"
    config_file.write_text('''
[github]
token = "ghp_test"

[jenkins]
server_url = "http://jenkins"
username = "admin"
''')
    monkeypatch.setattr("mcp_coder.utils.user_config.get_config_file_path", 
                        lambda: config_file)
    
    result = get_config_values([
        ("github", "token", None),
        ("jenkins", "server_url", None),
        ("jenkins", "username", None),
    ])
    
    assert result[("github", "token")] == "ghp_test"
    assert result[("jenkins", "server_url")] == "http://jenkins"
    assert result[("jenkins", "username")] == "admin"
```

### Test 2: Environment variable priority
```python
def test_get_config_values_env_var_priority(tmp_path, monkeypatch):
    """Environment variables take priority over config file."""
    config_file = tmp_path / "config.toml"
    config_file.write_text('[github]\ntoken = "file_token"')
    monkeypatch.setattr("mcp_coder.utils.user_config.get_config_file_path",
                        lambda: config_file)
    monkeypatch.setenv("GITHUB_TOKEN", "env_token")
    
    result = get_config_values([("github", "token", None)])
    
    assert result[("github", "token")] == "env_token"
```

### Test 3: Missing values return None
```python
def test_get_config_values_missing_returns_none(tmp_path, monkeypatch):
    """Missing keys return None without raising."""
    config_file = tmp_path / "config.toml"
    config_file.write_text('[github]\ntoken = "test"')
    monkeypatch.setattr("mcp_coder.utils.user_config.get_config_file_path",
                        lambda: config_file)
    
    result = get_config_values([
        ("github", "token", None),
        ("nonexistent", "key", None),
    ])
    
    assert result[("github", "token")] == "test"
    assert result[("nonexistent", "key")] is None
```

### Test 4: Nested section support
```python
def test_get_config_values_nested_sections(tmp_path, monkeypatch):
    """Test dot notation for nested sections."""
    config_file = tmp_path / "config.toml"
    config_file.write_text('''
[coordinator.repos.mcp_coder]
repo_url = "https://github.com/test/repo"
executor_os = "linux"
''')
    monkeypatch.setattr("mcp_coder.utils.user_config.get_config_file_path",
                        lambda: config_file)
    
    result = get_config_values([
        ("coordinator.repos.mcp_coder", "repo_url", None),
        ("coordinator.repos.mcp_coder", "executor_os", None),
    ])
    
    assert result[("coordinator.repos.mcp_coder", "repo_url")] == "https://github.com/test/repo"
    assert result[("coordinator.repos.mcp_coder", "executor_os")] == "linux"
```

### Test 5: Single disk read verification
```python
def test_get_config_values_single_disk_read(tmp_path, monkeypatch):
    """Verify config is loaded only once for multiple keys."""
    config_file = tmp_path / "config.toml"
    config_file.write_text('[a]\nx = "1"\n[b]\ny = "2"')
    monkeypatch.setattr("mcp_coder.utils.user_config.get_config_file_path",
                        lambda: config_file)
    
    load_count = 0
    original_load = load_config
    
    def counting_load():
        nonlocal load_count
        load_count += 1
        return original_load()
    
    monkeypatch.setattr("mcp_coder.utils.user_config.load_config", counting_load)
    
    get_config_values([("a", "x", None), ("b", "y", None)])
    
    assert load_count == 1  # Only one disk read
```

### Test 6: Explicit env var override
```python
def test_get_config_values_explicit_env_var(monkeypatch):
    """Test explicit env_var parameter overrides auto-detection."""
    monkeypatch.setenv("CUSTOM_VAR", "custom_value")
    
    result = get_config_values([("any", "key", "CUSTOM_VAR")])
    
    assert result[("any", "key")] == "custom_value"
```

## Implementation Checklist

- [ ] Write tests first (TDD)
- [ ] Remove `@log_function_call` from `get_config_file_path()`
- [ ] Add `@log_function_call(sensitive_fields=["token", "api_token"])` to `load_config()`
- [ ] Add helper `_get_nested_value(config_data, section, key)` 
- [ ] Implement `get_config_values()` function
- [ ] Remove `get_config_value()` function
- [ ] Run tests to verify
