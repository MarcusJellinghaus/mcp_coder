# Step 2: CLI Defaults — --log-level choices, _resolve_log_level(), _INFO_COMMANDS

## LLM Prompt
> Read `pr_info/steps/summary.md` for full context. Implement Step 2: Add OUTPUT to --log-level CLI choices, shrink _INFO_COMMANDS to just coordinator, update _resolve_log_level() to default to OUTPUT, update tests. Run all three code quality checks after changes.

## WHERE
- `src/mcp_coder/cli/main.py` — CLI argument changes
- `tests/cli/test_main.py` — update affected tests

## WHAT

### 2a. Add OUTPUT to `--log-level` choices (`main.py`)

```python
# BEFORE
choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
help="Set the logging level (default: NOTICE, or INFO for workflow commands)",

# AFTER
choices=["DEBUG", "INFO", "OUTPUT", "WARNING", "ERROR", "CRITICAL"],
help="Set the logging level (default: OUTPUT, or INFO for coordinator)",
```

### 2b. Shrink `_INFO_COMMANDS` (`main.py`)

```python
# BEFORE
_INFO_COMMANDS = frozenset({"create-plan", "implement", "create-pr", "coordinator"})

# AFTER
_INFO_COMMANDS = frozenset({"coordinator"})
```

### 2c. Update `_resolve_log_level()` (`main.py`)

```python
# BEFORE
def _resolve_log_level(args: argparse.Namespace) -> str:
    if args.log_level is not None:
        return str(args.log_level)
    if args.command in _INFO_COMMANDS:
        return "INFO"
    if (
        args.command == "vscodeclaude"
        and getattr(args, "vscodeclaude_subcommand", None) == "launch"
    ):
        return "INFO"
    return "NOTICE"

# AFTER
def _resolve_log_level(args: argparse.Namespace) -> str:
    """Resolve the effective log level based on command and explicit flag.

    Coordinator defaults to INFO (it sets --log-level INFO for sub-commands).
    All other commands default to OUTPUT for clean CLI output.
    An explicit --log-level always wins.

    Returns:
        The log level string to pass to setup_logging.
    """
    if args.log_level is not None:
        return str(args.log_level)
    if args.command in _INFO_COMMANDS:
        return "INFO"
    return "OUTPUT"
```

Key changes:
- Remove the `vscodeclaude launch` special case (follows OUTPUT default)
- Default return changes from `"NOTICE"` to `"OUTPUT"`
- Update docstring

### 2d. Update tests (`tests/cli/test_main.py`)

Update any tests that reference `NOTICE` in log level assertions or mock expectations to use `OUTPUT`. Specifically look for:
- Tests that assert the default log level is `"NOTICE"` → change to `"OUTPUT"`
- Tests for `_resolve_log_level` that check return values
- Tests that verify `_INFO_COMMANDS` membership
- Tests for `vscodeclaude launch` defaulting to `INFO` → now defaults to `OUTPUT`

## DATA
- `_INFO_COMMANDS`: `frozenset[str]` = `frozenset({"coordinator"})`
- `_resolve_log_level()` returns: `str` — one of the log level names

## HOW — Integration Points
- `_resolve_log_level()` is called in `main()` to determine the effective log level before `setup_logging()`
- The `choices` list in argparse ensures invalid level names are rejected at parse time
- `setup_logging()` (updated in Step 1) will use `CleanFormatter` when level is `"OUTPUT"`

## ALGORITHM
```
1. If explicit --log-level provided: use it
2. If command is "coordinator": return "INFO"
3. Otherwise: return "OUTPUT"
```

## Commit Message
```
feat(cli): default all commands to OUTPUT threshold

- Add OUTPUT to --log-level choices
- Shrink _INFO_COMMANDS to coordinator only
- Remove vscodeclaude launch INFO special case
- All commands now default to clean OUTPUT formatting
```
