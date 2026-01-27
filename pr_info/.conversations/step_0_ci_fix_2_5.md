# CI Fix Attempt 2

I've fixed all 8 CI test failures:

**Category 1 - Mock Target Mismatch (6 failures fixed):**
Updated mock targets in `tests/cli/commands/test_commit.py` from `@patch("mcp_coder.workflow_utils.commit_operations.get_prompt")` to `@patch("mcp_coder.prompt_manager.get_prompt")` in the following tests:
- `TestGenerateCommitMessageWithLLM.test_generate_commit_message_with_llm_success`
- `TestGenerateCommitMessageWithLLM.test_generate_commit_message_with_llm_failure`
- `TestGenerateCommitMessageWithLLMExtended.test_prompt_file_not_found`
- `TestGenerateCommitMessageWithLLMExtended.test_empty_llm_response`
- `TestGenerateCommitMessageWithLLMExtended.test_empty_parsed_commit_message`
- `TestGenerateCommitMessageWithLLMExtended.test_invalid_commit_message_format`

**Category 2 - Function Signature Mismatch (2 failures fixed):**
1. Updated `test_collect_branch_status_all_good` mock assertion from `mock_label.assert_called_once_with(project_dir)` to `mock_label.assert_called_once_with(project_dir, "main")` to match the new `_collect_github_label(project_dir, branch_name)` signature.

2. Fixed `test_collect_branch_status_all_failed` to correctly expect that the "Rebase onto origin/main" recommendation is NOT present when CI is FAILED and tasks are incomplete (per `_generate_recommendations()` logic).

All quality checks pass:
- **Pytest**: 1721 tests pass
- **Mypy**: No type errors
- **Pylint**: No new errors (existing unrelated warnings)