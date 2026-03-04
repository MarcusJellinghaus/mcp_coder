# Step 3: Add Test for Improved Error Message

## Objective
Add test to verify improved "logs not available" message includes GitHub URL.

## Context
See `pr_info/steps/summary.md` for full context. This step tests the enhanced error message when logs cannot be found locally.

## WHERE
- **File**: `tests/checks/test_branch_status.py`
- **Location**: After `test_build_ci_error_details_includes_github_urls()` (around line 1090)
- **New function**: `test_build_ci_error_details_logs_not_available_with_url()`

## WHAT
Create test function that verifies:
1. When logs not found, message includes "(logs not available locally)"
2. GitHub job URL is included in the message
3. Message is user-friendly

### Function Signature
```python
def test_build_ci_error_details_logs_not_available_with_url() -> None:
    """Test _build_ci_error_details shows GitHub URL when logs unavailable."""
```

## HOW
1. Create test function with descriptive docstring
2. Set up status_result with run URL and job ID
3. Mock get_run_logs with EMPTY dict (no logs)
4. Call _build_ci_error_details()
5. Assert error message includes GitHub URL

## ALGORITHM
```
CREATE status_result with run URL and job IDs
MOCK ci_manager.get_run_logs with EMPTY dict
CALL _build_ci_error_details(...)
ASSERT "(logs not available locally)" in result
ASSERT job URL in result
VERIFY message is user-friendly
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

# IMPORTANT: Empty dict means no logs found
mock_instance.get_run_logs.return_value = {}
```

### Expected Output
```python
# Result should contain:
assert "(logs not available locally)" in result
assert "View on GitHub: https://github.com/user/repo/actions/runs/12345/job/67890" in result
assert "## Job: file-size" in result
```

## Integration Points
- Import: Already imported `_build_ci_error_details` at top
- Mock: Use existing `MagicMock` pattern
- Assertions: Standard pytest assertions

## Complete Test Code
```python
def test_build_ci_error_details_logs_not_available_with_url() -> None:
    """Test _build_ci_error_details shows GitHub URL when logs unavailable."""
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
    # Empty dict = no logs available
    mock_instance.get_run_logs.return_value = {}

    result = _build_ci_error_details(mock_instance, status_result, False, 300)

    assert result is not None
    # Check error message with GitHub URL
    assert "(logs not available locally)" in result
    assert "View on GitHub: https://github.com/user/repo/actions/runs/12345/job/67890" in result
    # Check job header still present
    assert "## Job: file-size" in result
    assert "Failed step: Run file-size" in result
```

## Verification
```bash
# Run new test (should FAIL)
pytest tests/checks/test_branch_status.py::test_build_ci_error_details_logs_not_available_with_url -v
```

Expected: Test fails because enhanced error message not yet implemented

## LLM Prompt
```
Review pr_info/steps/summary.md for context on issue #479.

Implement Step 3: Add test for improved error message when logs unavailable.

File: tests/checks/test_branch_status.py

Add new test function after test_build_ci_error_details_includes_github_urls():

def test_build_ci_error_details_logs_not_available_with_url() -> None:
    """Test _build_ci_error_details shows GitHub URL when logs unavailable."""

Use the complete test code provided in step_3.md.

Key test scenario:
- get_run_logs returns EMPTY dict (no logs found)
- Verify message: "(logs not available locally)"
- Verify GitHub URL: "View on GitHub: https://github.com/user/repo/actions/runs/12345/job/67890"

Run the test to verify it FAILS (expected before implementation).
```
