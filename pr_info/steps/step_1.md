# Step 1: Move `set-status` under `gh-tool` (parser + routing + help)

**References:** [summary.md](summary.md) — Part 3

## Goal

Move `mcp-coder set-status` to `mcp-coder gh-tool set-status`. Hard removal of old path.

## WHERE

- `src/mcp_coder/cli/parsers.py`
- `src/mcp_coder/cli/main.py`
- `src/mcp_coder/cli/commands/help.py`
- `src/mcp_coder/cli/commands/set_status.py`
- `tests/cli/commands/test_help.py`
- `tests/cli/test_main.py`

## WHAT

### parsers.py

- **Delete** `add_set_status_parser()` function entirely.
- **Modify** `add_gh_tool_parsers()` — add a `"set-status"` subparser inside `gh_tool_subparsers` with the same arguments (status_label, --issue, --project-dir, --force) and epilog.
- **Remove** `from .commands.set_status import build_set_status_epilog` from module-level import; move it into `add_gh_tool_parsers()` as a local import (since it's only needed there now).

### main.py

- **Remove** `from .commands.set_status import execute_set_status` import.
- **Remove** `add_set_status_parser` from parsers import list and from `create_parser()` call.
- **Remove** `elif args.command == "set-status":` routing block.
- **Add** in `_handle_gh_tool_command()`: `elif args.gh_tool_subcommand == "set-status": return execute_set_status(args)` with a local import of `execute_set_status`.
- **Update** the error message in `_handle_gh_tool_command()` to include `'set-status'` in the list.

### help.py

- **Replace** `Command("set-status", "Update GitHub issue workflow status label")` with `Command("gh-tool set-status", "Update GitHub issue workflow status label")`.

### set_status.py

- **Update** the 2 epilog example lines from `mcp-coder set-status` to `mcp-coder gh-tool set-status`.

## HOW

The set-status parser arguments and execute function are unchanged — only the parser registration location and routing change.

## ALGORITHM

```
# parsers.py — inside add_gh_tool_parsers():
set_status_parser = gh_tool_subparsers.add_parser("set-status", ...)
set_status_parser.add_argument("status_label", ...)
set_status_parser.add_argument("--issue", ...)
set_status_parser.add_argument("--project-dir", ...)
set_status_parser.add_argument("--force", ...)

# main.py — inside _handle_gh_tool_command():
elif args.gh_tool_subcommand == "set-status":
    from .commands.set_status import execute_set_status
    return execute_set_status(args)
```

## DATA

No data structure changes. `execute_set_status(args)` signature unchanged.

## Tests

### test_help.py

- Update `test_command_categories_contains_all_commands`: replace `"set-status"` with `"gh-tool set-status"` in expected list.

### test_main.py

- Existing set-status routing tests (if any via `sys.argv` patches) need updating to use `["mcp-coder", "gh-tool", "set-status", ...]`.
- Verify `mcp-coder set-status` now falls through to "unknown command" path.

## LLM Prompt

```
Please read pr_info/steps/summary.md and pr_info/steps/step_1.md.
Implement step 1: Move set-status under gh-tool.

Key changes:
1. parsers.py: Move set-status parser body into add_gh_tool_parsers(), delete add_set_status_parser()
2. main.py: Remove top-level set-status routing, add "set-status" case in _handle_gh_tool_command()
3. help.py: Rename "set-status" to "gh-tool set-status" in COMMAND_CATEGORIES
4. set_status.py: Update epilog examples
5. Update tests in test_help.py and test_main.py

Run all quality checks after changes. One commit for this step.
```
