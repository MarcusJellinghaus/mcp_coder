# Step 2: Add Test for GitHub URL Display

## Objective
Add new test to verify GitHub Actions URLs are displayed in CI error output.

## Context
See `pr_info/steps/summary.md` for full context. This step adds TDD test for the GitHub URL feature before implementation.

## WHERE
- **File**: `tests/checks/test_branch_status.py`
- **Location**: After `test_build_ci_error_details_multiple_failures()` (around line 1050)
- **New function**: `test_build_ci_error_details_includes_github_urls()`

## WHAT
Create test function that verifies:
1. Run URL appears at top of error output
2. Job URLs appear for each failed job
3. Job URLs are correctly formatted

### Function Signature
```python
def test_build_ci_error_details_includes_github_urls() -> None:
    """Test _build_ci_error_details includes GitHub Actions URLs."""
```

## HOW
1. Create test function with descriptive docstring
2. Set up status_result with run URL and job IDs
3. Mock get_run_logs with real format
4. Call _build_ci_error_details()
5. Assert URLs present in output

## ALGORITHM
```
CREATE status_result with run URL and job IDs
MOCK ci_manager.get_run_logs with real format
CALL _build_ci_error_details(...)
ASSERT run URL in result
ASSERT job URL in result
VERIFY URL format is correct
```

## DATA

### Input (Test Setup)
```python
status_result = {
    "run": {
        "id": 12345,
        "url": "https://github.com/user/repo/actions/runs/12345"
    },
    "jobs": [
        {
            "id": 67890,
            "name": "file-size",
            "conclusion": "failure",
            "steps": [{"name": "Run file-size", "conclusion": "failure"}]
        }
    ]
}

mock_instance.get_run_logs.return_value = {
    "2_file-size.txt": "File size check failed"
}
```

### Expected Output
```python
# Result should contain:
assert "GitHub Actions: https://github.com/user/repo/actions/runs/12345" in result
assert "View job: https://github.com/user/repo/actions/runs/12345/job/67890" in result
assert "## Job: file-size" in result
assert "File size check failed" in result
```

## Integration Points
- Import: Already imported `_build_ci_error_details` at top
- Mock: Use existing `MagicMock` pattern
- Assertions: Standard pytest assertions

## Complete Test Code
```python
def test_build_ci_error_details_includes_github_urls() -> None:
    """Test _build_ci_error_details includes GitHub Actions URLs."""
    status_result = {
        "run": {
            "id": 12345,
            "url": "https://github.com/user/repo/actions/runs/12345"
        },
        "jobs": [
            {
                "id": 67890,
                "name": "file-size",
                "conclusion": "failure",
                "steps": [{"name": "Run file-size", "conclusion": "failure"}]
            }
        ]
    }

    mock_instance = MagicMock()
    mock_instance.get_run_logs.return_value = {
        "2_file-size.txt": "File size check failed"
    }

    result = _build_ci_error_details(mock_instance, status_result, False, 300)

    assert result is not None
    # Check run URL at top
    assert "GitHub Actions: https://github.com/user/repo/actions/runs/12345" in result
    # Check job URL in job section
    assert "View job: https://github.com/user/repo/actions/runs/12345/job/67890" in result
    # Verify other content still present
    assert "## Job: file-size" in result
    assert "Failed step: Run file-size" in result
    assert "File size check failed" in result
```

## Verification
```bash
# Run new test (should FAIL)
pytest tests/checks/test_branch_status.py::test_build_ci_error_details_includes_github_urls -v
```

Expected: Test fails because URLs not yet implemented

## LLM Prompt
```
Review pr_info/steps/summary.md for context on issue #479.

Implement Step 2: Add test for GitHub URL display.

File: tests/checks/test_branch_status.py

Add new test function after test_build_ci_error_details_multiple_failures():

def test_build_ci_error_details_includes_github_urls() -> None:
    """Test _build_ci_error_details includes GitHub Actions URLs."""
    
Use the complete test code provided in step_2.md.

This test should verify:
- Run URL appears: "GitHub Actions: https://github.com/user/repo/actions/runs/12345"
- Job URL appears: "View job: https://github.com/user/repo/actions/runs/12345/job/67890"
- Log content still displays correctly

Run the test to verify it FAILS (expected before implementation).
```
