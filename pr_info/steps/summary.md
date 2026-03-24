# Summary: `mcp-coder init` CLI Command (#554)

## Goal

Add a `mcp-coder init` subcommand that creates a default `config.toml` file, giving users a one-command way to bootstrap their configuration.

## Architectural / Design Changes

**No new patterns or architectural changes.** This feature reuses:

- The existing `create_default_config()` and `get_config_file_path()` from `utils/user_config.py` — zero new business logic needed
- The inline parser registration pattern already used by `help` (no-argument command → no dedicated parser function needed)
- The standard `execute_<command>(args) -> int` convention for CLI command handlers

The only structural addition is a new command module file and its test file, wired into the existing CLI routing.

## Files to Create

| File | Purpose |
|------|---------|
| `src/mcp_coder/cli/commands/init.py` | `execute_init(args)` — CLI handler wrapping `create_default_config()` |
| `tests/cli/commands/test_init.py` | 4 test cases covering success, exists, failure, and template content |

## Files to Modify

| File | Change |
|------|--------|
| `src/mcp_coder/cli/main.py` | Import `execute_init`, add inline parser registration, add routing `elif` |
| `src/mcp_coder/cli/commands/__init__.py` | Add `execute_init` to exports |
| `src/mcp_coder/cli/commands/help.py` | Add `init` line to COMMANDS section in help text |
| `tests/cli/commands/test_help.py` | Add assertion for `init` in help text |

## Files NOT Modified (Simplification)

| File | Reason |
|------|--------|
| `src/mcp_coder/cli/parsers.py` | `init` takes zero arguments — follows `help` inline pattern instead of a dedicated parser function |
| `src/mcp_coder/utils/user_config.py` | All needed functions already exist |

## Implementation Steps

- **Step 1**: Create `init.py` command module with tests (TDD), wire into CLI, and add to help text

## Expected CLI Behavior

```
$ mcp-coder init
Created default config at: C:\Users\user\.mcp_coder\config.toml
Please update it with your actual credentials and settings.

Next steps:
  mcp-coder verify          Check your setup
  mcp-coder define-labels   Sync workflow labels to your GitHub repo

$ mcp-coder init
Config already exists: C:\Users\user\.mcp_coder\config.toml

$ mcp-coder init  # (on write failure)
Error: Failed to write config to C:\Users\user\.mcp_coder\config.toml: [Permission denied]
```
