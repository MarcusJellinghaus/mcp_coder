# Step 1: Dependency + subprocess shims

**Commit message:** `adopt mcp-coder-utils: subprocess_runner and subprocess_streaming shims`

> **Context:** See `pr_info/steps/summary.md` for the full plan (issue #744).
> This step pins the dependency and replaces `subprocess_runner.py` and `subprocess_streaming.py` with thin re-export shims.

## WHERE

- `pyproject.toml` — dependencies section
- `src/mcp_coder/utils/subprocess_runner.py` — replace body
- `src/mcp_coder/utils/subprocess_streaming.py` — replace body

## WHAT

### pyproject.toml
Change `"mcp-coder-utils"` to `"mcp-coder-utils>=0.1.3"` in the `dependencies` list.

### subprocess_runner.py — re-export shim
Replace the entire file body with re-exports from `mcp_coder_utils.subprocess_runner`.

Must re-export all names currently in `__all__`:
- `CommandResult`, `CommandOptions`, `MAX_STDERR_IN_ERROR`
- `check_tool_missing_error`, `execute_command`, `execute_subprocess`, `launch_process`, `truncate_stderr`
- `CalledProcessError`, `SubprocessError`, `TimeoutExpired` (re-exported exceptions)

Also re-export internal names used by other modules in this project:
- `prepare_env`, `is_python_command`, `get_python_isolation_env`, `get_utf8_env`
- `_run_heartbeat` (used by existing tests — but those tests will be deleted in step 5; still re-export for safety during intermediate steps)

### subprocess_streaming.py — re-export shim
Replace the entire file body with re-exports from `mcp_coder_utils.subprocess_streaming`.

Must re-export: `StreamResult`, `stream_subprocess`

## HOW

Each shim file:
1. Module docstring explaining it's a thin shim
2. `from mcp_coder_utils.<module> import <names>` 
3. `__all__` listing re-exported names

No local logic. No imports of `subprocess`, `os`, `signal`, `threading`, etc.

## ALGORITHM (subprocess_runner.py shim)

```python
"""Subprocess execution utilities — thin shim over mcp-coder-utils."""
from mcp_coder_utils.subprocess_runner import (
    CommandResult, CommandOptions, MAX_STDERR_IN_ERROR,
    check_tool_missing_error, execute_command, execute_subprocess,
    launch_process, truncate_stderr, prepare_env, is_python_command,
    get_python_isolation_env, get_utf8_env, _run_heartbeat,
    CalledProcessError, SubprocessError, TimeoutExpired,
)
__all__ = [...]
```

## ALGORITHM (subprocess_streaming.py shim)

```python
"""Streaming subprocess execution — thin shim over mcp-coder-utils."""
from mcp_coder_utils.subprocess_streaming import StreamResult, stream_subprocess
__all__ = ["StreamResult", "stream_subprocess"]
```

## DATA

No new data structures. All types come from `mcp_coder_utils`.

## VERIFICATION

- All existing imports (`from mcp_coder.utils.subprocess_runner import ...`) still resolve
- Existing tests pass (they import from the shim, which delegates to mcp_coder_utils)
- Run pylint, mypy, pytest

## LLM PROMPT

```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md.

Implement step 1: Pin mcp-coder-utils>=0.1.3 in pyproject.toml, then replace
subprocess_runner.py and subprocess_streaming.py with thin re-export shims
over mcp_coder_utils. Keep __all__ lists matching current exports.
Do NOT modify any other files. Run all checks after.
```
