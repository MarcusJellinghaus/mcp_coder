# Step 3: New `icoder/env_setup.py` — RuntimeInfo + Environment Setup

> **Context:** Read `pr_info/steps/summary.md` for full issue context.

## Goal

Create the iCoder-specific environment setup module. Computes tool env, project venv, assembles env vars, verifies MCP binaries, and returns a `RuntimeInfo` dataclass.

## WHERE

- **Create:** `src/mcp_coder/icoder/env_setup.py`
- **Create:** `tests/icoder/test_env_setup.py`

## WHAT

### `src/mcp_coder/icoder/env_setup.py`

```python
@dataclass(frozen=True)
class RuntimeInfo:
    """Runtime information gathered during iCoder startup."""
    mcp_coder_version: str
    tool_env_path: str          # venv root where mcp-coder is installed
    project_venv_path: str      # project .venv root (or tool_env_path if self-hosting)
    project_dir: str
    env_vars: dict[str, str]    # MCP_CODER_* vars that were applied
    mcp_servers: list[MCPServerInfo]  # verified MCP server binaries

def setup_icoder_environment(project_dir: Path) -> RuntimeInfo:
    """Set up iCoder environment: compute paths, set env vars, verify MCP servers."""
```

### ALGORITHM

```
tool_env = sys.prefix                           # Python IS the tool env
bin_dir = _get_bin_dir(tool_env)                # from mcp_verification
project_venv = project_dir / ".venv"
if not project_venv.exists():
    log INFO "No project .venv found — using tool environment for both."
    project_venv = Path(tool_env)

env_vars = {
    "MCP_CODER_VENV_PATH": str(bin_dir),
    "MCP_CODER_VENV_DIR": str(tool_env),
    "MCP_CODER_PROJECT_DIR": str(project_dir),
}
for key, value in env_vars.items():
    existing = os.environ.get(key)
    if existing is None:
        os.environ[key] = value
    elif existing != value:
        log DEBUG f"{key} already set to {existing} (computed: {value})"

mcp_servers = verify_mcp_servers(tool_env)
version = importlib.metadata.version("mcp-coder")
return RuntimeInfo(...)
```

### DATA

- `RuntimeInfo` — frozen dataclass with all startup info.
- `setup_icoder_environment()` returns `RuntimeInfo` or raises `FileNotFoundError` (from `verify_mcp_servers`) / `PackageNotFoundError` (from `importlib.metadata`).

## HOW

- Uses `sys.prefix` for tool env (NOT `_get_runner_environment()` from `llm/env.py`).
- Imports `verify_mcp_servers`, `MCPServerInfo`, `_get_bin_dir` from `utils.mcp_verification`.
- Uses `importlib.metadata.version("mcp-coder")` for own version.
- Sets `os.environ` for vars not already present.

## Constraints

- **Respect pre-set env vars** — Only set if missing from `os.environ`. If pre-set differs from computed, log at DEBUG (not warning — expected in two-env dev mode via `icoder_local.bat`).
- **Project `.venv` fallback** — If `<project_dir>/.venv` doesn't exist, fall back to `sys.prefix`. Log at INFO.

## Tests (TDD — write first)

Add `tests/icoder/test_env_setup.py`:

1. **`test_setup_returns_runtime_info`** — Mock `sys.prefix`, create fake binaries, mock `subprocess.run` and `importlib.metadata.version`. Verify `RuntimeInfo` fields.
2. **`test_tool_env_uses_sys_prefix`** — Verify `tool_env_path` equals `sys.prefix`.
3. **`test_project_venv_found`** — Create `project_dir/.venv`, verify `project_venv_path` points to it.
4. **`test_project_venv_fallback`** — No `.venv` dir, verify fallback to `sys.prefix` and INFO log.
5. **`test_respects_preset_env_vars`** — Pre-set `MCP_CODER_VENV_PATH` in env, verify it's NOT overwritten.
6. **`test_logs_debug_when_preset_differs`** — Pre-set a var with different value, verify DEBUG log emitted.
7. **`test_sets_missing_env_vars`** — No pre-set vars, verify `os.environ` updated after call.
8. **`test_mcp_servers_verified`** — Verify `mcp_servers` list in returned `RuntimeInfo` is populated from `verify_mcp_servers`.

## Commit

```
feat(icoder): add env_setup module with RuntimeInfo

New icoder/env_setup.py provides iCoder-specific environment setup:
- Tool env from sys.prefix (no PATH scanning)
- Project venv from <project_dir>/.venv with fallback
- Respects pre-set MCP_CODER_* env vars (for icoder_local.bat)
- Returns RuntimeInfo dataclass with all startup info

Part of #724.
```
