# Step 3: Wire Up main.py — Compact Output and Exit Code 0

> **Reference**: See `pr_info/steps/summary.md` for overall design.

## Goal

Update `handle_no_command()` in `main.py` to use `get_compact_help_text()` and return exit code `0`. Update tests in `test_main.py`.

## WHERE

- `src/mcp_coder/cli/main.py`
- `tests/cli/test_main.py`

## WHAT

### Changes to `main.py`

```python
# Change import:
# OLD: from .commands.help import execute_help, get_help_text
# NEW: from .commands.help import execute_help, get_compact_help_text

def handle_no_command(_args: argparse.Namespace) -> int:
    """Handle case when no command is provided.

    Returns:
        Exit code (0 — showing help is valid behavior).
    """
    logger.info("No command provided, showing help")
    help_text = get_compact_help_text()  # was: get_help_text(include_examples=False)
    print(help_text)
    return 0  # was: 1
```

## DATA

- `handle_no_command()` returns `int` — now `0` instead of `1`

## HOW (Integration)

- Import `get_compact_help_text` from `help.py` (replaces `get_help_text` import)
- `execute_help` import remains unchanged

## Tests to Update

In `tests/cli/test_main.py`:

1. **`test_handle_no_command_prints_help`** — change `assert result == 1` to `assert result == 0`
2. **`test_main_no_args_calls_handle_no_command`** — change `mock_handle_no_command.return_value = 1` to `0`, and `assert result == 1` to `assert result == 0`

## LLM Prompt

```
Implement Step 3 of issue #565 (see pr_info/steps/summary.md and pr_info/steps/step_3.md).

TDD approach:
1. Read the current test_main.py and main.py files
2. Update test assertions: handle_no_command returns 0, not 1
3. Update main.py: import get_compact_help_text, use it in handle_no_command(), return 0
4. Run all three code quality checks (pylint, pytest, mypy) and fix any issues
5. Commit when all checks pass
```
