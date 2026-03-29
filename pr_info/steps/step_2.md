# Step 2: Wire HelpHintArgumentParser into CLI + update manual error paths

## Context

See [summary.md](./summary.md) for overall design. Step 1 created the class. This step integrates it.

## LLM Prompt

> Implement Step 2 of issue #624 (CLI help hints). Read `pr_info/steps/summary.md` and this file for context.
> Wire `HelpHintArgumentParser` into `create_parser()` in `main.py`, add help hints to all manual error messages, downgrade `logger.error` → `logger.debug`, and update/add tests in `tests/cli/test_main.py`.
> Run all three code quality checks (pylint, mypy, pytest) and fix any issues. Commit when green.

## WHERE

- `src/mcp_coder/cli/main.py` — use new parser class, update error messages
- `tests/cli/test_main.py` — update existing tests, add new ones

## WHAT

### Changes in `main.py`

1. **Import**: Add `HelpHintArgumentParser` to the import from `.parsers`
2. **`create_parser()`**: Change `argparse.ArgumentParser(` → `HelpHintArgumentParser(`
3. **Manual error paths**: Add help hint print after each error print, downgrade logger

### Functions with manual error paths to update

| Function | Help hint text | Logger change |
|----------|---------------|---------------|
| `_handle_check_command` (no subcommand) | `Try 'mcp-coder check --help' for more information.` | `logger.error` → `logger.debug` |
| `_handle_gh_tool_command` (no subcommand) | `Try 'mcp-coder gh-tool --help' for more information.` | `logger.error` → `logger.debug` |
| `_handle_vscodeclaude_command` (no subcommand) | `Try 'mcp-coder vscodeclaude --help' for more information.` | `logger.error` → `logger.debug` |
| `_handle_git_tool_command` (no subcommand) | `Try 'mcp-coder git-tool --help' for more information.` | `logger.error` → `logger.debug` |
| `_handle_coordinator_command` (missing flags) | `Try 'mcp-coder coordinator --help' for more information.` | (no logger call exists) |

Note: The "unknown subcommand" branches and `_handle_commit_command` are dead code paths (argparse rejects unknown subcommands before these are reached). Do **not** add hints there — keep changes minimal.

### Test updates in `test_main.py`

```python
# UPDATE existing test:
def test_check_no_subcommand_shows_error  # change logger.error → logger.debug, add hint assertion

# ADD new tests:
def test_unrecognized_arg_shows_help_hint(self) -> None: ...
def test_subcommand_unrecognized_arg_shows_help_hint(self) -> None: ...
def test_gh_tool_no_subcommand_shows_help_hint(self) -> None: ...
def test_vscodeclaude_no_subcommand_shows_help_hint(self) -> None: ...
def test_git_tool_no_subcommand_shows_help_hint(self) -> None: ...
def test_coordinator_no_flags_shows_help_hint(self) -> None: ...
```

## HOW

- One-line change in `create_parser()` — subparsers auto-inherit via `parser_class=type(self)`
- Manual error paths: add `print("Try 'mcp-coder <cmd> --help' for more information.", file=sys.stderr)` after each existing error print
- Tests for argparse errors: use `capsys.readouterr().err` to check stderr contains hint
- Tests for manual errors: use `capsys` or mock `print` to verify hint is printed

## ALGORITHM (manual error path pattern)

```
# Before (example: _handle_check_command, no subcommand):
logger.error("Check subcommand required")
print("Error: Please specify a check subcommand ...")
return 1

# After:
logger.debug("Check subcommand required")
print("Error: Please specify a check subcommand ...")
print("Try 'mcp-coder check --help' for more information.", file=sys.stderr)
return 1
```

## DATA

No new data structures. Only string output changes.
