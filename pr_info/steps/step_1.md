# Step 1: Add `verify_config()` Function

> **Reference**: See `pr_info/steps/summary.md` for overall context and architecture.

## Goal

Implement `verify_config()` in `utils/user_config.py` with full test coverage. This is the core logic — no CLI integration yet.

## WHERE

- **Implementation**: `src/mcp_coder/utils/user_config.py` — add `verify_config()` function
- **Tests**: `tests/utils/test_user_config.py` — add `TestVerifyConfig` class

## WHAT

```python
def verify_config() -> dict[str, Any]:
    """Verify user config file and return structured result.

    Returns:
        Dict with:
        - "entries": list of {"label": str, "status": "ok"|"warning"|"error", "value": str}
        - "has_error": bool (True only for invalid TOML)
    """
```

## HOW

- Uses existing `get_config_file_path()`, `load_config()`, `_format_toml_error()` from same module
- Uses `os.environ.get()` for env var checks
- Uses `_get_standard_env_var()` mappings already defined in the module
- Build a local section-to-env-var mapping for the verify loop, e.g.:
  ```python
  _SECTION_ENV_VARS = {
      "github": [("token", "GITHUB_TOKEN")],
      "jenkins": [("server_url", "JENKINS_URL"), ("username", "JENKINS_USER"), ("api_token", "JENKINS_TOKEN")],
  }
  ```
- Add to module's `__all__` or just ensure it's importable

## ALGORITHM

```
1. path = get_config_file_path()
2. if not path.exists():
   2a. add warning entries (not found + expected path + hint)
   2b. config_data = {}
3. else: try load_config() → on ValueError → return error entry with parse error, has_error=True
4. for each known section (llm, github, jenkins, coordinator):
   4a. check config data AND relevant env vars
   4b. build entry with source annotation ("env var", "config.toml", "env var, also in config.toml")
5. return {"entries": [...], "has_error": False}
```

## DATA

### Return value — missing config:
```python
{
    "entries": [
        {"label": "Config file", "status": "warning", "value": "not found"},
        {"label": "Expected path", "status": "info", "value": "C:\\Users\\user\\.mcp_coder\\config.toml"},
        {"label": "Hint", "status": "info", "value": "Create a config at <path> — see docs/configuration/config.md for format"},
    ],
    "has_error": False
}
```

### Return value — invalid TOML:
```python
{
    "entries": [
        {"label": "Config file", "status": "error", "value": "invalid TOML"},
        {"label": "Parse error", "status": "error", "value": "<formatted multi-line error>"},
    ],
    "has_error": True
}
```

### Return value — valid config:
```python
{
    "entries": [
        {"label": "Config file", "status": "ok", "value": "C:\\Users\\user\\.mcp_coder\\config.toml"},
        {"label": "[llm]", "status": "ok", "value": "default_provider = langchain"},
        {"label": "[github]", "status": "ok", "value": "token configured (env var, also in config.toml)"},
        {"label": "[jenkins]", "status": "ok", "value": "server_url configured (config.toml)"},
        {"label": "[coordinator]", "status": "ok", "value": "2 repos configured"},
    ],
    "has_error": False
}
```

### Section-specific logic:

**`[llm]`** — only show if section exists in config:
- Show `default_provider` value: `"default_provider = langchain"`

**`[github]`** — check `GITHUB_TOKEN` env var + `config["github"]["token"]`:
- Both present: `"token configured (env var, also in config.toml)"`
- Env only: `"token configured (env var)"`
- Config only: `"token configured (config.toml)"`
- Neither: skip section (don't show)

**`[jenkins]`** — check `JENKINS_URL`, `JENKINS_USER`, `JENKINS_TOKEN` env vars + config keys:
- Show `server_url` source as representative: `"server_url configured (config.toml)"`
- Same dual-source pattern as github

**`[coordinator]`** — count repos:
- Count keys in `config.get("coordinator", {}).get("repos", {})}`
- Show: `"2 repos configured"`
- Skip if no repos

## TESTS (TDD — write first)

All tests in `TestVerifyConfig` class in `tests/utils/test_user_config.py`:

1. **`test_verify_config_missing_file`** — no config file → warning status, `has_error=False`, expected path shown, hint shown
2. **`test_verify_config_invalid_toml`** — bad TOML → error status, `has_error=True`, parse error in value
3. **`test_verify_config_valid_with_all_sections`** — full config → ok status for each section, correct summaries
4. **`test_verify_config_env_var_only`** — no config file section but env var set → section shows `(env var)`
5. **`test_verify_config_dual_source`** — env var AND config both set → `(env var, also in config.toml)`
6. **`test_verify_config_coordinator_repo_count`** — 3 repos → `"3 repos configured"`
7. **`test_verify_config_llm_default_provider`** — `[llm]` section → shows `default_provider = langchain`
8. **`test_verify_config_unknown_sections_ignored`** — unknown `[custom]` section not in output
9. **`test_verify_config_empty_valid_file`** — valid but empty TOML → ok config file, no section entries

## LLM Prompt

```
Read pr_info/steps/summary.md for overall context, then implement Step 1.

1. Read tests/utils/test_user_config.py and src/mcp_coder/utils/user_config.py
2. Add TestVerifyConfig test class to tests/utils/test_user_config.py with all 9 tests listed in step_1.md
3. Add verify_config() function to src/mcp_coder/utils/user_config.py following the algorithm and data structures in step_1.md
4. Run all three code quality checks (pylint, pytest, mypy) and fix any issues
5. Commit with message: "feat(verify): add verify_config() for config file validation (#552)"
```
