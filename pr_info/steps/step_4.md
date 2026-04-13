# Step 4: Update int/list/langchain callers and type annotations

**Commit message:** `config: update int, list, and langchain callers for native types`

> Read `pr_info/steps/summary.md` for full context. This is Step 4: update remaining callers that parse integers, lists, or duplicate env var logic.

## Goal

Update `vscodeclaude/config.py` (int and list handling), `langchain/__init__.py` (env var override removal), and type annotations in `jenkins_operations/client.py` and `github_operations/base_manager.py`.

## WHERE + WHAT

### 1. `src/mcp_coder/workflows/vscodeclaude/config.py` — `load_vscodeclaude_config()` (line ~88)

**Before:**
```python
max_sessions_str = config[("vscodeclaude", "max_sessions")]
max_sessions = DEFAULT_MAX_SESSIONS
if max_sessions_str:
    try:
        max_sessions = int(max_sessions_str)
    except ValueError:
        logger.warning(...)
```

**After:**
```python
max_sessions_value = config[("vscodeclaude", "max_sessions")]
max_sessions = DEFAULT_MAX_SESSIONS
if max_sessions_value is not None:
    if isinstance(max_sessions_value, int):
        max_sessions = max_sessions_value
    else:
        # Env var case: string value
        try:
            max_sessions = int(max_sessions_value)
        except (ValueError, TypeError):
            logger.warning(...)
```

### 2. `src/mcp_coder/workflows/vscodeclaude/config.py` — `load_repo_vscodeclaude_config()` (lines ~117-128)

**Before:**
```python
windows_commands = config[(section, "setup_commands_windows")]
if windows_commands:
    try:
        parsed = json.loads(windows_commands)
        if isinstance(parsed, list):
            result["setup_commands_windows"] = parsed
    except json.JSONDecodeError:
        result["setup_commands_windows"] = [windows_commands]
```

**After:**
```python
windows_commands = config[(section, "setup_commands_windows")]
if windows_commands is not None:
    if isinstance(windows_commands, list):
        result["setup_commands_windows"] = windows_commands
    elif isinstance(windows_commands, str):
        # Env var case: try JSON parse, fallback to single command
        try:
            parsed = json.loads(windows_commands)
            if isinstance(parsed, list):
                result["setup_commands_windows"] = parsed
            else:
                result["setup_commands_windows"] = [windows_commands]
        except json.JSONDecodeError:
            result["setup_commands_windows"] = [windows_commands]
```

Same pattern for `setup_commands_linux`.

### 3. `src/mcp_coder/llm/providers/langchain/__init__.py` — `_load_langchain_config()` (lines 113-142)

**Before:**
```python
raw = get_config_values([
    ("llm", "default_provider", None),
    ("llm.langchain", "backend", None),
    ("llm.langchain", "model", None),
    ("llm.langchain", "api_key", None),
    ("llm.langchain", "endpoint", None),
    ("llm.langchain", "api_version", None),
])
config = {
    "default_provider": raw[("llm", "default_provider")],
    "backend": raw[("llm.langchain", "backend")],
    ...
}
# Env vars override config file values
env_overrides = {
    "backend": "MCP_CODER_LLM_LANGCHAIN_BACKEND",
    "model": "MCP_CODER_LLM_LANGCHAIN_MODEL",
    "endpoint": "MCP_CODER_LLM_LANGCHAIN_ENDPOINT",
    "api_version": "MCP_CODER_LLM_LANGCHAIN_API_VERSION",
}
for key, env_var in env_overrides.items():
    value = os.environ.get(env_var)
    if value:
        config[key] = value
return config
```

**After:**
```python
raw = get_config_values([
    ("llm", "default_provider", None),
    ("llm.langchain", "backend", None),
    ("llm.langchain", "model", None),
    ("llm.langchain", "api_key", None),
    ("llm.langchain", "endpoint", None),
    ("llm.langchain", "api_version", None),
])
return {
    "default_provider": raw[("llm", "default_provider")],
    "backend": raw[("llm.langchain", "backend")],
    "model": raw[("llm.langchain", "model")],
    "api_key": raw[("llm.langchain", "api_key")],
    "endpoint": raw[("llm.langchain", "endpoint")],
    "api_version": raw[("llm.langchain", "api_version")],
}
```

The env var override loop is deleted. The schema already maps these keys to their env vars, so `get_config_values()` checks them automatically. Remove the `import os` if it becomes unused.

### 4. Type annotations

**`src/mcp_coder/utils/jenkins_operations/client.py` (line 91):**

```python
# Before
config: dict[tuple[str, str], Optional[str]] = get_config_values(...)
# After
config: dict[tuple[str, str], str | bool | int | list | None] = get_config_values(...)
```

**`src/mcp_coder/utils/github_operations/base_manager.py` (line 169):**

```python
# Before
config: dict[tuple[str, str], Optional[str]] = user_config.get_config_values(...)
# After
config: dict[tuple[str, str], str | bool | int | list | None] = user_config.get_config_values(...)
```

## Tests to update

### `tests/workflows/vscodeclaude/test_config.py`

- `test_load_vscodeclaude_config_success`: `"5"` → `5` for max_sessions mock
- `test_load_repo_vscodeclaude_config`: `'["uv venv", "uv sync"]'` → `["uv venv", "uv sync"]` (native list), `'["make setup"]'` → `["make setup"]`

### `tests/llm/providers/langchain/test_langchain_provider.py`

- `test_env_var_overrides_config_values`: This test sets env vars and expects them to override. After this change, `get_config_values` handles env vars via schema. The mock for `get_config_values` already returns the config-file values. The env vars should now be picked up by `get_config_values` itself (not by the manual loop). Update the test: instead of mocking `get_config_values` to return config values and relying on the manual loop, mock `get_config_values` to return the env var values directly (since that's what it would do in reality).
- `test_env_var_does_not_override_when_empty`: Similar update — env vars are now handled by `get_config_values`.

### Other test files

Check for any other tests mocking `get_config_values` with string representations of int/list values and update to native types.

## Checklist
- [ ] `vscodeclaude/config.py`: handle native `int` for max_sessions
- [ ] `vscodeclaude/config.py`: handle native `list` for setup_commands
- [ ] `langchain/__init__.py`: remove env var override loop
- [ ] `jenkins_operations/client.py`: update type annotation
- [ ] `github_operations/base_manager.py`: update type annotation
- [ ] All test mocks updated
- [ ] All checks pass (pylint, pytest, mypy)
