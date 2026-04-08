# Step 2: New `utils/mcp_verification.py` — Cross-Platform MCP Binary Verification

> **Context:** Read `pr_info/steps/summary.md` for full issue context.

## Goal

Create a generic, reusable utility that verifies MCP server binaries exist in a given venv bin directory and captures their `--version` output. Cross-platform from day one.

## WHERE

- **Create:** `src/mcp_coder/utils/mcp_verification.py`
- **Create:** `tests/utils/test_mcp_verification.py`

## WHAT

### `src/mcp_coder/utils/mcp_verification.py`

```python
MCP_SERVER_NAMES: list[str] = ["mcp-tools-py", "mcp-workspace"]

def _get_bin_dir(venv_root: str | Path) -> Path:
    """Return Scripts (Windows) or bin (POSIX) subdirectory."""

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

    Raises FileNotFoundError if any binary is missing.
    """
```

### ALGORITHM

```
bin_dir = _get_bin_dir(venv_root)
results = []
for name in MCP_SERVER_NAMES:
    exe_path = bin_dir / _exe_name(name)
    if not exe_path.exists():
        raise FileNotFoundError(f"{_exe_name(name)} not found in {bin_dir}")
    version = subprocess.run([str(exe_path), "--version"], capture_output=True, text=True).stdout.strip()
    results.append(MCPServerInfo(name=name, path=exe_path, version=version))
return results
```

### DATA

- `MCPServerInfo` dataclass: `name` (e.g. `"mcp-tools-py"`), `path` (absolute `Path`), `version` (stdout string).
- `verify_mcp_servers()` returns `list[MCPServerInfo]` or raises `FileNotFoundError`.

## HOW

- Uses `sys.platform` for cross-platform logic.
- Uses `subprocess.run` for `--version` capture.
- No dependency on other `mcp_coder` modules — fully standalone utility.

## Tests (TDD — write first)

Add `tests/utils/test_mcp_verification.py`:

1. **`test_get_bin_dir_windows`** — Monkeypatch `sys.platform = "win32"`, verify returns `Scripts` subdir.
2. **`test_get_bin_dir_posix`** — Monkeypatch `sys.platform = "linux"`, verify returns `bin` subdir.
3. **`test_exe_name_windows`** — Monkeypatch `sys.platform = "win32"`, verify `.exe` suffix.
4. **`test_exe_name_posix`** — Monkeypatch `sys.platform = "linux"`, verify no suffix.
5. **`test_verify_mcp_servers_success`** — Create fake executables in tmp_path, mock `subprocess.run`, verify returns `MCPServerInfo` list.
6. **`test_verify_mcp_servers_missing_binary`** — Empty bin dir, verify `FileNotFoundError` with clear message.
7. **`test_verify_mcp_servers_version_capture`** — Mock `subprocess.run` to return version string, verify it's captured.

## Commit

```
feat(utils): add cross-platform MCP server verification

New utils/mcp_verification.py provides generic verification of MCP
server binaries (existence check + version capture). Cross-platform
via _get_bin_dir() and _exe_name() helpers. Tests parametrize over
sys.platform via monkeypatch.

Part of #724.
```
