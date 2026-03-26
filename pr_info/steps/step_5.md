# Step 5: Migrate Config Keys

## Context
See `pr_info/steps/summary.md` for full issue context.

## Goal
Migrate config keys from `coordinator.vscodeclaude` to top-level `vscodeclaude` section. Update default config template. Clean break — old keys stop working silently.

## LLM Prompt
```
Implement Step 5 of issue #570 (CLI restructure). Read pr_info/steps/summary.md for context, then read pr_info/steps/step_5.md for detailed instructions. Migrate vscodeclaude config keys to top-level. Update tests first (TDD), then implementation. Run all code quality checks after changes.
```

## WHERE
- `src/mcp_coder/workflows/vscodeclaude/config.py` — change config key strings
- `src/mcp_coder/utils/user_config.py` — update default config template + verify_config
- `tests/workflows/vscodeclaude/test_config.py` — update config key expectations
- `tests/utils/test_user_config.py` — update if default template is tested

## WHAT

### vscodeclaude/config.py — `load_vscodeclaude_config()`

Change config key lookups:

```python
# OLD:
config = get_config_values([
    ("coordinator.vscodeclaude", "workspace_base", None),
    ("coordinator.vscodeclaude", "max_sessions", None),
])
workspace_base = config[("coordinator.vscodeclaude", "workspace_base")]
max_sessions_str = config[("coordinator.vscodeclaude", "max_sessions")]

# NEW:
config = get_config_values([
    ("vscodeclaude", "workspace_base", None),
    ("vscodeclaude", "max_sessions", None),
])
workspace_base = config[("vscodeclaude", "workspace_base")]
max_sessions_str = config[("vscodeclaude", "max_sessions")]
```

Update error message:
```python
# OLD:
f"workspace_base not configured in [coordinator.vscodeclaude] section. "

# NEW:
f"workspace_base not configured in [vscodeclaude] section. "
```

### vscodeclaude/config.py — `_get_configured_repos()`

This function reads `coordinator.repos.*` sections. The repo config stays under `coordinator.repos` (per design — repo config is shared, not vscodeclaude-specific). **No change needed** for this function.

### vscodeclaude/config.py — `load_repo_vscodeclaude_config()`

This reads `coordinator.repos.{repo_name}` for setup_commands. The setup commands are repo-specific, not vscodeclaude-specific. **No change needed** for this function.

### user_config.py — `create_default_config()`

Add `[vscodeclaude]` section to the template:

```toml
[vscodeclaude]
# VSCodeClaude session configuration
# workspace_base = "C:/path/to/vscodeclaude/workspaces"
# max_sessions = 3
```

### user_config.py — `verify_config()`

The verify_config function checks `[coordinator]` section. Update to also check `[vscodeclaude]`:

```python
# After coordinator check, add:
vscodeclaude = config_data.get("vscodeclaude")
if isinstance(vscodeclaude, dict) and vscodeclaude.get("workspace_base"):
    entries.append({
        "label": "[vscodeclaude]",
        "status": "ok",
        "value": f"workspace_base configured",
    })
```

## HOW

Direct string replacements in config.py. The `get_config_values()` function already supports any section name via dot notation, so changing `"coordinator.vscodeclaude"` to `"vscodeclaude"` just changes which TOML section is read.

## ALGORITHM (config loading)
```
read config.toml
look up [vscodeclaude].workspace_base  (was [coordinator.vscodeclaude])
look up [vscodeclaude].max_sessions    (was [coordinator.vscodeclaude])
validate workspace_base exists
return VSCodeClaudeConfig(workspace_base, max_sessions)
```

## TEST CHANGES

### tests/workflows/vscodeclaude/test_config.py

Update any tests that mock or reference `coordinator.vscodeclaude` config keys:

- Tests that mock `get_config_values` — update the expected key tuples:
  - `("coordinator.vscodeclaude", "workspace_base")` → `("vscodeclaude", "workspace_base")`
  - `("coordinator.vscodeclaude", "max_sessions")` → `("vscodeclaude", "max_sessions")`

- Tests that check error messages — update expected strings:
  - `"[coordinator.vscodeclaude]"` → `"[vscodeclaude]"`

### tests/utils/test_user_config.py

If any tests validate the default config template content, update the expected `[vscodeclaude]` section.

## DATA

**Old config.toml format:**
```toml
[coordinator.vscodeclaude]
workspace_base = "C:/path"
max_sessions = 3
```

**New config.toml format:**
```toml
[vscodeclaude]
workspace_base = "C:/path"
max_sessions = 3
```

Config keys for repo-specific setup commands remain unchanged:
```toml
[coordinator.repos.mcp_coder]
setup_commands_windows = '["pip install -e ."]'
```
