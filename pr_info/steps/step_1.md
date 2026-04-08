# Step 1: Add `MCP_CODER_VENV_PATH` to `prepare_llm_environment()`

> **Context:** Read `pr_info/steps/summary.md` for full issue context.

## Goal

Fix latent bug: `.mcp.json` references `${MCP_CODER_VENV_PATH}` but `prepare_llm_environment()` never returns it. Only `.bat` launchers set it today. Add it to the returned dict so all Python callers get it.

## WHERE

- **Modify:** `src/mcp_coder/llm/env.py`
- **Modify:** `tests/llm/test_env.py`

## WHAT

### `src/mcp_coder/llm/env.py`

Add a helper to compute the bin/Scripts subdirectory, and include `MCP_CODER_VENV_PATH` in the returned dict.

```python
def _get_bin_dir(venv_root: str) -> str:
    """Return the bin/Scripts subdirectory for a venv root."""
```

Update `prepare_llm_environment()` return dict to include `MCP_CODER_VENV_PATH`.

### ALGORITHM

```
venv_root = _get_runner_environment()  # existing, unchanged
bin_dir = "Scripts" if sys.platform == "win32" else "bin"
venv_path = Path(venv_root) / bin_dir
return {
    "MCP_CODER_PROJECT_DIR": ...,    # existing
    "MCP_CODER_VENV_DIR": ...,       # existing
    "MCP_CODER_VENV_PATH": str(venv_path.resolve()),  # NEW
}
```

### DATA

Return type stays `dict[str, str]`. New key `MCP_CODER_VENV_PATH` added — value is the absolute OS-native path to the `Scripts` (Windows) or `bin` (POSIX) subdirectory of the resolved venv root.

## HOW

- Import `sys` (already imported in the file).
- `_get_bin_dir` is a private module-level function — no exports needed.
- No change to `_get_runner_environment()` or its precedence logic.

## Tests (TDD — write first)

Add to `tests/llm/test_env.py`:

1. **`test_prepare_llm_environment_includes_venv_path`** — Verify `MCP_CODER_VENV_PATH` is in the returned dict.
2. **`test_venv_path_is_scripts_subdir`** — On the current platform, verify the returned path ends with `Scripts` (Windows) or `bin` (POSIX) and is a child of `MCP_CODER_VENV_DIR`.
3. **`test_venv_path_absolute`** — Verify the returned `MCP_CODER_VENV_PATH` is an absolute path.

## Commit

```
feat(llm): add MCP_CODER_VENV_PATH to prepare_llm_environment

.mcp.json references ${MCP_CODER_VENV_PATH} for MCP server binary
paths, but prepare_llm_environment() never returned it — only .bat
launchers set it. Add it to the returned dict using the existing
venv precedence (VIRTUAL_ENV → CONDA_PREFIX → sys.prefix).

Closes part of #724.
```
