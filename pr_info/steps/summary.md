# TUI Pre-flight Terminal Checks (tui_preparation) — Issue #780

## Overview

Add a `tui_preparation` utility that runs pre-flight terminal checks before launching any TUI app (iCoder). Detects terminal-specific issues (broken mouse capture, missing Unicode, etc.) and either auto-fixes them silently, warns, or prompts the user to abort.

## Architecture / Design Changes

### New module: `src/mcp_coder/utils/tui_preparation.py`

Single new file containing everything — no new packages, no new dependencies.

**`TuiPreflightAbort`** — Exception with `message: str` and `exit_code: int`. Raised when the TUI cannot launch. Co-located in `tui_preparation.py` (only consumer is `execute_icoder`).

**`TuiChecker`** — Class with per-terminal `_check_*()` methods. Each check self-gates on platform. The class holds three internal lists:

```
_silent_fixes: list[tuple[str, Callable[[], None]]]   # (log_msg, fix_fn)
_warnings: list[str]                                   # just messages
_prompts: list[tuple[str, str]]                        # (prompt_text, instruction_text)
```

**`run_all_checks()`** orchestrator:
1. Calls all `_check_*` methods (each appends to the appropriate list)
2. Applies silent fixes (call fix_fn, log one-liner via `logger.log(OUTPUT, ...)`)
3. Prints warnings (log and continue)
4. Presents prompts sequentially (plain `input()`, both choices abort → raises `TuiPreflightAbort`)

### Modified: `src/mcp_coder/cli/commands/icoder.py`

- Import `TuiChecker` and `TuiPreflightAbort`
- Call `TuiChecker().run_all_checks()` between directory resolution (line ~52) and `setup_icoder_environment()` (line ~54)
- Add `except TuiPreflightAbort` handler **before** `except Exception` (the broad handler). This is the critical constraint since `TuiPreflightAbort` inherits from `Exception`. Placement relative to `KeyboardInterrupt` is stylistic only.

### Seven checks

| # | Check | Platform gate | Category |
|---|-------|---------------|----------|
| 1 | Windows CMD codepage (`GetConsoleOutputCP() != 65001`) | `win32` | Silent fix |
| 2 | VS Code gpuAcceleration off (regex in settings.json) | `win32` + no `SSH_CONNECTION` | Prompt |
| 3 | macOS Terminal.app (limited mouse) | `darwin` | Warning |
| 4 | SSH/dumb terminal (`TERM=dumb` or unset) | all | Warning |
| 5 | Non-UTF-8 locale (`LANG`/`LC_ALL`) | all | Warning |
| 6 | tmux/screen mouse forwarding | all | Warning |
| 7 | Windows Terminal (`WT_SESSION`) | `win32` | (no-op, future-proofing) |

### Design constraints (from issue)

- No Textual imports in `tui_preparation.py`
- Plain `input()` for prompts (TUI may be broken)
- Both prompt choices (Instructions/Abort) result in abort
- `logger.log(OUTPUT, ...)` for all user-facing messages
- CMD codepage restore via `atexit`
- VS Code: regex search on raw settings.json (no JSON/JSONC parsing)
- VS Code: skip when `SSH_CONNECTION` is set
- VS Code: stable only (`%APPDATA%\Code\User\settings.json`), no Insiders

## Files Created / Modified

| Action | Path |
|--------|------|
| **Create** | `src/mcp_coder/utils/tui_preparation.py` |
| **Create** | `tests/utils/test_tui_preparation.py` |
| **Modify** | `src/mcp_coder/cli/commands/icoder.py` |
| **Create** | `tools/test_scroll.py` |

## Implementation Steps

- [Step 1](step_1.md) — `TuiPreflightAbort` + `TuiChecker` skeleton + warning checks (SSH/dumb, locale, tmux/screen, macOS Terminal.app, Windows Terminal stub)
- [Step 2](step_2.md) — Silent fix: Windows CMD codepage auto-fix with atexit restore
- [Step 3](step_3.md) — Prompted check: VS Code gpuAcceleration detection + prompt flow
- [Step 4](step_4.md) — Integration into `execute_icoder()` + `tools/test_scroll.py`
