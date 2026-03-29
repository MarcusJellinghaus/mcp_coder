# Python Environments Architecture

## Two Environment Types

When mcp-coder works on a project, two distinct Python environments are involved:

### 1. Tool Environment

Where mcp-coder and MCP servers are installed. Provides the tooling.

Example: `C:\Jenkins\environments\mcp-coder-dev\.venv` (Python 3.13)

**Contains:** mcp-coder, mcp-tools-py, mcp-workspace, pytest, pylint, mypy, and their dependencies.

### 2. Project Environment

Where the project's dependencies live. May or may not be inside the project directory.

Examples:
- `C:\Users\Marcus\Documents\VSCC\mcp_coder_598\.venv` — inside project dir
- `C:\Jenkins\environments\some-project\.venv` — separate location

**Contains:** the project's library dependencies.

## Environment Variables Reference

| Variable | Points to | Purpose | Set by | Read by |
|----------|-----------|---------|--------|---------|
| `VIRTUAL_ENV` | Project env venv root | Standard Python venv indicator; identifies the active project environment | venv `activate.bat` | `env.py`, `.mcp.json`, batch launchers |
| `MCP_CODER_PROJECT_DIR` | Project root directory | Tells MCP servers where project source code lives | `env.py`, `templates.py`, batch launchers | `.mcp.json`, `interface.py`, `claude_code_cli.py` |
| `MCP_CODER_VENV_DIR` | Tool env venv root | Tells MCP servers where tool env is (for `PYTHONPATH`) | `env.py`, `templates.py`, batch launchers | `.mcp.json` (workspace server `PYTHONPATH`) |
| `MCP_CODER_VENV_PATH` | Tool env `Scripts` dir | Added to PATH so MCP server executables are found | `templates.py` (vscodeclaude startup) | PATH resolution, `.mcp.json` `command` fields |
| `PYTHONPATH` | Project `src/` or tool env `Lib/` | Module discovery for MCP server processes | `.mcp.json` `env` section | Python import system |
| `DISABLE_AUTOUPDATER` | `1` | Prevents Claude CLI auto-updates during automation | `command_templates.py`, batch launchers | Claude CLI |

### Variable relationships

```
Tool env venv root:     C:\Jenkins\environments\mcp-coder-dev\.venv
                        ↑ MCP_CODER_VENV_DIR (venv root)
                        ↑ MCP_CODER_VENV_PATH = {root}\Scripts (executables)

Project env venv root:  C:\Users\Marcus\Documents\VSCC\project\.venv
                        ↑ VIRTUAL_ENV (set by activate.bat)

Project root:           C:\Users\Marcus\Documents\VSCC\project
                        ↑ MCP_CODER_PROJECT_DIR
```

## Who Sets the Environments?

There are two paths that set up environment variables: batch launchers (for interactive use) and Python code (for programmatic LLM invocation).

### Entry Point Matrix

| Entry point | Sets tool env how | Sets project env how | Two-env aware? |
|---|---|---|---|
| `.vscodeclaude_start.bat` (coordinator) | `MCP_CODER_VENV_PATH` on PATH | activates project `.venv`, sets `VIRTUAL_ENV` | **Yes** |
| `claude.bat` | Not yet — assumes single env | activates `.venv` | **No** (to be fixed in #613) |
| `claude_local.bat` | Not yet — assumes single env | activates `.venv` with wrong-venv detection | **No** (to be fixed in #613) |
| `env.py` (`prepare_llm_environment()`) | Sets `MCP_CODER_VENV_DIR` from `VIRTUAL_ENV` / `CONDA_PREFIX` / `sys.prefix` | Sets `MCP_CODER_PROJECT_DIR` from `project_dir` arg | **Partial** — reads whatever venv is active |

### How `.vscodeclaude_start.bat` Does It (Coordinator)

This is the most complete implementation. It already separates the two environments:

```batch
REM Tool env: added to PATH for mcp-coder CLI and MCP server executables
set "MCP_CODER_VENV_PATH=C:\Jenkins\environments\mcp-coder-dev\.venv\Scripts"
set "PATH=%MCP_CODER_VENV_PATH%;%PATH%"

REM Project env: activated, sets VIRTUAL_ENV
call .venv\Scripts\activate.bat
```

Result:
- `VIRTUAL_ENV` → project env (`.venv`, Python 3.11)
- `PATH` → tool env first (Jenkins, Python 3.13), then project env

The coordinator knows the tool env path because it **runs from it** — `get_mcp_coder_install_path()` in `workspace.py` detects the installation directory at generation time and bakes it into the startup script.

### How `env.py` Does It (Python Path)

When mcp-coder invokes Claude programmatically (e.g. `mcp-coder prompt`), `prepare_llm_environment()` sets environment variables for the subprocess:

```python
# Priority: VIRTUAL_ENV > CONDA_PREFIX > sys.prefix
runner_venv = os.environ.get("VIRTUAL_ENV") or ...

env_vars = {
    "MCP_CODER_PROJECT_DIR": str(project_dir),
    "MCP_CODER_VENV_DIR": runner_venv,
}
```

This sets `MCP_CODER_VENV_DIR` to whatever venv is currently active. In the two-env model, `VIRTUAL_ENV` is the project env at this point (the tool env is only on PATH), so `MCP_CODER_VENV_DIR` ends up pointing to the **project** env — not the tool env. This is a known limitation.

### How `claude.bat` Does It (Current — Broken)

Simpler: activates the project-local `.venv` if no venv is active. Assumes mcp-coder is installed in that same venv. Works only when tool env = project env.

### How `claude_local.bat` Does It (Current — Broken)

For local development: ensures the project `.venv` is active and mcp-coder is importable from it. Deactivates wrong venvs. Assumes mcp-coder is editable-installed in the project env.

## Which Environment Runs What?

| Operation | Environment | Why |
|-----------|------------|-----|
| `mcp-coder` CLI | Tool env (via PATH) | It's a tool, not part of the project |
| MCP server processes (`mcp-tools-py`, `mcp-workspace`) | Tool env | MCP servers are tools |
| `pytest` / `pylint` / `mypy` | Project env | Tests import project code and its dependencies |

The MCP server runs in the tool env but launches pytest/pylint/mypy using the **project's Python** via `--venv-path`.

## Configuration (`.mcp.json`)

### Current State (Broken)

```json
{
  "tools-py": {
    "command": "${VIRTUAL_ENV}\\Scripts\\mcp-tools-py.exe",
    "args": [
      "--project-dir", "${MCP_CODER_PROJECT_DIR}",
      "--venv-path", "${VIRTUAL_ENV}",
      "--python-executable", "${VIRTUAL_ENV}\\Scripts\\python.exe"
    ]
  },
  "workspace": {
    "command": "${VIRTUAL_ENV}/Scripts/mcp-workspace.exe",
    "args": ["--project-dir", "${MCP_CODER_PROJECT_DIR}"]
  }
}
```

### Problem: `${VIRTUAL_ENV}` Used for Both Environments

`.mcp.json` uses `${VIRTUAL_ENV}` for:
1. **MCP server executable** (`command`) — should come from the **tool env**
2. **`--venv-path`** for pytest execution — should come from the **project env**

This works today only because `uv sync --extra dev` installs mcp-tools-py into the project env redundantly (the project IS mcp-coder, so its dependencies include the MCP servers). For other projects, `${VIRTUAL_ENV}\Scripts\mcp-tools-py.exe` would not exist.

### Target State (After #613)

```json
{
  "tools-py": {
    "command": "${MCP_CODER_VENV_PATH}\\mcp-tools-py.exe",
    "args": [
      "--project-dir", "${MCP_CODER_PROJECT_DIR}",
      "--venv-path", "${VIRTUAL_ENV}",
      "--python-executable", "${VIRTUAL_ENV}\\Scripts\\python.exe"
    ]
  },
  "workspace": {
    "command": "${MCP_CODER_VENV_PATH}\\mcp-workspace.exe",
    "args": ["--project-dir", "${MCP_CODER_PROJECT_DIR}"]
  }
}
```

`command` uses `${MCP_CODER_VENV_PATH}` (tool env Scripts dir), while `--venv-path` and `--python-executable` stay as `${VIRTUAL_ENV}` (project env).

## Observed Issue: Python Version Mismatch

Because `VIRTUAL_ENV` (project env, Python 3.11) differs from what's first on PATH (tool env, Python 3.13):

| Command | Python used | Source |
|---------|------------|--------|
| `python -m pytest` in shell | 3.13 | PATH → tool env |
| MCP pytest server | 3.11 | `${VIRTUAL_ENV}` → project env |

This caused flaky `caplog` + `pytest-xdist` failures: a known Python 3.11 bug fixed in 3.13. Tests passed when run directly but failed intermittently through the MCP server.

## Special Case: mcp-coder Working on Itself

When the project IS mcp-coder, the tool env already has all project dependencies. A separate project `.venv` is redundant — the tool env's pytest can execute the project's tests directly (with `PYTHONPATH` pointing to `src/`).

However, the current scripts always create a project `.venv` via `uv sync --extra dev`, which installs a second copy of everything. This is wasteful but not harmful (except for the Python version mismatch above).

## Project Environment Location

The project environment does not have to be inside the project directory. The launch scripts just need to tell mcp-coder where it is. This supports:
- Project `.venv` inside the repo
- Shared environments in a central location (e.g., `C:\Jenkins\environments\`)
- No separate project environment (when tool env has everything needed)
