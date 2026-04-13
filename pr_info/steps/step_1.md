# Step 1: TuiPreflightAbort exception + TuiChecker skeleton

## References
- [Summary](summary.md) for architecture overview
- Issue #780 for full requirements

## Goal
Create the module with the exception class and the `TuiChecker` class skeleton including the `run_all_checks()` orchestrator. No actual checks yet — just the framework that collects and presents issues in categorized order.

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
1. call each _check_* method (none yet — will be added in steps 2-4)
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
```

## DATA
- `_silent_fixes`: `list[tuple[str, Callable[[], None]]]` — log message + side-effect function
- `_warnings`: `list[str]` — plain messages
- `_prompts`: `list[tuple[str, str]]` — prompt text + instruction text
- Logging: `logger.log(OUTPUT, ...)` from `mcp_coder.utils.log_utils`

## Tests (`tests/utils/test_tui_preparation.py`)
1. `test_tui_preflight_abort_attributes` — exception carries message + exit_code
2. `test_tui_preflight_abort_default_exit_code` — defaults to 1
3. `test_run_all_checks_empty` — no checks registered, no error
4. `test_presentation_order` — manually append to all 3 lists, verify silent fixes run before warnings before prompts (use side-effect tracking)
5. `test_present_prompt_instructions_raises` — mock `input()` returning "i", verify `TuiPreflightAbort` raised
6. `test_present_prompt_abort_raises` — mock `input()` returning "a", verify `TuiPreflightAbort` raised
7. `test_present_prompt_default_aborts` — mock `input()` returning "x" (invalid), verify `TuiPreflightAbort` raised

## LLM Prompt
```
Implement Step 1 of issue #780 (TUI pre-flight terminal checks).
See pr_info/steps/summary.md for architecture and pr_info/steps/step_1.md for this step's spec.

Create src/mcp_coder/utils/tui_preparation.py with:
- TuiPreflightAbort exception (message + exit_code)
- TuiChecker class with run_all_checks() orchestrator and _present_prompt() method
- No actual terminal checks yet — just the skeleton

Create tests/utils/test_tui_preparation.py with TDD tests as specified in step_1.md.
Use logger.log(OUTPUT, ...) for all user-facing messages. Use plain input() for prompts.
Run all code quality checks (pylint, pytest, mypy) and fix any issues.
```
