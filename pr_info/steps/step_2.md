# Step 2: Parser + Dispatch Wiring for `checkout-issue-branch`

> **Context**: See `pr_info/steps/summary.md` for full overview of issue #647.
> **Depends on**: Step 1 (handler function exists).

## Goal

Wire `checkout-issue-branch` into the CLI parser and dispatcher so it's callable as `mcp-coder gh-tool checkout-issue-branch <number>`.

## WHERE

- **Modify**: `src/mcp_coder/cli/parsers.py` — in `add_gh_tool_parsers()`
- **Modify**: `src/mcp_coder/cli/main.py` — in `_handle_gh_tool_command()` + imports
- **Modify**: `tests/cli/commands/test_gh_tool.py` — CLI integration tests

## WHAT

### Parser addition in `parsers.py` (`add_gh_tool_parsers()`):

```python
# gh-tool checkout-issue-branch command
checkout_branch_parser = gh_tool_subparsers.add_parser(
    "checkout-issue-branch",
    help="Checkout or create a branch linked to a GitHub issue",
    formatter_class=WideHelpFormatter,
    epilog="""Exit codes:
  0  Success - branch checked out
  1  Could not find or create branch
  2  Error (not a git repo, API failure)""",
)
checkout_branch_parser.add_argument(
    "issue_number", type=int, help="GitHub issue number"
)
checkout_branch_parser.add_argument(
    "--project-dir",
    type=str,
    default=None,
    help="Project directory: where source code lives. Default: current directory",
)
```

### Dispatch addition in `main.py` (`_handle_gh_tool_command()`):

```python
elif args.gh_tool_subcommand == "checkout-issue-branch":
    return execute_checkout_issue_branch(args)
```

### Import addition in `main.py`:

```python
from .commands.gh_tool import execute_get_base_branch, execute_checkout_issue_branch
```

### Update error message in `_handle_gh_tool_command()`:
Add `'checkout-issue-branch'` to the subcommand list in the error message.

## HOW

Follow the exact pattern of existing `get-base-branch` registration:
1. Subparser with `WideHelpFormatter` and exit code epilog
2. Positional arg + optional `--project-dir`
3. Dispatch via `elif` in `_handle_gh_tool_command()`

## TESTS

Add to `tests/cli/commands/test_gh_tool.py`:

### Test class `TestGhToolCheckoutIssueBranchIntegration`:

```python
class TestGhToolCheckoutIssueBranchIntegration:
    """Test gh-tool checkout-issue-branch CLI integration."""

    def test_checkout_issue_branch_command_exists(self):
        """checkout-issue-branch is registered under gh-tool."""
        parser = create_parser()
        args = parser.parse_args(["gh-tool", "checkout-issue-branch", "123"])
        assert args.command == "gh-tool"
        assert args.gh_tool_subcommand == "checkout-issue-branch"
        assert args.issue_number == 123

    def test_checkout_issue_branch_with_project_dir(self):
        """--project-dir is parsed."""
        parser = create_parser()
        args = parser.parse_args([
            "gh-tool", "checkout-issue-branch", "456",
            "--project-dir", "/my/project"
        ])
        assert args.issue_number == 456
        assert args.project_dir == "/my/project"

    def test_checkout_issue_branch_help_shows_exit_codes(self):
        """Epilog documents exit codes."""
        # Navigate to checkout-issue-branch parser and verify epilog
        ...
```

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_2.md.

Implement Step 2: Wire `checkout-issue-branch` into the CLI.

1. Add subparser in `add_gh_tool_parsers()` in `src/mcp_coder/cli/parsers.py`
2. Add dispatch + import in `src/mcp_coder/cli/main.py`
3. Add CLI integration tests in `tests/cli/commands/test_gh_tool.py`

Follow the existing pattern of `get-base-branch` registration.
Run pylint, pytest, and mypy after implementation.
```
