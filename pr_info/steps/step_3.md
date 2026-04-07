# Step 3: Wire `enable_crash_logging` into long-running CLI commands

> **Context**: See `pr_info/steps/summary.md` for full issue context (Issue #712).

## LLM Prompt

```
Implement step 3 of issue #712 (see pr_info/steps/summary.md for context).

Wire enable_crash_logging() into the three long-running commands: implement, create_plan,
and create_pr. Each command calls it immediately after log_command_startup(). Add tests
to verify the wiring. Run all three quality checks after implementation.
```

## WHERE

- **Modify**: `src/mcp_coder/cli/commands/implement.py`
- **Modify**: `src/mcp_coder/cli/commands/create_plan.py`
- **Modify**: `src/mcp_coder/cli/commands/create_pr.py`
- **Modify**: `tests/cli/commands/test_implement.py` (add wiring test)
- **Modify**: `tests/cli/commands/test_create_plan.py` (add wiring test)
- **Modify**: `tests/cli/commands/test_create_pr.py` (add wiring test)

## WHAT

In each command module, add one import and one call:

```python
from ...utils.crash_logging import enable_crash_logging
```

Then inside the execute function, immediately after `log_command_startup(...)`:

```python
enable_crash_logging(project_dir, "<command_name>")
```

Command names: `"implement"`, `"create-plan"`, `"create-pr"`.

## HOW

- Import at module top level (crash_logging is lightweight, no circular dependency risk)
- Call placement: right after `log_command_startup()`, before any other resolution logic
- Return value ignored — crash logging is fire-and-forget

## Tests

For each of the three commands, add one test that:
- Mocks `enable_crash_logging` at the command module level
- Calls the execute function with minimal valid args
- Asserts `enable_crash_logging` was called with `(project_dir, "<command_name>")`

**Important**: When mocking `enable_crash_logging`, patch the *importing module's* binding (e.g., `mcp_coder.cli.commands.implement.enable_crash_logging`), not `mcp_coder.utils.crash_logging.enable_crash_logging`, because the command modules use `from ... import enable_crash_logging`.

| Test file | Test name |
|-----------|-----------|
| `test_implement.py` | `test_enable_crash_logging_called` |
| `test_create_plan.py` | `test_enable_crash_logging_called` |
| `test_create_pr.py` | `test_enable_crash_logging_called` |

## DATA

No new data structures. `enable_crash_logging` return value is intentionally discarded.
