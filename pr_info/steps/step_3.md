# Step 3: New `icoder/env_setup.py` — RuntimeInfo + Environment Setup

> **Context:** Read `pr_info/steps/summary.md` for full issue context.

## Goal

Create the iCoder-specific environment setup module. Pure function: computes tool env, project venv, assembles env vars, verifies MCP binaries, and returns a `RuntimeInfo` dataclass. **No `os.environ` mutation.** Env vars flow to the Claude subprocess because the caller passes `runtime_info.env_vars` into `RealLLMService`, which merges them with `os.environ` in `subprocess_runner.prepare_env()`.

**Intentional deviation from `icoder.bat`:** Does NOT prepend `MCP_CODER_VENV_PATH` to `PATH`. `.mcp.json` uses absolute `${MCP_CODER_VENV_PATH}\...` paths, so `PATH` manipulation is unnecessary.

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
    python_version: str
    claude_code_version: str
    tool_env_path: str          # venv root where mcp-coder is installed (str, not Path)
    project_venv_path: str      # project .venv root or tool_env_path if self-hosting (str)
    project_dir: str            # absolute project dir (str, not Path)
    env_vars: dict[str, str]
    # ^ The effective final values for MCP_CODER_VENV_PATH, MCP_CODER_VENV_DIR,
    #   MCP_CODER_PROJECT_DIR — i.e., pre-set values from os.environ if present,
    #   otherwise computed from sys.prefix / project_dir. All three keys are
    #   always present.
    mcp_servers: list[MCPServerInfo]  # verified MCP server binaries

# All path fields are `str` (not `Path`) to match env_vars and to serialize
# cleanly into the session_start event data. Convert Path -> str at the
# function boundary when constructing RuntimeInfo.

def setup_icoder_environment(project_dir: Path) -> RuntimeInfo:
    """Set up iCoder environment: compute paths, verify MCP servers, return RuntimeInfo.

    Pure function — does NOT mutate os.environ. Env vars are available to
    subprocesses because the caller passes runtime_info.env_vars into
    RealLLMService, which merges with os.environ in prepare_env().
    """
```

### ALGORITHM

```
tool_env = sys.prefix                           # Python IS the tool env
bin_dir = get_bin_dir(Path(tool_env))           # public helper from mcp_verification
project_venv = project_dir / ".venv"
if not project_venv.exists():
    log INFO "No project .venv found — using tool environment for both."
    project_venv = Path(tool_env)

computed = {
    "MCP_CODER_VENV_PATH": str(bin_dir),
    "MCP_CODER_VENV_DIR": str(tool_env),
    "MCP_CODER_PROJECT_DIR": str(project_dir),
}
# Respect pre-set values; log at DEBUG if they differ from computed. Do NOT
# mutate os.environ — return the effective values in env_vars only.
effective: dict[str, str] = {}
for key, value in computed.items():
    existing = os.environ.get(key)
    if existing is None:
        effective[key] = value
    else:
        if existing != value:
            log DEBUG f"{key} already set to {existing} (computed: {value})"
        effective[key] = existing

mcp_servers = verify_mcp_servers(tool_env)
version = importlib.metadata.version("mcp-coder")
return RuntimeInfo(..., env_vars=effective, ...)
```

### DATA

- `RuntimeInfo` — frozen dataclass with all startup info.
- `setup_icoder_environment()` returns `RuntimeInfo` or raises `FileNotFoundError` / `RuntimeError` (from `verify_mcp_servers`) / `PackageNotFoundError` (from `importlib.metadata`).

## HOW

- Uses `sys.prefix` for tool env (NOT `_get_runner_environment()` from `llm/env.py`).
- Imports `verify_mcp_servers`, `MCPServerInfo`, and the **public** `get_bin_dir` from `mcp_coder.utils.mcp_verification` (single source of truth — no local `_get_bin_dir` duplicate).
- Uses `importlib.metadata.version("mcp-coder")` for own version.
- **Pure function** — does NOT mutate `os.environ`. Env vars flow to Claude subprocess via `runtime_info.env_vars` → `RealLLMService` → `subprocess_runner.prepare_env()` merge with `os.environ`.
- Does NOT prepend `MCP_CODER_VENV_PATH` to `PATH` — `.mcp.json` uses absolute paths, so PATH manipulation is unnecessary (intentional deviation from `icoder.bat`).
- `RuntimeInfo` and `setup_icoder_environment` are imported directly from `mcp_coder.icoder.env_setup` — do NOT add them to any `__init__.py` unless a test requires it.

## Constraints

- **Respect pre-set env vars** — If a key is present in `os.environ`, the pre-set value wins. `RuntimeInfo.env_vars` reflects the effective final value (pre-set value if present, otherwise computed). If pre-set differs from computed, log at DEBUG (not warning — expected in two-env dev mode via `icoder_local.bat`). Does NOT mutate `os.environ`.
- **Project `.venv` fallback** — If `<project_dir>/.venv` doesn't exist, fall back to `sys.prefix`. Log at INFO.
- **Intentional behavior change vs `prepare_llm_environment()`** — Inside icoder, `sys.prefix` is the authoritative source for `MCP_CODER_VENV_DIR` (with pre-set `MCP_CODER_*` taking priority). Icoder does NOT use the `VIRTUAL_ENV → CONDA_PREFIX → sys.prefix` precedence from `llm/env.py::_get_runner_environment()`. See `summary.md`.

## Tests (TDD — write first)

Add `tests/icoder/test_env_setup.py`.

**Test isolation:** Use `monkeypatch.setenv` / `monkeypatch.delenv` — NEVER mutate `os.environ` directly. pytest-xdist (`-n auto`) runs tests in parallel and requires isolation.

1. **`test_setup_returns_runtime_info`** — Mock `sys.prefix`, create fake binaries, mock `subprocess.run` and `importlib.metadata.version`. Verify `RuntimeInfo` fields.
2. **`test_tool_env_uses_sys_prefix`** — Verify `tool_env_path` equals `sys.prefix`.
3. **`test_project_venv_found`** — Create `project_dir/.venv`, verify `project_venv_path` points to it.
4. **`test_project_venv_fallback`** — No `.venv` dir, verify fallback to `sys.prefix` and INFO log.
5. **`test_respects_preset_env_vars`** — Parametrized `@pytest.mark.parametrize("key", ["MCP_CODER_VENV_PATH", "MCP_CODER_VENV_DIR", "MCP_CODER_PROJECT_DIR"])`. For each key, pre-set it via `monkeypatch.setenv`, verify `RuntimeInfo.env_vars[key]` contains the pre-set value (not the computed one) AND `os.environ` is unchanged. This fully covers the per-key loop in the algorithm.
6. **`test_logs_debug_when_preset_differs`** — Pre-set a var with different value via monkeypatch, verify DEBUG log emitted and effective value is the pre-set one.
7. **`test_env_vars_always_contain_all_three_keys`** — With no pre-set vars (all `delenv`'d), verify `RuntimeInfo.env_vars` has all three `MCP_CODER_*` keys and `os.environ` is NOT mutated.
8. **`test_does_not_mutate_os_environ`** — Snapshot `os.environ` keys before the call, verify no new `MCP_CODER_*` keys were added afterwards.
9. **`test_mcp_servers_verified`** — Verify `mcp_servers` list in returned `RuntimeInfo` is populated from `verify_mcp_servers`.

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
