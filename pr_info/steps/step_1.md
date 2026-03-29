# Step 1: Create real-subprocess integration tests

**Commit:** `test: add real-subprocess integration tests for subprocess_runner (#623)`

## WHERE

- **Create:** `tests/utils/test_subprocess_runner_real.py`

## WHAT

No new production functions. One new test file with:

- `temp_dir` fixture — `Generator[Path, None, None]` (Windows-safe temp directory cleanup)
- `TestExecuteSubprocessReal` — 9 test methods
- `TestSTDIOIsolationReal` — 7 test methods (excludes `test_is_python_command_detection`, moved to detection class)
- `TestPythonCommandDetectionReal` — 3 test methods (includes moved `test_is_python_command_detection`)
- `TestIntegrationScenariosReal` — 4 test methods
- `TestErrorHandlingReal` — 3 test methods

## HOW

**Imports from `mcp_coder.utils.subprocess_runner`:**
```python
from mcp_coder.utils.subprocess_runner import (
    CommandOptions,
    CommandResult,
    execute_command,
    execute_subprocess,
    get_python_isolation_env,
    is_python_command,
)
```

**Standard library imports:** `gc`, `os`, `queue`, `subprocess`, `sys`, `tempfile`, `threading`, `time`
**Third-party:** `pytest`
**Mock usage:** `unittest.mock.patch` (only for `test_execute_command_permission_error`)

## ALGORITHM

No algorithm — this is a mechanical port:

```
1. Copy p_tools/tests/test_subprocess_runner.py content
2. Replace import path to mcp_coder
3. Rename 5 classes with Real suffix
4. Move test_is_python_command_detection to TestPythonCommandDetectionReal
5. Remove excluded classes (TestCommandResult, TestCommandOptions, TestConvenienceFunctions, fixtures)
6. Remove test_execute_command_unexpected_error (incompatible error handling)
```

## DATA

All tests assert on `CommandResult` fields:
- `return_code: int`
- `stdout: str`
- `stderr: str`
- `timed_out: bool`
- `execution_error: str | None`
- `command: list[str] | None`
- `runner_type: str | None`
- `execution_time_ms: int | None`

## Key Adaptations

1. **`temp_dir` fixture**: Defined in-file with `gc.collect()` + `time.sleep(0.5)` for Windows file-handle cleanup
2. **Windows timeout handling**: Tests accept `PermissionError` as valid timeout on Windows (STDIO isolation file locking)
3. **Platform-specific commands**: `echo` on Unix, `cmd /c echo` on Windows
4. **Environment save/restore**: Tests that modify `os.environ` use `original_env = os.environ.copy()` with `try/finally` restore
5. **Mock patch target**: The reference test patches `"subprocess.Popen"` — in the ported test, this must become `"mcp_coder.utils.subprocess_runner.subprocess.Popen"` (matching the existing mock-based tests pattern)

## Verification

After creating the file, run:
1. `pylint` — no errors
2. `mypy` — no type errors
3. `pytest tests/utils/test_subprocess_runner_real.py -n auto` — all 26 tests pass

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md for context.

Create the file tests/utils/test_subprocess_runner_real.py by porting tests from
the p_tools reference project (tests/test_subprocess_runner.py).

This is a mechanical port — copy the source tests and apply these changes:
- Import from mcp_coder.utils.subprocess_runner (not mcp_tools_py)
- Rename classes with Real suffix
- Move test_is_python_command_detection into TestPythonCommandDetectionReal
- Include temp_dir fixture in the file (self-contained)
- Exclude: TestCommandResult, TestCommandOptions, TestConvenienceFunctions,
  standalone fixtures, test_execute_command_unexpected_error
- Keep all Windows-specific skip conditions and platform handling as-is

After creating the file, run pylint, mypy, and pytest to verify all checks pass.
Fix any issues. Commit when green.
```
