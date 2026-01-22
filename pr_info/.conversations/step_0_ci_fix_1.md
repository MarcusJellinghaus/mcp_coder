# CI Fix Attempt 1

I've completed the fix for the CI pipeline failure. Here's a summary of the changes:

## Summary

**Problem:** The test `test_error_resilience_mixed_scenarios` in `tests/formatters/test_integration.py:209` was failing because it expected both "black" and "isort" keys in the results dictionary, but only "black" was present.

**Root cause:** The `format_code()` function in `src/mcp_coder/formatters/__init__.py` was updated with an "early exit on failure" feature. When Black encounters a syntax error, it fails and the loop breaks immediately, so isort never runs.

**Fix:** Updated the test to expect the new behavior:
- Changed assertions to expect only "black" in results when Black fails
- Added assertion that "isort" is NOT in results (confirming early exit works)
- Updated the docstring to document this early exit behavior

**Quality checks:**
- Pylint: Passed (no issues)
- Mypy: Passed (no type errors)
- Commit message written to `pr_info/.commit_message.txt`