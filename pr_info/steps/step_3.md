# Step 3: Add vscodeclaude Top-Level Command

## Context
See `pr_info/steps/summary.md` for full issue context.

## Goal
Add `vscodeclaude` as a top-level command with `launch` and `status` subcommands. Route to existing execute functions. Remove vscodeclaude from coordinator parsers (already done in step 2's parser rewrite).

## LLM Prompt
```
Implement Step 3 of issue #570 (CLI restructure). Read pr_info/steps/summary.md for context, then read pr_info/steps/step_3.md for detailed instructions. Add vscodeclaude as a top-level CLI command. Update tests first (TDD), then implementation. Run all code quality checks after changes.
```

## WHERE
- `src/mcp_coder/cli/parsers.py` — add `add_vscodeclaude_parsers()`
- `src/mcp_coder/cli/main.py` — add `_handle_vscodeclaude_command()`, register in routing
- `tests/cli/commands/coordinator/test_vscodeclaude_cli.py` — update parser tests in TestCLI class
- `tests/cli/test_main.py` — add vscodeclaude routing tests (optional, if patterns exist)

## WHAT

### parsers.py — New `add_vscodeclaude_parsers()`

```python
def add_vscodeclaude_parsers(subparsers: Any) -> None:
    """Add vscodeclaude command parsers."""
    vscodeclaude_parser = subparsers.add_parser(
        "vscodeclaude",
        help="Manage VSCode/Claude sessions for interactive workflow stages",
    )
    vscodeclaude_subparsers = vscodeclaude_parser.add_subparsers(
        dest="vscodeclaude_subcommand",
        help="VSCodeClaude commands",
        metavar="SUBCOMMAND",
    )

    # vscodeclaude launch
    launch_parser = vscodeclaude_subparsers.add_parser(
        "launch",
        help="Launch VSCode/Claude sessions for issues needing review",
        formatter_class=WideHelpFormatter,
    )
    launch_parser.add_argument(
        "--repo", type=str, metavar="NAME",
        help="Filter to specific repository only",
    )
    launch_parser.add_argument(
        "--max-sessions", type=int, metavar="N",
        help="Override max concurrent sessions (default: from config or 3)",
    )
    launch_parser.add_argument(
        "--cleanup", action="store_true",
        help="Delete stale clean folders (without this flag, only lists them)",
    )
    launch_parser.add_argument(
        "--intervene", action="store_true",
        help="Force open a bot_busy issue for debugging",
    )
    launch_parser.add_argument(
        "--issue", type=int, metavar="NUMBER",
        help="Issue number for intervention mode (requires --intervene)",
    )

    # vscodeclaude status
    status_parser = vscodeclaude_subparsers.add_parser(
        "status",
        help="Show current VSCodeClaude sessions",
    )
    status_parser.add_argument(
        "--repo", type=str, metavar="NAME",
        help="Filter to specific repository only",
    )
```

### main.py — Add vscodeclaude routing

```python
def _handle_vscodeclaude_command(args: argparse.Namespace) -> int:
    if hasattr(args, "vscodeclaude_subcommand") and args.vscodeclaude_subcommand:
        if args.vscodeclaude_subcommand == "launch":
            return execute_coordinator_vscodeclaude(args)
        elif args.vscodeclaude_subcommand == "status":
            return execute_coordinator_vscodeclaude_status(args)
        else:
            print(f"Error: Unknown vscodeclaude subcommand '{args.vscodeclaude_subcommand}'")
            return 1
    else:
        # Bare "vscodeclaude" without subcommand — show help
        print("Error: Please specify a subcommand (e.g., 'launch', 'status')")
        return 1
```

Add to routing in `main()`:
```python
elif args.command == "vscodeclaude":
    return _handle_vscodeclaude_command(args)
```

Add import:
```python
from .commands.coordinator import (
    execute_coordinator_vscodeclaude,
    execute_coordinator_vscodeclaude_status,
)
```

Register parser in `create_parser()`:
```python
add_vscodeclaude_parsers(subparsers)
```

## HOW
- Import new `add_vscodeclaude_parsers` from parsers module
- Keep importing execute functions from coordinator module (no code movement)
- The existing `execute_coordinator_vscodeclaude()` and `execute_coordinator_vscodeclaude_status()` are called unchanged

## ALGORITHM (routing)
```
if subcommand == "launch": call execute_coordinator_vscodeclaude(args)
if subcommand == "status": call execute_coordinator_vscodeclaude_status(args)
if no subcommand: print help message, return 1
```

## TEST CHANGES

### tests/cli/commands/coordinator/test_vscodeclaude_cli.py

**TestCLI class** — update all parser tests:

- `test_vscodeclaude_parser_exists` → parse `["vscodeclaude", "launch"]`, assert `args.vscodeclaude_subcommand == "launch"`
- `test_vscodeclaude_repo_argument` → parse `["vscodeclaude", "launch", "--repo", "test"]`
- `test_vscodeclaude_max_sessions_argument` → parse `["vscodeclaude", "launch", "--max-sessions", "5"]`
- `test_vscodeclaude_cleanup_flag` → parse `["vscodeclaude", "launch", "--cleanup"]`
- `test_vscodeclaude_intervene_with_issue` → parse `["vscodeclaude", "launch", "--intervene", "--issue", "123"]`
- `test_vscodeclaude_status_subcommand` → parse `["vscodeclaude", "status"]`
- `test_vscodeclaude_status_with_repo` → parse `["vscodeclaude", "status", "--repo", "myrepo"]`

**TestCommandHandlers** — no changes needed (they test execute functions directly, not CLI parsing)

## DATA
- `args.command == "vscodeclaude"` (top-level)
- `args.vscodeclaude_subcommand: str` — "launch" or "status"
- All other args unchanged (--repo, --max-sessions, --cleanup, --intervene, --issue)
