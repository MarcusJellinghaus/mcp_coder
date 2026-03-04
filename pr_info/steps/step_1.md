# Step 1: Update Tests for Real GitHub Log Format

## Objective
Update existing test mocks to use the actual GitHub Actions log filename format, preparing for TDD implementation.

## Context
See `pr_info/steps/summary.md` for full context. This step updates test fixtures to match real GitHub format before implementing the fix.

## WHERE
- **File**: `tests/checks/test_branch_status.py`
- **Functions to modify**:
  - `test_build_ci_error_details_single_failure()` (line ~1000)
  - `test_build_ci_error_details_multiple_failures()` (line ~1025)
  - `test_collect_ci_status_with_truncation()` (line ~875)

## WHAT
Update mock log dictionaries in existing tests to use GitHub's actual format:
- **Old format**: `{job_name}/{step_number}_{step_name}.txt`
- **New format**: `{global_number}_{job_name}.txt`

### Example Changes
```python
# OLD (incorrect format)
mock_instance.get_run_logs.return_value = {
    "test-job/0_Run tests.txt": "Error details here"
}

# NEW (real GitHub format)
mock_instance.get_run_logs.return_value = {
    "2_test-job.txt": "Error details here"
}
```

## HOW
1. Locate test functions that mock `get_run_logs.return_value`
2. Update dictionary keys to format: `"{number}_{job_name}.txt"`
3. Use realistic execution numbers (2, 4, 9, etc.)
4. Run tests to verify they currently FAIL (expected with old implementation)

## ALGORITHM
```
FOR each test function with get_run_logs mock:
    FIND mock_instance.get_run_logs.return_value = {...}
    FOR each log filename key:
        REPLACE "{job_name}/{step_number}_{step_name}.txt"
        WITH "{execution_number}_{job_name}.txt"
    END FOR
END FOR
```

## DATA

### Input (Test Mocks)
```python
# Function: test_build_ci_error_details_single_failure
mock_instance.get_run_logs.return_value = {
    "2_test-job.txt": "Error details here"
}

# Function: test_build_ci_error_details_multiple_failures
mock_instance.get_run_logs.return_value = {
    "2_test-job.txt": "First job error",
    "4_lint-job.txt": "Lint error",
    "9_build-job.txt": "Build error"
}

# Function: test_collect_ci_status_with_truncation
mock_instance.get_run_logs.return_value = {
    "2_test-job.txt": long_logs  # 400 lines
}
```

### Expected Test Behavior
- Tests will FAIL after this step (expected)
- Error: Log files not found because implementation still uses old format
- This confirms tests are properly detecting the issue

## Integration Points
- No new imports needed
- Only modify existing mock return values
- Tests use existing test infrastructure

## Verification
```bash
# Run affected tests (should FAIL)
pytest tests/checks/test_branch_status.py::test_build_ci_error_details_single_failure -v
pytest tests/checks/test_branch_status.py::test_build_ci_error_details_multiple_failures -v
pytest tests/checks/test_branch_status.py::test_collect_ci_status_with_truncation -v
```

Expected output: Tests fail with logs showing "(logs not available)"

## LLM Prompt
```
Review pr_info/steps/summary.md for context on issue #479.

Implement Step 1: Update test mocks to use real GitHub Actions log format.

Files to modify: tests/checks/test_branch_status.py

Update these test functions to use format "{number}_{job_name}.txt":
- test_build_ci_error_details_single_failure (use "2_test-job.txt")
- test_build_ci_error_details_multiple_failures (use "2_test-job.txt", "4_lint-job.txt", "9_build-job.txt")
- test_collect_ci_status_with_truncation (use "2_test-job.txt")

Change only the mock_instance.get_run_logs.return_value dictionary keys.

After changes, run the tests to verify they FAIL (expected behavior).
```
