# CI Fix Attempt 1

I've completed the fix for the CI pipeline failure. Here's a summary of the changes made:

## Summary

**Problem:** Two tests were failing with `TypeError` because mock lambda functions didn't accept the `cached_issues` keyword argument that the production code now passes.

**Changes Made:**

1. **`tests/utils/vscodeclaude/test_status.py`** (line 337):
   - Changed `lambda s: False` to `lambda s, cached_issues=None: False` for `is_issue_closed` mock

2. **`tests/utils/vscodeclaude/test_status.py`** (line 355):
   - Changed `lambda s: False` to `lambda s, cached_issues=None: False` for `is_session_stale` mock

3. **`tests/utils/vscodeclaude/test_orchestrator.py`** (line 547):
   - Changed `lambda session: False` to `lambda session, cached_issues=None: False` for `is_session_stale` mock

**Quality Checks:**
- Mypy: No type errors found
- Pylint: Only pre-existing environment import errors (not related to this change)

**Commit message:** Written to `pr_info/.commit_message.txt`