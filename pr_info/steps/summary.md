# Summary: Add Real-Subprocess Integration Tests for subprocess_runner

**Issue:** #623
**Related:** #618, MarcusJellinghaus/mcp-tools-py#130

## Goal

Port real-subprocess integration tests from `p_tools` reference project (`tests/test_subprocess_runner.py`) into mcp_coder as a new file `tests/utils/test_subprocess_runner_real.py`.

These complement the existing mock-based tests in `tests/utils/test_subprocess_runner.py` — they do not replace them.

## Architectural / Design Changes

**Minimal.** One small production fix was included alongside the tests:

- `src/mcp_coder/utils/subprocess_runner.py`: Added early guard in `execute_subprocess()` for empty command lists — returns `CommandResult(return_code=1, execution_error="Command list must not be empty")` instead of allowing an unhandled `IndexError` from `subprocess.Popen`.

No new modules, classes, or public API changes. The existing `subprocess_runner.py` module is tested as-is (with the above fix).

## Approach

Mechanical port from `p_tools` reference with minimal adaptations:

1. **Import path**: `mcp_tools_py.utils.subprocess_runner` → `mcp_coder.utils.subprocess_runner`
2. **Class naming**: Append `Real` suffix to all ported classes
3. **Reorganization**: Move `test_is_python_command_detection` from `TestSTDIOIsolation` into `TestPythonCommandDetectionReal`
4. **Self-contained fixture**: `temp_dir` fixture defined in the new file (Windows file-handle cleanup)
5. **Exclusion**: `test_execute_command_unexpected_error` is excluded because mcp_coder's `execute_subprocess` does not catch generic `Exception` (only `FileNotFoundError`, `PermissionError`, `OSError`)

## Files

| Action | Path |
|--------|------|
| **CREATE** | `tests/utils/test_subprocess_runner_real.py` |
| **MODIFY** | `src/mcp_coder/utils/subprocess_runner.py` |

## What is NOT ported (per issue)

- `TestCommandResult` / `TestCommandOptions` — trivial dataclass assertions
- `TestConvenienceFunctions` — thin wrapper, tested implicitly
- Standalone fixture smoke tests (`test_sample_command_with_fixture`, etc.)

## Test Classes to Create

| New Class | Source Class | Tests |
|-----------|-------------|-------|
| `TestExecuteSubprocessReal` | `TestExecuteSubprocess` | 9 tests: simple command, options, error code, not-found, timeout, permission error, check option, input data, None command |
| `TestSTDIOIsolationReal` | `TestSTDIOIsolation` | 7 tests: isolation env, subprocess with isolation, subprocess with error, timeout, non-python, MCP var removal, env merging |
| `TestPythonCommandDetectionReal` | `TestPythonCommandDetection` + moved test | 3 tests: is_python_command positive/negative, isolation verification, env passthrough |
| `TestIntegrationScenariosReal` | `TestIntegrationScenarios` | 4 tests: concurrent, mixed commands, sequential, env isolation e2e |
| `TestErrorHandlingReal` | `TestErrorHandling` | 3 tests: empty command, execution time, env vars |

**Total: 26 tests in 1 new file, 1 commit.**
