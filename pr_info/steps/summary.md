# Issue #565: Consolidate Help Output and Add Missing Commands

## Summary

Refactor the CLI help system from hardcoded inline strings to a **data-driven design** where all command metadata lives in a single `COMMAND_CATEGORIES` list. Both the compact output (`mcp-coder` with no args) and detailed output (`mcp-coder help`) render from this shared data source.

## Architectural / Design Changes

### Before
- `help.py` contains `get_help_text()` with a large f-string embedding command names, descriptions, and inline option details
- `get_usage_examples()` returns a separate hardcoded examples string
- `handle_no_command()` calls `get_help_text(include_examples=False)` and returns exit code `1`
- Many commands missing from help text entirely (`create-plan`, `implement`, `create-pr`, `coordinator *`, `set-status`, `check *`, `gh-tool *`, `git-tool *`)

### After
- `help.py` defines `Command` and `Category` as `NamedTuple` types
- A module-level `COMMAND_CATEGORIES` list holds all command metadata (4 categories, ~19 commands)
- `get_compact_help_text()` renders category headers + aligned commands (no category descriptions)
- `get_help_text()` renders category headers + category descriptions + aligned commands
- Column alignment is computed programmatically from the longest command name
- `handle_no_command()` uses `get_compact_help_text()` and returns exit code `0`
- `get_usage_examples()` is removed (dead code)

### Three Help Levels

| Invocation | Function | Detail |
|---|---|---|
| `mcp-coder` (no args) | `get_compact_help_text()` | Category headers + commands |
| `mcp-coder help` | `get_help_text()` | Adds category descriptions |
| `mcp-coder <cmd> --help` | argparse (unchanged) | Per-command options |

## Files Modified

| File | Change |
|---|---|
| `src/mcp_coder/cli/commands/help.py` | Add `Command`/`Category` NamedTuples, `COMMAND_CATEGORIES` data, `get_compact_help_text()`, rewrite `get_help_text()`, remove `get_usage_examples()` |
| `src/mcp_coder/cli/main.py` | Import `get_compact_help_text`, use it in `handle_no_command()`, return `0` |
| `tests/cli/commands/test_help.py` | Update tests for new output format, add tests for new functions, remove tests for deleted functions |
| `tests/cli/test_main.py` | Update expected exit code from `1` to `0` |

## No New Files Created

All changes are modifications to existing files.
