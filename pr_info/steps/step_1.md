# Step 1: TuiPreflightAbort + TuiChecker skeleton + warning checks

## References
- [Summary](summary.md) for architecture overview
- Issue #780 for full requirements

## Goal
Create the module with the exception class, the `TuiChecker` class skeleton including the `run_all_checks()` orchestrator, all four warning-type checks, and the Windows Terminal no-op stub.

## WHERE
- **Create**: `src/mcp_coder/utils/tui_preparation.py`
- **Create**: `tests/utils/test_tui_preparation.py`

## WHAT

### `TuiPreflightAbort(Exception)`
```python
class TuiPreflightAbort(Exception):
    def __init__(self, message: str, exit_code: int = 1) -> None:
        ...
        self.message = message
        self.exit_code = exit_code
```

### `TuiChecker`
```python
class TuiChecker:
    def __init__(self) -> None:
        self._silent_fixes: list[tuple[str, Callable[[], None]]] = []
        self._warnings: list[str] = []
        self._prompts: list[tuple[str, str]] = []   # (prompt_text, instruction_text)

    def run_all_checks(self) -> None: ...
    def _present_prompt(self, prompt_text: str, instruction_text: str) -> None: ...
```

## ALGORITHM — `run_all_checks()`
```
1. call each _check_* method:
   - _check_ssh_dumb_terminal()
   - _check_non_utf8_locale()
   - _check_tmux_screen()
   - _check_macos_terminal_app()
   - _check_windows_terminal()
2. for each (msg, fix_fn) in _silent_fixes: call fix_fn(), log msg
3. for each msg in _warnings: log msg
4. for each (prompt_text, instruction_text) in _prompts: call _present_prompt()
```

## ALGORITHM — `_present_prompt()`
```
1. log prompt_text
2. read choice = input("(I)nstructions or (A)bort: ").strip().lower()
3. if choice starts with "i": log instruction_text, input("Press Enter to exit..."), raise TuiPreflightAbort
4. else: raise TuiPreflightAbort
Note: catch EOFError from input() and treat as abort (raise TuiPreflightAbort)
```

## DATA
- `_silent_fixes`: `list[tuple[str, Callable[[], None]]]` — log message + side-effect function
- `_warnings`: `list[str]` — plain messages
- `_prompts`: `list[tuple[str, str]]` — prompt text + instruction text
- Logging: `logger.log(OUTPUT, ...)` from `mcp_coder.utils.log_utils`

## WHAT — Four warning checks + Windows Terminal stub

### `_check_ssh_dumb_terminal(self) -> None`
- **Detection**: `os.environ.get("TERM")` is `"dumb"` or not set
- **Action**: append warning message to `self._warnings`
- **Message**: `"Terminal type is 'dumb' or unset — TUI may not render correctly. Fix: export TERM=xterm-256color"`

### `_check_non_utf8_locale(self) -> None`
- **Detection**: If neither `LANG` nor `LC_ALL` is set, skip (no warning). Otherwise, if no set variable contains 'UTF-8' (case-insensitive), warn.
- **Action**: append warning to `self._warnings`
- **Message**: `"System locale is not UTF-8 — Unicode rendering may break. Fix: export LANG=en_US.UTF-8"`

### `_check_tmux_screen(self) -> None`
- **Detection**: `os.environ.get("TMUX")` or `os.environ.get("STY")` is set
- **Action**: append warning to `self._warnings`
- **Message**: `"Running inside tmux/screen — mouse forwarding may be disabled. Fix: set -g mouse on (tmux)"`

### `_check_macos_terminal_app(self) -> None`
- **Platform gate**: `sys.platform != "darwin"` → return
- **Detection**: `os.environ.get("TERM_PROGRAM") == "Apple_Terminal"`
- **Action**: append warning to `self._warnings`
- **Message**: `"macOS Terminal.app has limited mouse reporting — consider iTerm2 or Kitty for full TUI support."`

### `_check_windows_terminal(self) -> None`
- **Platform gate**: `sys.platform != "win32"` → return immediately
- **Action**: no-op stub (future-proofing). Returns immediately without appending any warnings, fixes, or prompts.

## ALGORITHM — each check
```
1. check platform gate (if applicable) → return if wrong platform
2. read env var(s)
3. if issue detected: self._warnings.append(message)
```

## Tests (`tests/utils/test_tui_preparation.py`)

### Skeleton tests
1. `test_tui_preflight_abort_attributes` — exception carries message + exit_code
2. `test_tui_preflight_abort_default_exit_code` — defaults to 1
3. `test_run_all_checks_empty` — no checks registered, no error
4. `test_presentation_order` — manually append to all 3 lists, verify silent fixes run before warnings before prompts (use side-effect tracking)
5. `test_present_prompt_instructions_raises` — mock `input()` returning "i", verify `TuiPreflightAbort` raised
6. `test_present_prompt_abort_raises` — mock `input()` returning "a", verify `TuiPreflightAbort` raised
7. `test_present_prompt_default_aborts` — mock `input()` returning "x" (invalid), verify `TuiPreflightAbort` raised
8. `test_present_prompt_eof_aborts` — mock `input()` raising `EOFError`, verify `TuiPreflightAbort` raised

### Warning check tests
9. `test_check_ssh_dumb_terminal_detected` — set `TERM=dumb`, verify warning in `_warnings`
10. `test_check_ssh_dumb_terminal_unset` — unset `TERM`, verify warning
11. `test_check_ssh_dumb_terminal_ok` — set `TERM=xterm-256color`, verify no warning
12. `test_check_non_utf8_locale_detected` — set `LANG=C`, verify warning
13. `test_check_non_utf8_locale_ok` — set `LANG=en_US.UTF-8`, verify no warning
14. `test_check_non_utf8_locale_unset` — unset both `LANG` and `LC_ALL`, verify no warning (Windows case)
15. `test_check_non_utf8_locale_lc_all_overrides` — set `LANG=C`, `LC_ALL=en_US.UTF-8`, verify no warning
16. `test_check_tmux_detected` — set `TMUX=/tmp/tmux-1000/default,...`, verify warning
17. `test_check_screen_detected` — set `STY=12345.pts-0`, verify warning
18. `test_check_tmux_screen_not_detected` — unset both, verify no warning
19. `test_check_macos_terminal_app_detected` — mock `sys.platform="darwin"`, set `TERM_PROGRAM=Apple_Terminal`, verify warning
20. `test_check_macos_terminal_app_wrong_platform` — mock `sys.platform="win32"`, set `TERM_PROGRAM=Apple_Terminal`, verify no warning
21. `test_check_macos_terminal_app_different_terminal` — mock `sys.platform="darwin"`, set `TERM_PROGRAM=iTerm.app`, verify no warning
22. `test_warnings_logged_via_run_all_checks` — trigger one warning, run `run_all_checks()`, verify `logger.log(OUTPUT, ...)` called

### Windows Terminal stub test
23. `test_check_windows_terminal_noop` — mock `sys.platform="win32"`, call `_check_windows_terminal()`, verify no warnings, no fixes, no prompts produced

Use `monkeypatch.setenv` / `monkeypatch.delenv` for env vars. Use `monkeypatch.setattr` for `sys.platform`.

## LLM Prompt
```
Implement Step 1 of issue #780 (TUI pre-flight terminal checks).
See pr_info/steps/summary.md for architecture and pr_info/steps/step_1.md for this step's spec.

Create src/mcp_coder/utils/tui_preparation.py with:
- TuiPreflightAbort exception (message + exit_code)
- TuiChecker class with run_all_checks() orchestrator and _present_prompt() method
- _present_prompt() must catch EOFError from input() and treat as abort (raise TuiPreflightAbort)
- Four warning-type checks: _check_ssh_dumb_terminal, _check_non_utf8_locale, _check_tmux_screen, _check_macos_terminal_app
- Windows Terminal no-op stub: _check_windows_terminal() — platform-gated (win32), returns immediately
- Wire all checks into run_all_checks()

Create tests/utils/test_tui_preparation.py with TDD tests as specified in step_1.md.
Use logger.log(OUTPUT, ...) for all user-facing messages. Use plain input() for prompts.
Run all code quality checks (pylint, pytest, mypy) and fix any issues.
```
