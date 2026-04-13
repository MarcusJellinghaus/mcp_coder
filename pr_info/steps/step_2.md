# Step 2: Silent fix — Windows CMD codepage auto-fix

## References
- [Summary](summary.md) for architecture overview
- [Step 1](step_1.md) for the skeleton and warning checks this builds on
- Issue #780 for full requirements

## Goal
Add the Windows CMD codepage check: detect non-UTF-8 codepage, silently fix to 65001, register atexit restore.

## WHERE
- **Modify**: `src/mcp_coder/utils/tui_preparation.py`
- **Modify**: `tests/utils/test_tui_preparation.py`

## WHAT — New method on `TuiChecker`

### `_check_windows_cmd_codepage(self) -> None`
```python
def _check_windows_cmd_codepage(self) -> None: ...
```

## ALGORITHM
```
1. if sys.platform != "win32": return
2. import ctypes; current_cp = ctypes.windll.kernel32.GetConsoleOutputCP()
3. if current_cp == 65001: return  (already UTF-8)
4. define fix_fn that: calls SetConsoleOutputCP(65001), registers atexit to restore original cp
5. self._silent_fixes.append(("Console codepage set to UTF-8 (was {current_cp})", fix_fn))
```

## HOW — Integration
Add call in `run_all_checks()` (before the warning checks — silent fixes are collected first, presented first):
```python
self._check_windows_cmd_codepage()
```

## DATA
- `fix_fn` closure captures `current_cp` for atexit restore
- Log message: `"Console codepage set to UTF-8 (was {current_cp})"`

## Tests
All tests mock `ctypes.windll` so they run on any platform.

1. `test_check_cmd_codepage_non_utf8` — mock `sys.platform="win32"`, mock `GetConsoleOutputCP()` returning 437, verify `_silent_fixes` has one entry
2. `test_check_cmd_codepage_already_utf8` — mock returning 65001, verify `_silent_fixes` is empty
3. `test_check_cmd_codepage_wrong_platform` — mock `sys.platform="linux"`, verify `_silent_fixes` is empty
4. `test_check_cmd_codepage_fix_calls_set` — execute the fix_fn from `_silent_fixes`, verify `SetConsoleOutputCP(65001)` was called
5. `test_check_cmd_codepage_atexit_registered` — execute fix_fn, verify `atexit.register` was called with a restore function
6. `test_silent_fix_logged_via_run_all_checks` — trigger codepage fix, run `run_all_checks()`, verify `logger.log(OUTPUT, ...)` called with codepage message

### Mocking approach for ctypes.windll
```python
# Create mock windll module
mock_kernel32 = MagicMock()
mock_kernel32.GetConsoleOutputCP.return_value = 437
mock_kernel32.SetConsoleOutputCP.return_value = 1

mock_windll = MagicMock()
mock_windll.kernel32 = mock_kernel32

# Patch ctypes.windll (may not exist on non-Windows)
monkeypatch.setattr("ctypes.windll", mock_windll, raising=False)
```

## LLM Prompt
```
Implement Step 2 of issue #780 (TUI pre-flight terminal checks).
See pr_info/steps/summary.md for architecture and pr_info/steps/step_2.md for this step's spec.

Add _check_windows_cmd_codepage() to TuiChecker in src/mcp_coder/utils/tui_preparation.py.
It detects non-UTF-8 codepage via ctypes.windll.kernel32.GetConsoleOutputCP(),
auto-fixes with SetConsoleOutputCP(65001), and registers atexit to restore the original.
Wire into run_all_checks(). Add tests to tests/utils/test_tui_preparation.py.
Mock ctypes.windll so tests run on all platforms.
Run all code quality checks (pylint, pytest, mypy) and fix any issues.
```
