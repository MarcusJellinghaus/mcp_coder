# Step 2: Flatten Coordinator Command

## Context
See `pr_info/steps/summary.md` for full issue context.

## Goal
Convert `coordinator` from a subcommand group (test/run/vscodeclaude/issue-stats) to a direct command with `--dry-run` flag. After this step, `coordinator` runs the dispatch workflow and `coordinator --dry-run` triggers a Jenkins test.

## LLM Prompt
```
Implement Step 2 of issue #570 (CLI restructure). Read pr_info/steps/summary.md for context, then read pr_info/steps/step_2.md for detailed instructions. Flatten the coordinator command. Update tests first (TDD), then implementation. Run all code quality checks after changes.
```

## WHERE
- `src/mcp_coder/cli/parsers.py` — rewrite `add_coordinator_parsers()`
- `src/mcp_coder/cli/main.py` — rewrite `_handle_coordinator_command()`, update imports
- `tests/cli/test_main.py` — update `TestCoordinatorCommand`, `TestCoordinatorRunCommand`
- `tests/cli/commands/coordinator/test_commands.py` — update `TestExecuteCoordinatorRun`

## WHAT

### parsers.py — `add_coordinator_parsers()`

Replace the current subparsers-based coordinator with a flat command:

```python
def add_coordinator_parsers(subparsers: Any) -> None:
    """Add coordinator command parser (direct command, no subcommands)."""
    coordinator_parser = subparsers.add_parser(
        "coordinator",
        help="Monitor and dispatch workflows for GitHub issues",
        formatter_class=WideHelpFormatter,
    )

    # --dry-run mode (replaces old "coordinator test")
    coordinator_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Trigger Jenkins test instead of dispatching workflows",
    )

    # Run mode args (--all or --repo, mutually exclusive)
    run_group = coordinator_parser.add_mutually_exclusive_group()
    run_group.add_argument(
        "--all", action="store_true", help="Process all repositories from config"
    )
    run_group.add_argument(
        "--repo", type=str, metavar="NAME",
        help="Process single repository (e.g., mcp_coder)",
    )

    coordinator_parser.add_argument(
        "--force-refresh", action="store_true",
        help="Force full cache refresh, bypass all caching",
    )

    # Dry-run specific args (for Jenkins test trigger)
    coordinator_parser.add_argument(
        "--branch-name", type=str,
        help="Git branch to test (required with --dry-run)",
    )
    coordinator_parser.add_argument(
        "--log-level-coordinator", type=str.upper,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="DEBUG",
        help="Log level for mcp-coder commands in test script (default: DEBUG)",
        metavar="LEVEL",
        dest="coordinator_log_level",
    )
```

**Note**: `--all`/`--repo` group is NOT required anymore (was required for `run`). In `--dry-run` mode, `--repo` is required (validated in handler). In normal mode, `--all` or `--repo` is required (validated in handler).

### main.py — Update coordinator routing

```python
def _handle_coordinator_command(args: argparse.Namespace) -> int:
    if args.dry_run:
        # Validate dry-run args
        if not args.repo:
            print("Error: --dry-run requires --repo NAME", file=sys.stderr)
            return 1
        if not args.branch_name:
            print("Error: --dry-run requires --branch-name BRANCH", file=sys.stderr)
            return 1
        # Map args to what execute_coordinator_test expects
        args.repo_name = args.repo
        args.log_level = args.coordinator_log_level
        return execute_coordinator_test(args)
    else:
        # Validate run args
        if not args.all and not args.repo:
            print("Error: Either --all or --repo must be specified", file=sys.stderr)
            return 1
        return execute_coordinator_run(args)
```

Remove old imports for vscodeclaude and issue-stats from coordinator (those move in steps 3-4).

### main.py — Remove coordinator subcommand routing

The old `_handle_coordinator_command` checked `args.coordinator_subcommand`. The new version checks `args.dry_run` directly.

## HOW

1. Remove `coordinator_subcommand` attribute usage entirely
2. In `main.py`, the `coordinator` case calls `_handle_coordinator_command(args)` directly (no change to the top-level dispatch)
3. `execute_coordinator_test` and `execute_coordinator_run` stay in `coordinator/commands.py` — no changes to business logic

## ALGORITHM (main.py routing)
```
if args.dry_run:
    validate --repo and --branch-name present
    set args.repo_name = args.repo  # bridge to existing function signature
    set args.log_level = args.coordinator_log_level
    return execute_coordinator_test(args)
else:
    validate --all or --repo present
    return execute_coordinator_run(args)
```

**Note:** The `args.log_level = args.coordinator_log_level` assignment only happens in the dry-run branch. The normal (run) branch uses the global `args.log_level` set by the top-level `--log-level` flag, preserving current behavior.

## TEST CHANGES

### tests/cli/test_main.py

**TestCoordinatorCommand** — update all tests:
- `test_coordinator_test_command_parsing` → `test_coordinator_dry_run_parsing`: parse `["coordinator", "--dry-run", "--repo", "mcp_coder", "--branch-name", "feature-x"]`
- `test_coordinator_test_requires_branch_name` → removed (validation now in handler, not parser)
- `test_coordinator_test_executes_handler` → `test_coordinator_dry_run_executes_handler`: use new arg format
- `test_coordinator_test_with_log_level` → update arg format
- `test_coordinator_no_subcommand_shows_error` → remove (bare `coordinator` without --all/--repo now validated in handler)

**TestCoordinatorRunCommand** — update tests:
- `test_coordinator_run_with_repo_argument` → parse `["coordinator", "--repo", "mcp_coder"]` (no `run` subcommand)
- `test_coordinator_run_with_all_argument` → parse `["coordinator", "--all"]`
- `test_coordinator_run_with_log_level` → update arg format
- `test_coordinator_run_requires_all_or_repo` → remove (validation now in handler, not parser)
- `test_coordinator_run_all_and_repo_mutually_exclusive` → keep, update parse args

### tests/cli/commands/coordinator/test_commands.py

**TestExecuteCoordinatorRun** — update mock args:
- Remove `coordinator_subcommand="run"` from Namespace
- Tests for `execute_coordinator_test` and `execute_coordinator_run` functions don't change (they test the execute functions directly, not CLI parsing)

## DATA
- `args.dry_run: bool` — new flag
- `args.coordinator_log_level: str` — renamed from `args.log_level` (coordinator test subcommand) to avoid collision with global `--log-level`
- `args.branch_name: str | None` — optional, required only with `--dry-run`
