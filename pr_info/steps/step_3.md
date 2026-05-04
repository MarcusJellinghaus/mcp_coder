# Step 3 — Adopt shim in vscodeclaude sessions

## LLM Prompt
> Read `pr_info/steps/summary.md` for context, then implement
> `pr_info/steps/step_3.md`. This step replaces the platform-branching
> `get_sessions_file_path` in `vscodeclaude/sessions.py` with a single
> shim call, and trims the corresponding platform-branching test. Run
> all four checks before committing.

## Why this is one commit
The source change and the test it breaks are inseparable; landing them
together keeps every intermediate state green.

## WHERE
- **Modify**: `src/mcp_coder/workflows/vscodeclaude/sessions.py`
- **Modify**: `tests/workflows/vscodeclaude/test_sessions.py`

## WHAT

### `sessions.py` — `get_sessions_file_path`
Replace:
```python
def get_sessions_file_path() -> Path:
    """Get path to sessions JSON file.

    Returns:
        Path to ~/.mcp_coder/coordinator_cache/vscodeclaude_sessions.json
        on Windows, or ~/.config/mcp_coder/coordinator_cache/vscodeclaude_sessions.json
        on Linux/macOS.
    """
    if platform.system() == "Windows":
        base = Path.home() / ".mcp_coder"
    else:
        base = Path.home() / ".config" / "mcp_coder"
    return base / "coordinator_cache" / "vscodeclaude_sessions.json"
```
With:
```python
def get_sessions_file_path() -> Path:
    """Get path to sessions JSON file.

    Returns:
        Path to ~/.mcp_coder/coordinator_cache/vscodeclaude_sessions.json.
    """
    return (
        get_user_app_data_dir("mcp_coder")
        / "coordinator_cache"
        / "vscodeclaude_sessions.json"
    )
```

**Keep** `import platform` — it is still used by `VSCODE_PROCESS_NAMES`
elsewhere in the file.

### Test file — `tests/workflows/vscodeclaude/test_sessions.py`
- **Delete**: `test_get_sessions_file_path_linux` (lines ~50-62 in
  current file).
- **Rename**: `test_get_sessions_file_path_windows` →
  `test_get_sessions_file_path`. Drop the `monkeypatch.setattr(...,
  "Windows")` line; the assertions (`".mcp_coder" in str(path)`,
  `"vscodeclaude_sessions.json" in str(path)`) hold on every platform.

## HOW
Add at top of `sessions.py`:
```python
from mcp_coder.utils.user_app_data import get_user_app_data_dir
```
(Match existing relative-import style.)

## ALGORITHM
N/A — branch removal.

## DATA
On Linux/macOS the resolved path **changes** from
`~/.config/mcp_coder/coordinator_cache/vscodeclaude_sessions.json` to
`~/.mcp_coder/coordinator_cache/vscodeclaude_sessions.json`. This is
the intended bug fix. File auto-regenerates as VSCode sessions open and
close; no migration logic needed (no Linux/macOS users).

## Verification
1. `mcp__tools-py__run_pytest_check` (fast unit tests)
2. `mcp__tools-py__run_pylint_check`
3. `mcp__tools-py__run_mypy_check`
4. `mcp__tools-py__run_lint_imports_check`
5. Commit message: `vscodeclaude: route sessions file path through user_app_data shim`
