# Step 1 — Move checkout-issue-branch tests into their own file

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_1.md`.
> This is a pure test refactor: move the checkout-issue-branch tests out of
> `tests/cli/commands/test_gh_tool.py` into a new `tests/cli/commands/test_gh_tool_checkout.py`
> without changing any test logic. Run pylint, pytest (fast unit set, `-n auto`) and mypy;
> all must pass. Run `run_format_code`, then make exactly one commit.

## Why

`test_gh_tool.py` is about 748 lines, and the file-size limit is 750. Step 2 adds checkout
tests, so they need their own file first.

## Precondition

If `tests/cli/commands/test_gh_tool_checkout.py` already exists, write one line to
`pr_info/.blocked.txt` and stop.

## WHERE

- Create `tests/cli/commands/test_gh_tool_checkout.py`
- Modify `tests/cli/commands/test_gh_tool.py`

## WHAT

Move, unchanged, everything from the `# Fixtures for checkout-issue-branch` banner to the
end of `test_gh_tool.py`:

- fixtures `mock_issue_manager`, `mock_branch_manager`, `mock_fetch_remote`, `mock_checkout_branch`
- classes `TestCheckoutIssueBranchExitCodes`, `TestCheckoutIssueBranchBehavior`,
  `TestGhToolCheckoutIssueBranchIntegration`

## HOW

- The new file gets its own module docstring ("Tests for gh-tool checkout-issue-branch CLI
  command.") and the imports it needs: `argparse`, `logging`, `Generator`, `Path`,
  `MagicMock`, `patch`, `pytest`, `execute_checkout_issue_branch`.
- Copy the `mock_resolve_project_dir` fixture into the new file; it stays in
  `test_gh_tool.py` as well, since the get-base-branch tests use it.
- In `test_gh_tool.py`, drop `execute_checkout_issue_branch` from the import and remove any
  imports that become unused.

## DATA

No production code changes. The test count stays the same.
