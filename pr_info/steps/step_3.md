# Step 3: Remove dead "unknown subcommand" branches

## Context

See [summary.md](./summary.md) for overall design. This step removes unreachable code paths discovered during plan review.

## LLM Prompt

> Implement Step 3 of issue #624. Read `pr_info/steps/summary.md` and this file for context.
> Remove dead "unknown subcommand" else branches from `main.py` and any related unit tests.
> Run all three code quality checks (pylint, mypy, pytest) and fix any issues. Commit when green.

## IMPORTANT: Only remove truly dead code

Before removing each branch, **verify** that it is actually unreachable. The analysis says argparse validates subcommand choices before the handler is called — but if any branch turns out to be reachable (e.g., the subparser is configured differently than expected), do NOT remove it. Only remove what is provably dead.

If a related unit test exists that exercises the dead branch, remove that test too — but again, only if the branch is confirmed dead.

## WHERE

- `src/mcp_coder/cli/main.py` — remove dead else branches
- `tests/cli/test_main.py` — remove any tests for the dead branches

## WHAT

### Dead branches to remove (after verification)

These `else` branches handle "unknown subcommand" values, but argparse's `add_subparsers()` + `add_parser()` validates choices during `parse_args()` — invalid subcommands cause argparse to exit before the handler runs.

| Function | Dead branch | Why unreachable |
|----------|------------|-----------------|
| `_handle_check_command` | `else: "Unknown check subcommand"` | argparse validates `check_subcommand` choices |
| `_handle_gh_tool_command` | `else: "Unknown gh-tool subcommand"` | argparse validates `gh_tool_subcommand` choices |
| `_handle_vscodeclaude_command` | `else: "Unknown vscodeclaude subcommand"` | argparse validates `vscodeclaude_subcommand` choices |
| `_handle_git_tool_command` | `else: "Unknown git-tool subcommand"` | argparse validates `git_tool_subcommand` choices |
| `_handle_commit_command` | `else: "Commit mode not yet implemented"` | argparse validates `commit_mode` choices |
| `main()` | fallback `"Command not yet implemented"` block | argparse validates top-level `command` choices |

### Mypy fix

Removing the else branches creates "missing return statement" errors (mypy). Add `return 1` with an `# unreachable: argparse validates subcommand choices` comment after each if/elif chain to satisfy the type checker.

## HOW

For each function:
1. Verify the corresponding `add_subparsers()` call in `parsers.py` registers all handled subcommands via `add_parser()`
2. Confirm the if/elif chain in the handler covers all registered subcommands
3. Only then remove the else branch
4. Add `return 1  # unreachable: argparse validates subcommand choices` after the if/elif chain
5. Remove any tests that mock or exercise the removed branches
