# Step 2: Warning checks — SSH/dumb, locale, tmux/screen, macOS Terminal.app

## References
- [Summary](summary.md) for architecture overview
- [Step 1](step_1.md) for the skeleton this builds on
- Issue #780 for full requirements

## Goal
Add the four warning-type checks to `TuiChecker`. All print-and-continue (no pause, no prompt).

## WHERE
- **Modify**: `src/mcp_coder/utils/tui_preparation.py`
- **Modify**: `tests/utils/test_tui_preparation.py`

## WHAT — Four new methods on `TuiChecker`

### `_check_ssh_dumb_terminal(self) -> None`
- **Detection**: `os.environ.get("TERM")` is `"dumb"` or not set
- **Action**: append warning message to `self._warnings`
- **Message**: `"Terminal type is 'dumb' or unset — TUI may not render correctly. Fix: export TERM=xterm-256color"`

### `_check_non_utf8_locale(self) -> None`
- **Detection**: `os.environ.get("LANG", "") + os.environ.get("LC_ALL", "")` — if neither contains `"UTF-8"` (case-insensitive) and both are non-empty or at least one is set without UTF-8
- **Refinement**: skip if both LANG and LC_ALL are unset (Windows doesn't use these)
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

## ALGORITHM — each check
```
1. check platform gate (if applicable) → return if wrong platform
2. read env var(s)
3. if issue detected: self._warnings.append(message)
```

## HOW — Integration
Add calls in `run_all_checks()`:
```python
self._check_ssh_dumb_terminal()
self._check_non_utf8_locale()
self._check_tmux_screen()
self._check_macos_terminal_app()
```

## Tests
1. `test_check_ssh_dumb_terminal_detected` — set `TERM=dumb`, verify warning in `_warnings`
2. `test_check_ssh_dumb_terminal_unset` — unset `TERM`, verify warning
3. `test_check_ssh_dumb_terminal_ok` — set `TERM=xterm-256color`, verify no warning
4. `test_check_non_utf8_locale_detected` — set `LANG=C`, verify warning
5. `test_check_non_utf8_locale_ok` — set `LANG=en_US.UTF-8`, verify no warning
6. `test_check_non_utf8_locale_unset` — unset both `LANG` and `LC_ALL`, verify no warning (Windows case)
7. `test_check_tmux_detected` — set `TMUX=/tmp/tmux-1000/default,...`, verify warning
8. `test_check_screen_detected` — set `STY=12345.pts-0`, verify warning
9. `test_check_tmux_screen_not_detected` — unset both, verify no warning
10. `test_check_macos_terminal_app_detected` — mock `sys.platform="darwin"`, set `TERM_PROGRAM=Apple_Terminal`, verify warning
11. `test_check_macos_terminal_app_wrong_platform` — mock `sys.platform="win32"`, set `TERM_PROGRAM=Apple_Terminal`, verify no warning
12. `test_check_macos_terminal_app_different_terminal` — mock `sys.platform="darwin"`, set `TERM_PROGRAM=iTerm.app`, verify no warning
13. `test_warnings_logged_via_run_all_checks` — trigger one warning, run `run_all_checks()`, verify `logger.log(OUTPUT, ...)` called

Use `monkeypatch.setenv` / `monkeypatch.delenv` for env vars. Use `monkeypatch.setattr` for `sys.platform`.

## LLM Prompt
```
Implement Step 2 of issue #780 (TUI pre-flight terminal checks).
See pr_info/steps/summary.md for architecture and pr_info/steps/step_2.md for this step's spec.

Add four warning-type checks to TuiChecker in src/mcp_coder/utils/tui_preparation.py:
_check_ssh_dumb_terminal, _check_non_utf8_locale, _check_tmux_screen, _check_macos_terminal_app.
Wire them into run_all_checks(). Add tests to tests/utils/test_tui_preparation.py.
Run all code quality checks (pylint, pytest, mypy) and fix any issues.
```
