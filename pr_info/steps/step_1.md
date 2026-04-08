# Step 1: New `utils/mcp_verification.py` — Cross-Platform MCP Binary Verification

> **Context:** Read `pr_info/steps/summary.md` for full issue context.

## Goal

Create a generic, reusable utility that verifies MCP server binaries exist in a given venv bin directory and captures their `--version` output. Cross-platform from day one.

This step lands **first** because Step 2 (adding `MCP_CODER_VENV_PATH` to `prepare_llm_environment`) imports `get_bin_dir` from this module.

## WHERE

- **Create:** `src/mcp_coder/utils/mcp_verification.py`
- **Create:** `tests/utils/test_mcp_verification.py`

## WHAT

### `src/mcp_coder/utils/mcp_verification.py`

```python
MCP_SERVER_NAMES: list[str] = ["mcp-tools-py", "mcp-workspace"]

def get_bin_dir(venv_root: str | Path) -> Path:
    """Return Scripts (Windows) or bin (POSIX) subdirectory.

    Single source of truth — also imported by llm/env.py and icoder/env_setup.py.
    """

def _exe_name(name: str) -> str:
    """Return name.exe on Windows, name on POSIX."""

@dataclass(frozen=True)
class MCPServerInfo:
    """Verified MCP server binary info."""
    name: str
    path: Path
    version: str

def verify_mcp_servers(venv_root: str | Path) -> list[MCPServerInfo]:
    """Verify MCP server binaries exist and capture their versions.

    Raises FileNotFoundError if a binary is missing.
    Raises RuntimeError if a binary exists but `--version` fails
    (OSError/FileNotFoundError from subprocess.run, or non-zero returncode).
    """
```

### ALGORITHM

```
bin_dir = get_bin_dir(venv_root)
results = []
for name in MCP_SERVER_NAMES:
    exe_path = bin_dir / _exe_name(name)
    if not exe_path.exists():
        raise FileNotFoundError(f"{_exe_name(name)} not found in {bin_dir}")
    try:
        proc = subprocess.run(
            [str(exe_path), "--version"],
            capture_output=True, text=True,
        )
    except (FileNotFoundError, OSError) as e:
        raise RuntimeError(f"Failed to invoke {exe_path}: {e}") from e
    if proc.returncode != 0:
        raise RuntimeError(
            f"{exe_path} --version exited with code {proc.returncode}: {proc.stderr.strip()}"
        )
    version = proc.stdout.strip()
    results.append(MCPServerInfo(name=name, path=exe_path, version=version))
return results
```

### DATA

- `MCPServerInfo` dataclass: `name` (e.g. `"mcp-tools-py"`), `path` (absolute `Path`), `version` (stdout string).
- `verify_mcp_servers()` returns `list[MCPServerInfo]`. Raises `FileNotFoundError` (missing binary) or `RuntimeError` (binary present but `--version` failed — never silently swallow failures).

## HOW

- Uses `sys.platform` for cross-platform logic.
- Uses `subprocess.run` for `--version` capture.
- No dependency on other `mcp_coder` modules — fully standalone utility.
- `get_bin_dir` is the **public** single source of truth, imported by `llm/env.py` (Step 2) and `icoder/env_setup.py` (Step 3). `_exe_name` stays private.
- These symbols (`get_bin_dir`, `MCPServerInfo`, `verify_mcp_servers`) are imported directly from `mcp_coder.utils.mcp_verification` — do NOT add them to any `__init__.py` unless a test requires it.

## Tests (TDD — write first)

Add `tests/utils/test_mcp_verification.py`.

**Test isolation:** Use `monkeypatch.setattr(sys, "platform", ...)` — never mutate `sys.platform` directly. pytest-xdist (`-n auto`) runs tests in parallel and requires isolation.

1. **`test_get_bin_dir`** (parametrized) — Single `@pytest.mark.parametrize` over `(platform, expected_subdir)` pairs `[("win32", "Scripts"), ("linux", "bin"), ("darwin", "bin")]`, monkeypatching `sys.platform`.
2. **`test_exe_name`** (parametrized) — Single `@pytest.mark.parametrize` over `(platform, expected_suffix)` pairs, monkeypatching `sys.platform`.
3. **`test_verify_mcp_servers_success`** — Create fake executables in tmp_path, mock `subprocess.run`, verify returns `MCPServerInfo` list.
4. **`test_verify_mcp_servers_missing_binary`** — Empty bin dir, verify `FileNotFoundError` with clear message.
5. **`test_verify_mcp_servers_version_capture`** — Mock `subprocess.run` to return version string, verify it's captured.
6. **`test_verify_mcp_servers_version_nonzero_raises`** — Binary exists but `subprocess.run` returns `returncode=1` → verify `RuntimeError` is raised and the message names the binary.
7. **`test_verify_mcp_servers_subprocess_oserror_raises`** — Binary exists but `subprocess.run` raises `OSError` → verify `RuntimeError` is raised (chained from the OSError).

## Commit

```
feat(utils): add cross-platform MCP server verification

New utils/mcp_verification.py provides generic verification of MCP
server binaries (existence check + version capture). Cross-platform
via public get_bin_dir() and private _exe_name() helpers. Tests
parametrize over sys.platform via monkeypatch.

Part of #724.
```
