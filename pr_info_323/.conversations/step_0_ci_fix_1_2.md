# CI Fix Attempt 1

I have completed all the tasks:

## Summary

**Problem:** The CI pipeline failed on `test_restart_closed_sessions_relaunches` because the test called `restart_closed_sessions()` which internally invokes `is_session_stale()`. This function instantiates an `IssueManager` object that inherits from `BaseGitHubManager`, which requires a valid GitHub token from user configuration. Since no GitHub token is available in CI, the constructor raised a `ValueError`: "GitHub token not found."

**Fix:** Added a mock for `is_session_stale` in the test to return `False`, preventing the GitHub API call that was causing the failure. This is the minimal, focused change that allows the test to verify its intended purpose (VSCode relaunch logic) without requiring GitHub credentials.

**Changes made:**
- `tests/cli/commands/coordinator/test_vscodeclaude.py`: Added monkeypatch for `is_session_stale` to return `False` in the `test_restart_closed_sessions_relaunches` test

**Quality checks:**
- Mypy: Passed (no type errors)
- Pylint: The E0401 "Unable to import" errors are environment-specific issues (the MCP checker doesn't have the package installed), not actual code problems

**Commit message written to:** `pr_info/.commit_message.txt`