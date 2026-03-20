# Step 2: Core Resolution Logic — Config Key Rename, Return Type, MCP Auto-detect

> **Summary**: [pr_info/steps/summary.md](summary.md)
> **Covers**: Sub-tasks 2 (config rename) + 3 (mcp auto-detect) + return type change

## LLM Prompt

```
Implement Step 2 of issue #528: Update the core resolution functions in cli/utils.py.

Read pr_info/steps/summary.md for full context, then read this step file for details.

Three changes in src/mcp_coder/cli/utils.py:
1. resolve_llm_method() — read "default_provider" instead of "provider", return (provider, source) tuple
2. resolve_mcp_config_path() — add project_dir parameter, auto-detect .mcp.json when mcp_config is None
3. No other files in this step — callers are updated in Step 4

Also update:
- src/mcp_coder/llm/providers/langchain/__init__.py — _load_langchain_config() reads "default_provider"
- src/mcp_coder/utils/user_config.py — add commented-out [llm] section to create_default_config()

Update tests first (TDD), then the implementation. Run all three code quality checks after.
```

## WHERE

- **Source**: `src/mcp_coder/cli/utils.py`
- **Source**: `src/mcp_coder/llm/providers/langchain/__init__.py`
- **Source**: `src/mcp_coder/utils/user_config.py`
- **Tests**: `tests/cli/test_utils.py`
- **Tests**: `tests/llm/providers/langchain/test_langchain_provider.py`
- **Tests**: `tests/utils/test_user_config.py`

## WHAT

### `resolve_llm_method()` — signature change

```python
# BEFORE
def resolve_llm_method(llm_method: str | None) -> str:

# AFTER
def resolve_llm_method(llm_method: str | None) -> tuple[str, str]:
    """Returns (provider, source) tuple.
    
    source is one of: "cli argument", "config default_provider", "default"
    """
```

### `resolve_mcp_config_path()` — add parameter

```python
# BEFORE
def resolve_mcp_config_path(mcp_config: str | None) -> str | None:

# AFTER
def resolve_mcp_config_path(
    mcp_config: str | None,
    project_dir: str | None = None,
) -> str | None:
```

### `_load_langchain_config()` — config key change

```python
# BEFORE (in langchain/__init__.py)
(\"llm\", \"provider\", None),

# AFTER
(\"llm\", \"default_provider\", None),
```

## HOW

No new imports needed. Changes are internal to existing functions.

## ALGORITHM — `resolve_llm_method()`

```
1. If llm_method is not None → return (llm_method, "cli argument")
2. Read config key ("llm", "default_provider")
3. If config value == "langchain" → return ("langchain", "config default_provider")
4. Return ("claude", "default")
```

## ALGORITHM — `resolve_mcp_config_path()`

```
1. If mcp_config is not None → resolve to absolute path, validate exists, return (existing behavior)
2. base = project_dir if project_dir else CWD
3. candidate = Path(base) / ".mcp.json"
4. If candidate.exists() → log debug, return str(candidate.resolve())
5. Log debug "no .mcp.json found", return None
```

## DATA

```python
# resolve_llm_method return examples:
("claude", "cli argument")
("langchain", "config default_provider")
("claude", "default")

# resolve_mcp_config_path return: str | None (unchanged)
```

## Config Template Addition (user_config.py)

Add to `create_default_config()` template, before the `[github]` section:

```toml
# [llm]
# Default LLM provider: "claude" (default) or "langchain"
# default_provider = "langchain"
```

## Test Cases

### `tests/cli/test_utils.py`

1. `test_resolve_llm_method_cli_arg` — returns `("claude", "cli argument")`
2. `test_resolve_llm_method_config_default_provider` — mock config with `default_provider = "langchain"`, returns `("langchain", "config default_provider")`
3. `test_resolve_llm_method_default` — no CLI arg, no config → `("claude", "default")`
4. `test_resolve_mcp_config_auto_detect_project_dir` — `.mcp.json` exists in project_dir → returns path
5. `test_resolve_mcp_config_auto_detect_cwd` — `.mcp.json` exists in CWD → returns path
6. `test_resolve_mcp_config_auto_detect_missing` — no `.mcp.json` → returns `None`
7. `test_resolve_mcp_config_explicit_still_works` — explicit path still resolves as before

### `tests/llm/providers/langchain/test_langchain_provider.py`

1. Update any test mocking `get_config_values` for `("llm", "provider")` → `("llm", "default_provider")`

### `tests/utils/test_user_config.py`

1. `test_create_default_config_has_llm_section` — verify template contains `# default_provider`
