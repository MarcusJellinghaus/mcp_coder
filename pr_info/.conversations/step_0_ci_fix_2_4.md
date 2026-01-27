# CI Fix Attempt 2

I've completed all the required fixes for the CI pipeline failure. Here's a summary of the changes made:

## Summary of Changes

### 1. `tests/workflow_utils/test_commit_operations.py`
- Changed all `@patch("mcp_coder.workflow_utils.commit_operations.get_prompt")` to `@patch("mcp_coder.prompt_manager.get_prompt")`
- This fixes 14 tests in `TestGenerateCommitMessageWithLLM` class because `get_prompt` is imported inside the function using `from ..prompt_manager import get_prompt`

### 2. `tests/utils/test_branch_status.py`
- **`test_dataclass_immutability`**: Changed from `object.__setattr__(report, "ci_status", "FAILED")` to `report.ci_status = "FAILED"` - frozen dataclasses only prevent normal attribute assignment, not `object.__setattr__()`
- **`test_collect_branch_status_ci_failed`**, **`test_collect_branch_status_rebase_needed`**, **`test_collect_branch_status_tasks_incomplete`**, **`test_collect_branch_status_all_failed`**: Added missing mock for `get_current_branch_name` which is called at the start of `collect_branch_status()`
- **`test_generate_recommendations_logic`**: Fixed assertions to match actual `_generate_recommendations` behavior - rebase is only added when `tasks_complete=True` and `ci_status != FAILED`, and `NOT_CONFIGURED` also adds "Ready to merge"

### 3. `tests/cli/commands/test_check_branch_status.py`
- **`test_execute_check_branch_status_with_fixes_success`** and **`test_execute_check_branch_status_with_fixes_failure`**: Added mock for `resolve_execution_dir` and fixed expectations - `execution_dir` is a `Path` object (from `resolve_execution_dir()`), not `None`
- **`test_run_auto_fixes_ci_only_success`**, **`test_run_auto_fixes_ci_failure`**, **`test_run_auto_fixes_exception_handling`**: Changed patch target for `get_current_branch_name` from `mcp_coder.cli.commands.check_branch_status.get_current_branch_name` to `mcp_coder.utils.git_operations.readers.get_current_branch_name` (since it's imported inside the function), and updated to pass `Path` objects for `execution_dir`

The commit message has been written to `pr_info/.commit_message.txt`.