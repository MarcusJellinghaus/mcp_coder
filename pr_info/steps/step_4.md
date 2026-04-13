# Step 4: Integration into execute_icoder() + manual test tool

## References
- [Summary](summary.md) for architecture overview
- [Step 1](step_1.md) for the skeleton and warning checks
- [Step 2](step_2.md) for the silent fix (CMD codepage)
- [Step 3](step_3.md) for the prompted check (VS Code gpuAcceleration)
- Issue #780 for full requirements

## Goal
Wire `TuiChecker.run_all_checks()` into `execute_icoder()` at the correct integration point. Add the `except TuiPreflightAbort` handler. Create `tools/test_scroll.py` for manual TUI verification.

## WHERE
- **Modify**: `src/mcp_coder/cli/commands/icoder.py`
- **Modify**: `tests/icoder/test_cli_icoder.py`
- **Create**: `tools/test_scroll.py`

## WHAT — Changes to `execute_icoder()`

### Import additions
```python
from ...utils.tui_preparation import TuiChecker, TuiPreflightAbort
```

### Integration point
Insert between project directory resolution (line ~52) and `setup_icoder_environment()` (line ~54):
```python
        # Pre-flight terminal checks (fail fast before slow env setup)
        TuiChecker().run_all_checks()
```

### Exception handler
Add `except TuiPreflightAbort` **before** `except Exception` (the broad handler). This is the critical constraint — `TuiPreflightAbort` inherits from `Exception`, so it must be caught first to avoid being swallowed by the broad handler. The placement relative to `except KeyboardInterrupt` is just stylistic since `KeyboardInterrupt` does not inherit from `Exception`:
```python
    except TuiPreflightAbort as e:
        logger.log(OUTPUT, e.message)
        return e.exit_code
```

## ALGORITHM — execute_icoder() flow change
```
1. resolve execution_dir
2. resolve project_dir
3. TuiChecker().run_all_checks()    ← NEW (fail fast)
4. setup_icoder_environment(...)     (existing)
5. ... rest of function ...
```

## HOW — Exception ordering in try/except
The critical constraint is that `except TuiPreflightAbort` must appear **before** `except Exception` (the broad handler), because `TuiPreflightAbort` inherits from `Exception` and would otherwise be caught by the broad handler. The ordering relative to `KeyboardInterrupt` is a stylistic choice only, since `KeyboardInterrupt` inherits from `BaseException`, not `Exception`.
```python
    except TuiPreflightAbort as e:    # ← NEW: must be before except Exception
        logger.log(OUTPUT, e.message)
        return e.exit_code
    except KeyboardInterrupt:          # existing (ordering vs above is stylistic)
        ...
    except Exception as e:             # existing broad handler — must be AFTER TuiPreflightAbort
        ...
```

## Tests — `tests/icoder/test_cli_icoder.py`

1. `test_execute_icoder_tui_preflight_abort` — mock `TuiChecker.run_all_checks` to raise `TuiPreflightAbort("broken", 1)`, verify `execute_icoder()` returns 1 (no traceback, no error log)
2. `test_execute_icoder_tui_preflight_passes` — mock `TuiChecker.run_all_checks` to do nothing, verify normal flow continues (existing `setup_icoder_environment` mock gets called)

## `tools/test_scroll.py` — Manual verification tool

Minimal Textual app with a RichLog widget for manual testing of scroll/mouse/rendering:
```python
"""Minimal TUI for manual terminal verification (issue #780)."""
from textual.app import App, ComposeResult
from textual.widgets import RichLog

class TestScrollApp(App):
    def compose(self) -> ComposeResult:
        yield RichLog()

    def on_mount(self) -> None:
        log = self.query_one(RichLog)
        for i in range(100):
            log.write(f"Line {i}: scroll test — mouse and rendering check")

if __name__ == "__main__":
    TestScrollApp().run()
```

## LLM Prompt
```
Implement Step 4 of issue #780 (TUI pre-flight terminal checks).
See pr_info/steps/summary.md for architecture and pr_info/steps/step_4.md for this step's spec.

Modify src/mcp_coder/cli/commands/icoder.py:
- Import TuiChecker and TuiPreflightAbort from utils.tui_preparation
- Call TuiChecker().run_all_checks() between project dir resolution and setup_icoder_environment()
- Add except TuiPreflightAbort handler BEFORE except Exception (the broad handler)
  The critical constraint is that TuiPreflightAbort inherits from Exception, so it must be caught first.
  Placement relative to KeyboardInterrupt is just stylistic (KeyboardInterrupt doesn't inherit from Exception).

Add integration tests to tests/icoder/test_cli_icoder.py.
Create tools/test_scroll.py as a minimal manual verification TUI app.
Run all code quality checks (pylint, pytest, mypy) and fix any issues.
```
