# CI Failure Analysis

The CI pipeline failed with 9 test failures, all related to the status-aware branch handling implementation for issue #422. The failures fall into two categories:

**Category 1: Output Format Change (1 failure)**
The test `test_execute_vscodeclaude_status_success` in `tests/cli/commands/coordinator/test_vscodeclaude_cli.py:376` expects the message "No active sessions" but the refactored implementation now calls `display_status_table()` which outputs "No sessions or eligible issues found." when both sessions and eligible issues are empty. This is a simple assertion update needed in the test to match the new unified status display format.

**Category 2: Missing GitHub Token in Test Environment (8 failures)**
All remaining failures occur because tests are attempting to instantiate `IssueManager` which requires a GitHub token. The token validation happens in `BaseManager.__init__()` at `base_manager.py:170` which raises `ValueError: GitHub token not found` when neither the config file nor the `GITHUB_TOKEN` environment variable is set. The affected tests are in `test_orchestrator_launch.py` (4 failures) and `test_orchestrator_sessions.py` (4 failures). These tests call `process_eligible_issues()` or restart functions that now create `IssueManager` instances to check linked branches, but the test fixtures don't mock the GitHub token or the `IssueManager` creation. The implementation correctly requires a token for GitHub API operations, but the tests need to either mock the `IssueManager` instantiation or provide a fake token in the test environment.

**Files Requiring Changes:**
- `tests/cli/commands/coordinator/test_vscodeclaude_cli.py` - Update assertion on line 376 to check for "No sessions or eligible issues found." instead of "No active sessions"
- `tests/workflows/vscodeclaude/test_orchestrator_launch.py` - Add mocking for `IssueManager` instantiation in the 4 failing tests to prevent token validation
- `tests/workflows/vscodeclaude/test_orchestrator_sessions.py` - Add mocking for `IssueManager` instantiation in the 4 failing tests or mock the `_prepare_restart_branch` helper that attempts to create it

The root cause is that the implementation added GitHub API interactions (checking linked branches via `IssueManager`) to code paths that previously didn't require them, and the existing test mocks don't cover these new dependencies.