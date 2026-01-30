# CI Fix Attempt 2

I have completed the CI pipeline fix. Here's a summary of the changes made:

## Summary

**Problem:** The CI file-size check was failing because `tests/utils/github_operations/test_pr_manager.py` had grown to 755 lines, exceeding the 750 line limit.

**Solution:** Refactored `test_pr_manager.py` by introducing a `create_mock_pr()` helper function that consolidates the repetitive mock PR object creation pattern.

### Changes Made:

1. **Added `create_mock_pr()` helper function** (lines 18-51):
   - Creates mock PR objects with sensible defaults for all attributes
   - Accepts keyword overrides for any attribute
   - Includes special handling for optional fields (`skip_dates`, `skip_user`)
   - Reduces boilerplate from ~15 lines per mock PR to 1-3 lines

2. **Updated 8 tests** to use the new helper function:
   - `test_create_pull_request_success`
   - `test_get_pull_request_success`
   - `test_list_pull_requests_data_transformation`
   - `test_close_pull_request_success`
   - `test_create_pr_resolves_default_branch_when_none`
   - `test_create_pr_uses_explicit_base_branch`
   - `test_create_pr_resolves_master_as_default_branch`

3. **Line count reduced** from 755 to approximately 620 lines (well below the 750 limit)

### Quality Checks:
- **Mypy:** ✅ No type errors found
- **Pylint:** ✅ No errors in `test_pr_manager.py` (note: pre-existing errors in `test_issue_manager.py` related to missing `_parse_base_branch` implementation are unrelated to this fix)

The commit message has been written to `pr_info/.commit_message.txt`.