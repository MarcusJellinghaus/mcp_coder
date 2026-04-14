# Step 1: Dependency + subprocess shims

**Commit message:** `adopt mcp-coder-utils: subprocess shims + delete broken subprocess tests`

> **Context:** See `pr_info/steps/summary.md` for the full plan (issue #744).
> This step pins the dependency and replaces `subprocess_runner.py` and `subprocess_streaming.py` with thin re-export shims.

## WHERE

- `pyproject.toml` — dependencies section
- `src/mcp_coder/utils/subprocess_runner.py` — replace body
- `src/mcp_coder/utils/subprocess_streaming.py` — replace body
- `tests/utils/test_subprocess_runner.py` — delete
- `tests/utils/test_subprocess_runner_real.py` — delete
- `tests/utils/test_subprocess_streaming.py` — delete

## WHAT

### pyproject.toml
Change `"mcp-coder-utils"` to `"mcp-coder-utils>=0.1.3"` in the `dependencies` list.

### subprocess_runner.py — re-export shim
Replace the entire file body with re-exports from `mcp_coder_utils.subprocess_runner`.

Must re-export all names currently in `__all__`:
- `CommandResult`, `CommandOptions`, `MAX_STDERR_IN_ERROR`
- `check_tool_missing_error`, `execute_command`, `execute_subprocess`, `launch_process`, `truncate_stderr`
- `CalledProcessError`, `SubprocessError`, `TimeoutExpired` (re-exported exceptions)

Also re-export internal names:
- `prepare_env` (used by other production modules)
- `is_python_command`, `get_python_isolation_env`, `get_utf8_env` — re-exported for API completeness — no current external consumers but available for future use
- `_run_heartbeat` — re-exported for API completeness

### subprocess_streaming.py — re-export shim
Replace the entire file body with re-exports from `mcp_coder_utils.subprocess_streaming`.

Must re-export: `StreamResult`, `stream_subprocess`

### Delete 3 subprocess test files
These test files must be deleted in this same step because they break immediately once the shim replaces the full implementation:
- `test_subprocess_runner.py` — patches internal names like `_run_subprocess`, `threading` that no longer exist in the shim module
- `test_subprocess_runner_real.py` — patches internal names like `_run_subprocess` that no longer exist in the shim module
- `test_subprocess_streaming.py` — wraps `StreamResult(stream_subprocess(...))` which double-wraps now that `stream_subprocess` returns `StreamResult` directly

Core test coverage for these modules now lives in the `mcp-coder-utils` package.

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

## ALGORITHM (test deletions)

```
Delete:
- tests/utils/test_subprocess_runner.py
- tests/utils/test_subprocess_runner_real.py
- tests/utils/test_subprocess_streaming.py
```

## DATA

No new data structures. All types come from `mcp_coder_utils`.

## VERIFICATION

- All existing imports (`from mcp_coder.utils.subprocess_runner import ...`) still resolve
- Remaining tests pass (deleted tests no longer cause import/patch errors)
- Run pylint, mypy, pytest

## LLM PROMPT

```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md.

Implement step 1: Pin mcp-coder-utils>=0.1.3 in pyproject.toml, then replace
subprocess_runner.py and subprocess_streaming.py with thin re-export shims
over mcp_coder_utils. Keep __all__ lists matching current exports.
Also delete tests/utils/test_subprocess_runner.py,
tests/utils/test_subprocess_runner_real.py, and
tests/utils/test_subprocess_streaming.py (they patch internals that no longer
exist in the shim). Do NOT modify any other files. Run all checks after.
```
