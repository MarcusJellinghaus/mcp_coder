# Step 1: Add `MCP_CODER_VENV_PATH` to `prepare_llm_environment()`

> **Context:** Read `pr_info/steps/summary.md` for full issue context.

## Goal

Fix latent bug: `.mcp.json` references `${MCP_CODER_VENV_PATH}` but `prepare_llm_environment()` never returns it. Only `.bat` launchers set it today. Add it to the returned dict so all Python callers get it.

## WHERE

- **Modify:** `src/mcp_coder/llm/env.py`
- **Modify:** `tests/llm/test_env.py`

## WHAT

### `src/mcp_coder/llm/env.py`

Import the shared `get_bin_dir` helper from `utils.mcp_verification` (defined in Step 2) and include `MCP_CODER_VENV_PATH` in the returned dict.

```python
from mcp_coder.utils.mcp_verification import get_bin_dir
```

Update `prepare_llm_environment()` return dict to include `MCP_CODER_VENV_PATH`.

- Update the `prepare_llm_environment()` docstring to document the new `MCP_CODER_VENV_PATH` key in the returned dict (absolute OS-native path to the venv `Scripts`/`bin` subdir).

### ALGORITHM

```
venv_root = _get_runner_environment()  # existing, unchanged
venv_path = get_bin_dir(Path(venv_root))  # shared helper from utils.mcp_verification
return {
    "MCP_CODER_PROJECT_DIR": ...,    # existing
    "MCP_CODER_VENV_DIR": ...,       # existing
    "MCP_CODER_VENV_PATH": str(venv_path.resolve()),  # NEW
}
```

### DATA

Return type stays `dict[str, str]`. New key `MCP_CODER_VENV_PATH` added — value is the absolute OS-native path to the `Scripts` (Windows) or `bin` (POSIX) subdirectory of the resolved venv root.

## HOW

- Import `get_bin_dir` from `mcp_coder.utils.mcp_verification` (single source of truth, defined in Step 2). Do NOT define a local `_get_bin_dir` duplicate.
- No change to `_get_runner_environment()` or its precedence logic.
- Do NOT add `get_bin_dir` to any `__init__.py` — import directly from the module.

**Note:** Step 1 depends on Step 2 being merged first (or the helper can be added in Step 2 and imported here as the steps land together).

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
