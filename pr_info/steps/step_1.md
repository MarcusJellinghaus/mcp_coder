# Step 1: Create `crash_logging.py` module with unit tests

> **Context**: See `pr_info/steps/summary.md` for full issue context (Issue #712).

## LLM Prompt

```
Implement step 1 of issue #712 (see pr_info/steps/summary.md for context).

Create the crash_logging utility module and its unit tests. The module provides
enable_crash_logging() which enables faulthandler with a persistent crash log file.
Follow TDD: write tests first, then implement the module to make them pass.
Run all three quality checks (pylint, pytest, mypy) after implementation.
```

## WHERE

- **Create**: `src/mcp_coder/utils/crash_logging.py`
- **Create**: `tests/utils/test_crash_logging.py`

## WHAT

### `src/mcp_coder/utils/crash_logging.py`

```python
def enable_crash_logging(project_dir: Path, command_name: str) -> Path | None:
    """Enable faulthandler with a persistent per-process crash log."""

def _reset_for_testing() -> None:
    """Close the active handle and clear module state. Test-only helper."""
```

### Module-level state

```python
_state: dict[str, Any] = {"path": None, "handle": None}
```

## HOW

- Import `faulthandler`, `logging`, `os` from stdlib
- Timestamp format: `datetime.now().isoformat().replace(":", "-").split(".")[0]` (matches `session_storage.py:62`)
- Log directory: `{project_dir}/logs/faulthandler/`
- Filename: `crash_{command_name}_{timestamp}_{pid}.log`
- File opened with `open(..., "w", buffering=1)` (line-buffered)
- Handle stored in `_state["handle"]`, path in `_state["path"]`
- `faulthandler.enable(file=_state["handle"], all_threads=True)`

## ALGORITHM — `enable_crash_logging`

```
if _state["path"] is not None: return _state["path"]  # idempotent
try:
    create logs/faulthandler/ directory (exist_ok=True)
    open crash log file (line-buffered)
    store handle and path in _state
    call faulthandler.enable(file=handle, all_threads=True)
    log path at DEBUG, return path
except Exception:
    log WARNING, return None
```

## ALGORITHM — `_reset_for_testing`

```
if _state["handle"] is not None:
    _state["handle"].close()
_state["path"] = None
_state["handle"] = None
```

## DATA

- `_state`: `dict[str, Any]` with keys `"path"` (Path | None) and `"handle"` (IO | None)
- Return: `Path` to crash log file, or `None` on failure

## Tests — `tests/utils/test_crash_logging.py`

Use `tmp_path` fixture. Call `_reset_for_testing()` in a fixture's teardown to isolate tests.

| Test | What it verifies |
|------|-----------------|
| `test_enable_creates_file` | File created at expected path under `logs/faulthandler/`, filename matches pattern |
| `test_enable_calls_faulthandler` | Mock `faulthandler.enable`, verify called with `file=<handle>, all_threads=True` |
| `test_enable_returns_path` | Return value is a `Path` instance |
| `test_enable_logs_debug` | DEBUG log message contains the crash log path |
| `test_enable_idempotent` | Second call returns same path, `faulthandler.enable` called only once |
| `test_enable_swallows_error` | Mock `os.makedirs` to raise `OSError`, verify returns `None` and logs WARNING |
| `test_reset_clears_state` | After `_reset_for_testing()`, a new call creates a new file |
