# CI Failure Analysis

The CI pipeline failed in the unit-tests job with two test failures in the vscodeclaude module. Both failures are TypeError exceptions indicating that mock lambda functions received unexpected keyword arguments.

The root cause is a signature mismatch between the production code and test mocks. The `is_issue_closed` and `is_session_stale` functions in `src/mcp_coder/utils/vscodeclaude/status.py` were updated to accept an optional `cached_issues` keyword argument for performance optimization (avoiding redundant API calls). However, two test files still use simple lambda mocks that don't accept this parameter:

1. `tests/utils/vscodeclaude/test_status.py:368` - The `test_display_status_table_with_session` test patches `is_issue_closed` with `lambda s: False`, but the production code in `display_status_table` (status.py:283) now calls it as `is_issue_closed(session, cached_issues=repo_cached_issues)`.

2. `tests/utils/vscodeclaude/test_orchestrator.py:575` - The `test_restart_closed_sessions_relaunches` test patches `is_session_stale` with `lambda session: False`, but the production code in `restart_closed_sessions` (orchestrator.py:678) now calls it as `is_session_stale(session, cached_issues=repo_cached_issues)`.

To fix these failures, the mock lambdas need to be updated to accept the `cached_issues` keyword argument. The lambdas should be changed from `lambda s: False` and `lambda session: False` to `lambda s, cached_issues=None: False` and `lambda session, cached_issues=None: False` respectively. This will match the new function signatures while maintaining the same mock behavior.