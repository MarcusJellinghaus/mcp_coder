# Step 2: Add `[mcp]` Section to Config Template and Verify Display

## LLM Prompt

> Read `pr_info/steps/summary.md` for context. Implement Step 2: add commented `[mcp]` section to `create_default_config()` template and add `[mcp]` display to `verify_config()`. Follow TDD — write tests first, then implement. Run all three code quality checks after changes.

## WHERE

- **Test files**:
  - `tests/utils/test_user_config.py` — add test to `TestCreateDefaultConfig`
  - `tests/utils/test_verify_config.py` — add tests to `TestVerifyConfig`
- **Source file**: `src/mcp_coder/utils/user_config.py` — modify `create_default_config()` and `verify_config()`

## WHAT

### New tests

```python
# In TestCreateDefaultConfig
def test_create_default_config_has_mcp_section(self, tmp_path, monkeypatch): ...

# In TestVerifyConfig
def test_verify_config_mcp_configured_in_config(self, tmp_path, monkeypatch): ...
def test_verify_config_mcp_not_configured(self, tmp_path, monkeypatch): ...
def test_verify_config_mcp_configured_via_env_var(self, tmp_path, monkeypatch): ...
```

### Modified functions

- `create_default_config()` — add commented `[mcp]` block to template string
- `verify_config()` — add `[mcp]` entry after `[llm]` entry

## HOW

### `create_default_config()` template addition

Add after the existing commented `# [llm]` block:

```toml
# [mcp]
# Default MCP config file path (relative to CWD or absolute)
# Environment variable (higher priority): MCP_CODER_MCP_CONFIG
# default_config_path = ".mcp.json"
```

### `verify_config()` [mcp] entry

Add after the `[llm]` section check. Logic:

```python
# [mcp] - always shown
mcp_env = os.environ.get("MCP_CODER_MCP_CONFIG")
mcp_config = (
    config_data.get("mcp", {}).get("default_config_path")
    if isinstance(config_data.get("mcp"), dict)
    else None
)
if mcp_env:
    source = _get_source_annotation("mcp", "default_config_path", config_data)
    entries.append({"label": "[mcp]", "status": "ok", "value": f"default_config_path configured {source}"})
elif mcp_config:
    entries.append({"label": "[mcp]", "status": "ok", "value": f"default_config_path = {mcp_config} (config.toml)"})
else:
    entries.append({"label": "[mcp]", "status": "info", "value": "not configured (using auto-detect)"})
```

## ALGORITHM

For `verify_config()` addition (~8 lines):
```python
mcp_env = os.environ.get("MCP_CODER_MCP_CONFIG")
mcp_config_val = config_data.get("mcp", {}).get("default_config_path") if isinstance(...)
if mcp_env:
    source = _get_source_annotation(...)
    entries.append({"label": "[mcp]", "status": "ok", "value": f"... {source}"})
elif mcp_config_val:
    entries.append({"label": "[mcp]", "status": "ok", "value": f"... (config.toml)"})
else:
    entries.append({"label": "[mcp]", "status": "info", "value": "not configured (using auto-detect)"})
```

## DATA

### `verify_config()` entry format

```python
# When configured via config.toml:
{"label": "[mcp]", "status": "ok", "value": "default_config_path = .mcp.json (config.toml)"}

# When configured via env var:
{"label": "[mcp]", "status": "ok", "value": "default_config_path configured (env var)"}

# When not configured:
{"label": "[mcp]", "status": "info", "value": "not configured (using auto-detect)"}
```

## Test Details

### `test_create_default_config_has_mcp_section`
- Create config via `create_default_config()`
- Read raw text content
- Assert `# [mcp]` and `# default_config_path` appear in content
- Assert `[mcp]` does NOT appear as uncommented section (it's commented out)

### `test_verify_config_mcp_configured_in_config`
- Write config with `[mcp]\ndefault_config_path = ".mcp.json"`
- Call `verify_config()`
- Assert `[mcp]` entry has status `ok` and value contains `default_config_path = .mcp.json`

### `test_verify_config_mcp_not_configured`
- Write empty valid config
- Clear `MCP_CODER_MCP_CONFIG` env var
- Call `verify_config()`
- Assert `[mcp]` entry has status `info` and value contains `not configured`

### `test_verify_config_mcp_configured_via_env_var`
- Set `MCP_CODER_MCP_CONFIG` env var
- Write empty config
- Call `verify_config()`
- Assert `[mcp]` entry has status `ok` and value contains `(env var)`

## Commit

One commit: tests + implementation for `[mcp]` in config template and verify display.
