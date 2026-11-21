# Step 2: `generate_pr_summary` uses `get_pr_diff`

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_2.md` only (step 1 is already done). Follow TDD: update the tests first and see them fail, then implement. Keep the change minimal. Use the MCP tools for all file, check and git operations. When done, all checks listed below must pass. This step is exactly one commit.

## Precondition

`get_pr_diff` must exist in `src/mcp_coder/workflow_steps/pr_description.py` (from step 1). If it does not, write one line to `pr_info/.blocked.txt` and stop.

## WHERE

- `src/mcp_coder/workflows/create_pr/core.py`
- `tests/workflows/create_pr/test_generation.py`

## WHAT

No new functions. `generate_pr_summary(project_dir, provider, mcp_config=None, settings_file=None) -> tuple[str, str]` keeps its signature and behaviour, apart from where the diff comes from.

## HOW

- `core.py` imports:
  - remove `get_branch_diff,` from the `from mcp_coder.mcp_workspace_git import (...)` block;
  - add `from mcp_coder.workflow_steps.pr_description import get_pr_diff`, placed in import order next to `from mcp_coder.workflow_steps.prerequisites import ...`.
  - Import directly; do not re-export via `create_pr/helpers.py`.
- `core.py` in `generate_pr_summary`: replace
  ```python
  diff_content = get_branch_diff(
      project_dir, base_branch=base_branch, exclude_paths=["pr_info/"]
  )
  ```
  with `diff_content = get_pr_diff(project_dir, base_branch)`. The empty-diff check below stays unchanged.
- The file must not grow (it is near the 750-line CI limit); this change makes it shorter.

## ALGORITHM

None. This is a one-line call-site swap.

## DATA

Unchanged: `(title, body)`. An empty diff still returns `("Pull Request", "Pull Request")`.

## Tests (write first)

In `tests/workflows/create_pr/test_generation.py`:

1. Replace every `@patch("mcp_coder.workflows.create_pr.core.get_branch_diff")` with `@patch("mcp_coder.workflows.create_pr.core.get_pr_diff")`. Keep the parameter name `mock_get_diff`.
2. In `test_generate_pr_summary_success`, replace the `exclude_paths` assertion with
   `mock_get_diff.assert_called_once_with(Path("/test/project"), "main")`
   (the `pr_info/` exclusion is now covered by the helper tests from step 1).
3. Delete `test_generate_pr_summary_git_diff_exception`: the helper no longer raises, and its fallback test from step 1 replaces this test.

## Checks

- `mcp__mcp-tools-py__run_format_code`
- `mcp__mcp-tools-py__run_pylint_check`
- `mcp__mcp-tools-py__run_mypy_check`
- `mcp__mcp-tools-py__run_pytest_check` with `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not copilot_cli_integration and not install_integration and not jenkins_integration and not langchain_integration and not llm_integration and not setup_integration and not textual_integration"]`
- `mcp__mcp-tools-py__run_pytest_check` with `extra_args=["-n", "auto"]`, `markers=["git_integration"]`. This includes `test_pr_summary_generation_with_diff`, which runs the real compact diff and must pass.
- `mcp__mcp-tools-py__run_lint_imports_check`
- `mcp__mcp-workspace__check_file_size`: `src/mcp_coder/workflows/create_pr/core.py` must not be reported.

## Commit message

`feat(create-pr): generate PR summary from compact diff`
