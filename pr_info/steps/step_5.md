# Step 5: Integration into execute_icoder() + manual test tool

## References
- [Summary](summary.md) for architecture overview
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
Add `except TuiPreflightAbort` **before** `except KeyboardInterrupt`:
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
```python
    except TuiPreflightAbort as e:    # ← NEW: before KeyboardInterrupt
        logger.log(OUTPUT, e.message)
        return e.exit_code
    except KeyboardInterrupt:          # existing
        ...
    except Exception as e:             # existing broad handler
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
Implement Step 5 of issue #780 (TUI pre-flight terminal checks).
See pr_info/steps/summary.md for architecture and pr_info/steps/step_5.md for this step's spec.

Modify src/mcp_coder/cli/commands/icoder.py:
- Import TuiChecker and TuiPreflightAbort from utils.tui_preparation
- Call TuiChecker().run_all_checks() between project dir resolution and setup_icoder_environment()
- Add except TuiPreflightAbort handler before except KeyboardInterrupt

Add integration tests to tests/icoder/test_cli_icoder.py.
Create tools/test_scroll.py as a minimal manual verification TUI app.
Run all code quality checks (pylint, pytest, mypy) and fix any issues.
```
