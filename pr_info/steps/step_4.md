# Step 4: Move define-labels and issue-stats to gh-tool

## Context
See `pr_info/steps/summary.md` for full issue context.

## Goal
Add `define-labels` and `issue-stats` as subcommands under `gh-tool`. Remove top-level `define-labels` command. Route to existing execute functions.

## LLM Prompt
```
Implement Step 4 of issue #570 (CLI restructure). Read pr_info/steps/summary.md for context, then read pr_info/steps/step_4.md for detailed instructions. Move define-labels and issue-stats under gh-tool. Update tests first (TDD), then implementation. Run all code quality checks after changes.
```

## WHERE
- `src/mcp_coder/cli/parsers.py` — update `add_gh_tool_parsers()`, remove `add_define_labels_parser()`
- `src/mcp_coder/cli/main.py` — update `_handle_gh_tool_command()`, remove `define-labels` routing
- `tests/cli/commands/test_gh_tool.py` — add tests for new subcommands
- `tests/cli/commands/coordinator/test_issue_stats_cli.py` — update parser tests
- `tests/cli/test_main.py` — remove define-labels reference if any

## WHAT

### parsers.py — Update `add_gh_tool_parsers()`

Add two new subparsers to the existing `gh-tool` parser:

```python
def add_gh_tool_parsers(subparsers: Any) -> None:
    """Add gh-tool command parsers."""
    gh_tool_parser = subparsers.add_parser("gh-tool", help="GitHub tool commands")
    gh_tool_subparsers = gh_tool_parser.add_subparsers(
        dest="gh_tool_subcommand",
        help="Available GitHub tool commands",
        metavar="SUBCOMMAND",
    )

    # gh-tool get-base-branch (existing, unchanged)
    # ... existing code ...

    # gh-tool define-labels (moved from top-level)
    define_labels_parser = gh_tool_subparsers.add_parser(
        "define-labels",
        help="Sync workflow status labels to GitHub repository",
        formatter_class=WideHelpFormatter,
    )
    define_labels_parser.add_argument(
        "--project-dir", type=str, default=None,
        help="Project directory. Default: current directory",
    )
    define_labels_parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview changes without applying them",
    )

    # gh-tool issue-stats (moved from coordinator)
    issue_stats_parser = gh_tool_subparsers.add_parser(
        "issue-stats",
        help="Display issue statistics by workflow status",
        formatter_class=WideHelpFormatter,
    )
    issue_stats_parser.add_argument(
        "--filter", type=str.lower, choices=["all", "human", "bot"],
        default="all",
        help="Filter issues by category (default: all)",
    )
    issue_stats_parser.add_argument(
        "--details", action="store_true", default=False,
        help="Show individual issue details with links",
    )
    issue_stats_parser.add_argument(
        "--project-dir", metavar="PATH",
        help="Project directory. Default: current directory",
    )
```

### parsers.py — Remove `add_define_labels_parser()`

Delete the entire function. Remove its call from `create_parser()`.

### main.py — Update `_handle_gh_tool_command()`

```python
def _handle_gh_tool_command(args: argparse.Namespace) -> int:
    if hasattr(args, "gh_tool_subcommand") and args.gh_tool_subcommand:
        if args.gh_tool_subcommand == "get-base-branch":
            return execute_get_base_branch(args)
        elif args.gh_tool_subcommand == "define-labels":
            return execute_define_labels(args)
        elif args.gh_tool_subcommand == "issue-stats":
            return execute_coordinator_issue_stats(args)
        else:
            print(f"Error: Unknown gh-tool subcommand '{args.gh_tool_subcommand}'")
            return 1
    else:
        print("Error: Please specify a gh-tool subcommand (e.g., 'get-base-branch', 'define-labels', 'issue-stats')")
        return 1
```

### main.py — Remove top-level define-labels

Remove from routing:
```python
# DELETE this:
elif args.command == "define-labels":
    return execute_define_labels(args)
```

Remove from `create_parser()`:
```python
# DELETE this:
add_define_labels_parser(subparsers)
```

Keep the import of `execute_define_labels` (still used, just routed via gh-tool now).

## HOW
- `execute_define_labels` stays in `src/mcp_coder/cli/commands/define_labels.py` — no code movement
- `execute_coordinator_issue_stats` stays in `src/mcp_coder/cli/commands/coordinator/issue_stats.py` — no code movement
- Only parser definitions and routing change

## ALGORITHM
```
gh-tool subcommand routing:
  "get-base-branch" → execute_get_base_branch(args)
  "define-labels"   → execute_define_labels(args)
  "issue-stats"     → execute_coordinator_issue_stats(args)
  none              → print help, return 1
```

## TEST CHANGES

### tests/cli/commands/test_gh_tool.py

Add new test classes:

```python
class TestGhToolDefineLabelsIntegration:
    """Test gh-tool define-labels CLI integration."""

    def test_gh_tool_define_labels_command_exists(self) -> None:
        """define-labels is registered under gh-tool."""
        # parse ["gh-tool", "define-labels"]
        # assert args.gh_tool_subcommand == "define-labels"

    def test_gh_tool_define_labels_with_dry_run(self) -> None:
        """--dry-run flag is parsed."""
        # parse ["gh-tool", "define-labels", "--dry-run"]
        # assert args.dry_run is True

    def test_gh_tool_define_labels_with_project_dir(self) -> None:
        """--project-dir is parsed."""

class TestGhToolIssueStatsIntegration:
    """Test gh-tool issue-stats CLI integration."""

    def test_gh_tool_issue_stats_command_exists(self) -> None:
        """issue-stats is registered under gh-tool."""

    def test_gh_tool_issue_stats_default_values(self) -> None:
        """Default filter=all, details=False."""

    def test_gh_tool_issue_stats_with_filter(self) -> None:
        """--filter argument is parsed."""

    def test_gh_tool_issue_stats_with_details(self) -> None:
        """--details flag is parsed."""
```

### tests/cli/commands/coordinator/test_issue_stats_cli.py

**TestParseArguments** — update all tests:
- `test_default_values` → parse `["gh-tool", "issue-stats"]`, assert `args.gh_tool_subcommand == "issue-stats"`
- `test_filter_human` → parse `["gh-tool", "issue-stats", "--filter", "human"]`
- `test_filter_bot` → parse `["gh-tool", "issue-stats", "--filter", "bot"]`
- `test_filter_case_insensitive` → update parse args
- `test_details_flag` → update parse args
- `test_project_dir_argument` → update parse args
- `test_combined_arguments` → update parse args

Remove `args.command == "coordinator"` and `args.coordinator_subcommand == "issue-stats"` assertions.
Add `args.command == "gh-tool"` and `args.gh_tool_subcommand == "issue-stats"` assertions.

**TestExecuteCoordinatorIssueStats** — no changes (tests execute function directly)

## DATA
- `args.command == "gh-tool"`
- `args.gh_tool_subcommand: str` — "get-base-branch", "define-labels", or "issue-stats"
