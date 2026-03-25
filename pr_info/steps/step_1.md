# Step 1: Add Env Var + Config Resolution to `resolve_mcp_config_path()`

## LLM Prompt

> Read `pr_info/steps/summary.md` for context. Implement Step 1: extend `resolve_mcp_config_path()` in `src/mcp_coder/cli/utils.py` to support env var `MCP_CODER_MCP_CONFIG` and config file `[mcp] default_config_path` as intermediate resolution steps. Follow TDD — write tests first, then implement. Run all three code quality checks after changes.

## WHERE

- **Test file**: `tests/cli/test_utils.py` — extend existing `TestResolveMcpConfigPath` class
- **Source file**: `src/mcp_coder/cli/utils.py` — modify `resolve_mcp_config_path()`

## WHAT

### Modified function signature (unchanged externally)

```python
def resolve_mcp_config_path(
    mcp_config: str | None,
    project_dir: str | None = None,
) -> str | None:
```

### New tests to add to `TestResolveMcpConfigPath`

```python
# Priority tests
def test_resolve_mcp_config_env_var(self, tmp_path, monkeypatch): ...
def test_resolve_mcp_config_config_file(self, tmp_path, monkeypatch): ...
def test_resolve_mcp_config_cli_overrides_env(self, tmp_path, monkeypatch): ...
def test_resolve_mcp_config_env_overrides_config(self, tmp_path, monkeypatch): ...
def test_resolve_mcp_config_env_missing_file_falls_back(self, tmp_path, monkeypatch, caplog): ...
def test_resolve_mcp_config_config_missing_file_falls_back(self, tmp_path, monkeypatch, caplog): ...
```

## HOW

- Import `get_config_values` (already imported in utils.py)
- Use `os.environ.get("MCP_CODER_MCP_CONFIG")` for env var check (same pattern as `resolve_llm_method`)
- Use `get_config_values([("mcp", "default_config_path", None)])` for config file check
- No new env var mapping in `_get_standard_env_var()` (env var is checked directly, not via auto-detect)

## ALGORITHM

```python
def resolve_mcp_config_path(mcp_config, project_dir=None):
    if mcp_config is not None:
        # EXISTING: strict — resolve + validate, raise FileNotFoundError if missing
        return str(Path(mcp_config).resolve())

    # NEW: check env var
    if (env_path := os.environ.get("MCP_CODER_MCP_CONFIG")) is not None:
        resolved = Path(env_path).resolve()
        if resolved.exists():
            return str(resolved)
        logger.warning("MCP_CODER_MCP_CONFIG=%s: file not found, falling back to auto-detect", env_path)

    # NEW: check config file [mcp] default_config_path
    config = get_config_values([("mcp", "default_config_path", None)])
    if (cfg_path := config[("mcp", "default_config_path")]) is not None:
        resolved = Path(cfg_path).resolve()
        if resolved.exists():
            return str(resolved)
        logger.warning("[mcp] default_config_path=%s: file not found, falling back to auto-detect", cfg_path)

    # EXISTING: auto-detect .mcp.json in project_dir or CWD
    ...
```

## DATA

- **Input**: `mcp_config: str | None`, `project_dir: str | None`
- **Output**: `str | None` (absolute path or None) — unchanged
- **Side effects**: `logger.warning()` when env var or config points to missing file
- **Exceptions**: `FileNotFoundError` only for explicit CLI `--mcp-config` arg — unchanged

## Test Details

### `test_resolve_mcp_config_env_var`
- Set `MCP_CODER_MCP_CONFIG` env var to a real file in `tmp_path`
- Call `resolve_mcp_config_path(None)` — assert returns resolved path

### `test_resolve_mcp_config_config_file`
- Mock `get_config_values` to return a real file path
- Call `resolve_mcp_config_path(None)` in tmp_path with no `.mcp.json`
- Assert returns the config-specified path

### `test_resolve_mcp_config_cli_overrides_env`
- Set env var to one file, pass different file as `mcp_config`
- Assert CLI file is returned

### `test_resolve_mcp_config_env_overrides_config`
- Set env var to file A, mock config to return file B
- Assert env var file A is returned

### `test_resolve_mcp_config_env_missing_file_falls_back`
- Set env var to non-existent path, place `.mcp.json` in CWD
- Assert returns auto-detected `.mcp.json`, assert warning logged

### `test_resolve_mcp_config_config_missing_file_falls_back`
- Mock config to return non-existent path, place `.mcp.json` in CWD
- Assert returns auto-detected `.mcp.json`, assert warning logged

## Commit

One commit: tests + implementation for `resolve_mcp_config_path()` resolution chain.
