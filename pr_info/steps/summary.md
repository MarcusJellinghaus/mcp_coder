# Summary: CLI '--help' hint on argument errors (#624)

## Goal

When users pass unrecognized arguments, append a GNU-style help hint:

```
mcp-coder: error: unrecognized arguments: --resume-session
Try 'mcp-coder --help' for more information.
```

For subcommands, the hint auto-adapts (e.g., `Try 'mcp-coder prompt --help' ...`).

## Architectural / Design Changes

### New class: `HelpHintArgumentParser` (in `parsers.py`)

A minimal `argparse.ArgumentParser` subclass that overrides a single method — `error()` — to append the help hint before delegating to `super().error()`.

**Why a subclass instead of monkey-patching or wrapping?**
- argparse's `add_subparsers()` calls `kwargs.setdefault('parser_class', type(self))`, so all subparsers (and nested subparsers) automatically inherit the custom class. One change at the root parser cascades everywhere — zero changes needed in `parsers.py` parser-creation functions.
- This is the documented argparse extension point for custom error handling.

### Changes to manual error paths (in `main.py`)

The `_handle_*` functions print their own error messages for missing subcommands (these bypass argparse's `error()` method). Each gets a matching help hint line. The paired `logger.error()` calls are downgraded to `logger.debug()` since the user already sees the printed message.

### No changes to exit codes

- argparse errors: exit code **2** (preserved by `super().error()`)
- Manual error paths: exit code **1** (unchanged — these are user-level routing errors, not argument parse errors)

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/cli/parsers.py` | Add `HelpHintArgumentParser` class (~10 lines) |
| `src/mcp_coder/cli/main.py` | Use `HelpHintArgumentParser` in `create_parser()`, add help hints to manual error messages, downgrade `logger.error` → `logger.debug` |
| `tests/cli/test_main.py` | Add tests for help hint in argparse errors and manual error paths |
| `tests/cli/test_parsers.py` | Add unit tests for `HelpHintArgumentParser.error()` |

## Implementation Steps

- **Step 1**: `HelpHintArgumentParser` class + unit tests (`parsers.py`, `test_parsers.py`)
- **Step 2**: Wire it into `create_parser()` + update manual error paths + tests (`main.py`, `test_main.py`)
- **Step 3**: Remove dead "unknown subcommand" else branches from `main.py` + related tests
