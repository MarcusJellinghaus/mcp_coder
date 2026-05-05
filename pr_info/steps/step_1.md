# Step 1 — Foundation: shim, importlinter, `get_config_file_path` one-liner

## LLM Prompt
> Read `pr_info/steps/summary.md` for full context, then implement
> `pr_info/steps/step_1.md`. This step creates the new local shim,
> updates `.importlinter` in lock-step, and reduces
> `get_config_file_path()` to a one-line delegation through that shim.
> Update tests as instructed (delete platform-branching tests; add one
> thin shim test). Run all four checks (`run_pytest_check`,
> `run_pylint_check`, `run_mypy_check`, `run_lint_imports_check`) before
> committing. The commit must include all of: shim file, importlinter
> update, source change, test changes.

## Why this is one commit
The shim, the `.importlinter` `ignore_imports` entry, and the first
consumer of the shim (`get_config_file_path`) are tightly coupled. If
they land separately, CI fails on the intermediate state.

## WHERE
- **Create**: `src/mcp_coder/utils/user_app_data.py`
- **Modify**: `.importlinter`
- **Modify**: `src/mcp_coder/utils/user_config.py`
- **Modify**: `tests/utils/test_user_config.py`
- **Modify**: `tests/utils/test_user_config_integration.py`
- **Modify**: `tests/cli/commands/test_verify_exit_codes.py`

## WHAT

### New shim — `src/mcp_coder/utils/user_app_data.py`
```python
"""User app data directory shim — re-exports from mcp_coder_utils."""

from mcp_coder_utils.user_app_data import get_user_app_data_dir

__all__ = ["get_user_app_data_dir"]
```

### `user_config.py` — `get_config_file_path` reduced
```python
def get_config_file_path() -> Path:
    """Get the path to the user configuration file.

    Returns:
        Path object pointing to ~/.mcp_coder/config.toml on every platform.
    """
    return get_user_app_data_dir("mcp_coder") / "config.toml"
```

**Explicit docstring deletion**: the existing `get_config_file_path`
docstring contains a platform-bullets block listing each platform's
target path:
```
- Windows: %USERPROFILE%\.mcp_coder\config.toml
- Linux/macOS/Containers: ~/.config/mcp_coder/config.toml
```
**Delete this entire bullet block** (both lines) and replace it with the
single-platform statement shown above. Do not retain either bullet.

**Also delete the in-body XDG comment**: the function body currently
contains a comment `# Linux/macOS/Containers - use XDG Base Directory
Specification`. Remove this comment and any other "XDG Base Directory
Specification" trace alongside the branch removal. Also remove the
`r` prefix on the docstring (no backslash escapes remain).

Also: remove `import platform` (no other use in the file).

### `.importlinter` — extend `mcp_coder_utils_isolation` `ignore_imports`
Add one line under the existing 3:
```ini
ignore_imports =
    mcp_coder.utils.subprocess_runner -> mcp_coder_utils
    mcp_coder.utils.subprocess_streaming -> mcp_coder_utils
    mcp_coder.utils.log_utils -> mcp_coder_utils
    mcp_coder.utils.user_app_data -> mcp_coder_utils
```

## HOW
- Import the helper in `user_config.py`:
  `from mcp_coder.utils.user_app_data import get_user_app_data_dir`
- The shim's only job is re-export; no logic.
- Public symbol `get_config_file_path` is preserved → all existing
  internal callers (`init.py`, coordinator commands, etc.) keep working.

## ALGORITHM
N/A — pure delegation.

## DATA
- `get_user_app_data_dir(app_name: str) -> Path` returns
  `Path.home() / f".{app_name}"` on every platform.
- `get_config_file_path()` returns `Path.home() / ".mcp_coder" / "config.toml"`.

## Test changes (TDD: tests describe new behaviour first)

### Delete
- `tests/utils/test_user_config.py` → delete `TestGetConfigFilePath` class
  entirely.
- `tests/utils/test_user_config_integration.py` → delete
  `test_config_directory_creation_path_verification` and
  `test_path_consistency`. Delete `import platform` at the top of the
  file (only the two deleted test methods used it).

### Add (replacement, in `tests/utils/test_user_config.py`)
One thin assertion that the shim is wired correctly:
```python
def test_get_config_file_path_uses_shim() -> None:
    """get_config_file_path delegates to the user_app_data shim."""
    from mcp_coder.utils.user_app_data import get_user_app_data_dir
    assert get_config_file_path() == get_user_app_data_dir("mcp_coder") / "config.toml"
```

### Fix fixture
- `tests/cli/commands/test_verify_exit_codes.py:459` — change
  `"/home/user/.config/mcp_coder/config.toml"` →
  `str(Path.home() / ".mcp_coder" / "config.toml")` (or hardcoded
  `"~/.mcp_coder/config.toml"` if the fixture is purely textual; check
  which convention the surrounding fixture uses).

## Verification
1. `mcp__mcp-tools-py__run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"])`
2. `mcp__mcp-tools-py__run_pylint_check`
3. `mcp__mcp-tools-py__run_mypy_check`
4. `mcp__mcp-tools-py__run_lint_imports_check` — must show `mcp_coder_utils_isolation` passing.
5. Commit message: `user_config: introduce user_app_data shim and reduce get_config_file_path to one-liner`
