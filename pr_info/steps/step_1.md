# Step 1: `get_pr_diff` helper, used by `refresh_pr_description`

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_1.md` only. Follow TDD: write the tests first and see them fail, then implement. Keep the change minimal and match the surrounding code style. Use the MCP tools for all file, check and git operations. When done, all checks listed below must pass. This step is exactly one commit.

## Precondition

`get_compact_diff` must be importable from `mcp_coder.mcp_workspace_git` (it is listed in that module's `__all__`). If it is not, write one line to `pr_info/.blocked.txt` and stop.

## WHERE

- `src/mcp_coder/workflow_steps/pr_description.py`
- `tests/workflow_steps/test_pr_description.py`

## WHAT

```python
def get_pr_diff(project_dir: Path, base_branch: str) -> str:
    """Return the branch diff used for PR title/body prompts.

    Compact diff (moved blocks collapsed), excluding pr_info/. Falls back to the
    full branch diff when the compact renderer fails.
    """
```

Place it above `refresh_pr_description`.

## HOW

- Import: `from mcp_coder.mcp_workspace_git import get_branch_diff, get_compact_diff` (shim only, never `mcp_workspace` directly).
- In `refresh_pr_description`, replace
  ```python
  diff_content = get_branch_diff(
      project_dir, base_branch=base_branch, exclude_paths=["pr_info/"]
  )
  ```
  with `diff_content = get_pr_diff(project_dir, base_branch)`. The empty-diff check right below stays unchanged.
- In the `refresh_pr_description` docstring, change "from the full branch diff" to "from the compact branch diff".

## ALGORITHM

```
try:
    return get_compact_diff(project_dir, base_branch, exclude_paths=["pr_info/"])
except Exception as e:   # pylint: disable=broad-exception-caught  (renderer bug -> full diff)
    logger.warning("Compact diff failed, using full branch diff: %s", e)
    return get_branch_diff(project_dir, base_branch=base_branch, exclude_paths=["pr_info/"])
```

The fallback call has no try of its own: `get_branch_diff` never raises (it returns `""` on error). Use inline list literals; no constant.

## DATA

- Returns `str`: the compact diff, the full diff after a fallback, or `""` when there are no changes.
- The function adds no empty-diff handling; each caller checks for an empty result itself.

## Tests (write first)

In `tests/workflow_steps/test_pr_description.py`:

1. Import `get_pr_diff` next to the existing imports from `mcp_coder.workflow_steps.pr_description`.
2. Fixture `mocks`: replace
   `patch(f"{_MODULE}.get_branch_diff", return_value="diff --git a b") as diff`
   with
   `patch(f"{_MODULE}.get_pr_diff", return_value="diff --git a b") as diff`.
   This is required: patching only `get_branch_diff` would not stop the real `get_compact_diff` from running. Keep the `"diff"` key so `test_empty_diff` keeps working.
3. In `test_updates_with_parsed_title_and_kept_closing_ref`, add
   `mocks["diff"].assert_called_once_with(Path("/repo"), "main")`.
4. New class `TestGetPrDiff` (it does not use the `mocks` fixture):
   - `test_returns_compact_diff`: patch `f"{_MODULE}.get_compact_diff"` (return `"compact"`) and `f"{_MODULE}.get_branch_diff"`. Assert:
     - the result is `"compact"`;
     - `get_compact_diff.assert_called_once_with(Path("/repo"), "main", exclude_paths=["pr_info/"])`;
     - `get_branch_diff.assert_not_called()`.
   - `test_falls_back_to_full_diff_on_error`: `get_compact_diff` has `side_effect=IndexError("boom")`; `get_branch_diff` returns `"full"`. Run inside `caplog.at_level(logging.WARNING, logger=_MODULE)`. Assert:
     - the result is `"full"`;
     - `get_compact_diff` was called with `exclude_paths=["pr_info/"]`;
     - `get_branch_diff.assert_called_once_with(Path("/repo"), base_branch="main", exclude_paths=["pr_info/"])`;
     - `"Compact diff failed" in caplog.text` and `"boom" in caplog.text`.

## Checks

- `mcp__mcp-tools-py__run_format_code`
- `mcp__mcp-tools-py__run_pylint_check`
- `mcp__mcp-tools-py__run_mypy_check`
- `mcp__mcp-tools-py__run_pytest_check` with `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not copilot_cli_integration and not install_integration and not jenkins_integration and not langchain_integration and not llm_integration and not setup_integration and not textual_integration"]`
- `mcp__mcp-tools-py__run_lint_imports_check`

## Commit message

`feat(pr-description): build PR diff from compact diff with full-diff fallback`
