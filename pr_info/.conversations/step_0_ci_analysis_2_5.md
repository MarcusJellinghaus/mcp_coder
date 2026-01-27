# CI Failure Analysis

The CI pipeline failed with 8 test failures in the unit-tests job, falling into two distinct categories.

**Category 1: Mock Target Mismatch in Commit Tests (6 failures)**

Six tests in `tests/cli/commands/test_commit.py` failed because they attempt to mock `mcp_coder.workflow_utils.commit_operations.get_prompt`, but this function no longer exists at that module level. The `get_prompt` function is imported locally inside `generate_commit_message_with_llm()` from `mcp_coder.prompt_manager`, not exposed at the `commit_operations` module level. The tests `TestGenerateCommitMessageWithLLM` and `TestGenerateCommitMessageWithLLMExtended` use `@patch("mcp_coder.workflow_utils.commit_operations.get_prompt")` which fails with `AttributeError: module does not have the attribute 'get_prompt'`.

The fix requires updating the mock targets in these tests to either patch `mcp_coder.prompt_manager.get_prompt` or mock the import at the correct location where it's actually used.

**Category 2: Function Signature Mismatch in Branch Status Tests (2 failures)**

Two tests in `tests/utils/test_branch_status.py` failed due to a signature change in `_collect_github_label()`. The function now accepts an optional `branch_name` parameter: `_collect_github_label(project_dir: Path, branch_name: Optional[str] = None)`. The `collect_branch_status()` function passes `branch_name` when calling `_collect_github_label(project_dir, branch_name)`, but the test `test_collect_branch_status_all_good` expects the old signature with only `project_dir`. The mock assertion `mock_label.assert_called_once_with(project_dir)` fails because the actual call includes the branch name: `_collect_github_label(PosixPath('/test/repo'), 'main')`.

Additionally, `test_collect_branch_status_all_failed` expects the recommendation "Rebase onto origin/main" but the `_generate_recommendations()` function only adds this recommendation when `tasks_complete=True` AND `ci_status != CI_FAILED`. Since this test sets both `ci_status="FAILED"` and `tasks_complete=False`, the rebase recommendation is correctly not generated, but the test incorrectly asserts it should be present.

The fix requires updating mock assertions in the branch status tests to match the new function signature (passing both `project_dir` and `branch_name`), and correcting the `test_collect_branch_status_all_failed` test to either adjust its expectations or change the test setup to reflect valid recommendation generation logic.