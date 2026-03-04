# Step 7: Run Full Test Suite and Verify

## Objective
Run complete test suite to ensure all tests pass and no regressions were introduced.

## Context
See `pr_info/steps/summary.md` for full context. This final verification step ensures the implementation is complete and correct.

## WHAT
Execute full test suite for the branch_status module and verify:
1. All new tests pass
2. All existing tests still pass
3. No regressions introduced

## HOW
Run pytest with different test scopes to verify implementation:

### 1. Run All branch_status Tests
```bash
pytest tests/checks/test_branch_status.py -v
```

Expected: All tests pass (green)

### 2. Run Specific New Tests
```bash
# New tests added in this implementation
pytest tests/checks/test_branch_status.py::test_build_ci_error_details_includes_github_urls -v
pytest tests/checks/test_branch_status.py::test_build_ci_error_details_logs_not_available_with_url -v
pytest tests/checks/test_branch_status.py::test_build_ci_error_details_fallback_to_old_format -v

# Updated tests that now use real format
pytest tests/checks/test_branch_status.py::test_build_ci_error_details_single_failure -v
pytest tests/checks/test_branch_status.py::test_build_ci_error_details_multiple_failures -v
pytest tests/checks/test_branch_status.py::test_collect_ci_status_with_truncation -v
```

Expected: All 6 tests pass

### 3. Run Related Integration Tests (if any)
```bash
# Check if check_branch_status command tests exist
pytest tests/cli/commands/test_check_branch_status.py -v
```

Expected: All pass (no changes needed to CLI layer)

## Verification Checklist

### ✅ Test Results
- [ ] All tests in `test_branch_status.py` pass
- [ ] New URL tests pass
- [ ] Updated mock format tests pass
- [ ] No test failures or errors
- [ ] No warnings about deprecated patterns

### ✅ Functionality Verification
- [ ] Logs display with real GitHub format (`{number}_{job_name}.txt`)
- [ ] Pattern matching finds files ending with `_{job_name}.txt`
- [ ] Multi-match warning logs when multiple files match (Decision 1)
- [ ] Fallback works for old format (backward compatible - Decision 2)
- [ ] Warning messages updated to reflect pattern matching (Decision 4)
- [ ] Run URL appears at top
- [ ] Job URLs appear for each job
- [ ] Enhanced error message shows when logs unavailable
- [ ] GitHub URLs included in error message

### ✅ Code Quality
- [ ] No new linter warnings
- [ ] Code follows existing patterns
- [ ] Comments are clear and helpful
- [ ] KISS principle maintained

## Manual Verification (Optional)

If you have access to a real repository with CI:

```bash
# Test with actual GitHub repository
cd /path/to/repo/with/ci
mcp-coder check-branch-status

# Expected output should show:
# - "GitHub Actions: https://github.com/..."
# - "View job: https://github.com/.../job/..."
# - Actual log content (not "logs not available")
```

## Success Criteria

All of these must be true:
1. ✅ All existing tests pass
2. ✅ All new tests pass
3. ✅ No test failures or errors
4. ✅ Pattern matching works correctly
5. ✅ URLs display correctly
6. ✅ Error messages are helpful
7. ✅ Code is simple and maintainable

## Troubleshooting

### If Tests Fail

**Pattern matching not working:**
- Verify loop iterates over `logs.items()`
- Check `endswith()` logic: `f"_{job_name}.txt"`
- Ensure fallback to old format exists

**URLs not appearing:**
- Check `run_url = run_data.get("url", "")` extraction
- Verify `job_id = job.get("id")` extraction
- Check conditional: `if run_url and job_id:`

**Error message issues:**
- Verify if/else block structure
- Check multi-line string formatting
- Ensure fallback message exists

### Debug Commands
```bash
# Run with verbose output
pytest tests/checks/test_branch_status.py -vv

# Run with print statements visible
pytest tests/checks/test_branch_status.py -vv -s

# Run single failing test with full traceback
pytest tests/checks/test_branch_status.py::test_name -vv --tb=long
```

## LLM Prompt
```
Review pr_info/steps/summary.md and decisions.md for context on issue #479.

Implement Step 7: Final verification.

Run complete test suite:

1. All branch_status tests:
   pytest tests/checks/test_branch_status.py -v

2. Verify these specific tests PASS (6 total):
   - test_build_ci_error_details_includes_github_urls (NEW - URLs display)
   - test_build_ci_error_details_logs_not_available_with_url (NEW - error message)
   - test_build_ci_error_details_fallback_to_old_format (NEW - backward compatibility)
   - test_build_ci_error_details_single_failure (UPDATED - real format)
   - test_build_ci_error_details_multiple_failures (UPDATED - real format)
   - test_collect_ci_status_with_truncation (UPDATED - real format)

3. Check for any failures or warnings

4. Verify decisions implemented:
   - Decision 1: Multi-match warning in code
   - Decision 2: Fallback test passes
   - Decision 4: Warning messages updated

If all tests pass:
- Implementation is complete
- Ready for code review

If any tests fail:
- Review the troubleshooting section in step_7.md
- Fix issues and re-run tests
- Do not proceed until all tests pass
```
