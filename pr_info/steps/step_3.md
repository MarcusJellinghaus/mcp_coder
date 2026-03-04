# Step 3: Add Tests for Error Handling and Fallback

## Objective
Add tests to verify:
1. Improved "logs not available" message includes GitHub URL
2. Fallback to old format still works (backward compatibility)

## Context
See `pr_info/steps/summary.md` for full context. This step tests the enhanced error message when logs cannot be found locally.

## WHERE
- **File**: `tests/checks/test_branch_status.py`
- **Location**: After `test_build_ci_error_details_includes_github_urls()` (around line 1090)
- **New functions**: 
  - `test_build_ci_error_details_logs_not_available_with_url()`
  - `test_build_ci_error_details_fallback_to_old_format()`

## WHAT

### Test 1: Enhanced Error Message
Create test function that verifies:
1. When logs not found, message includes "(logs not available locally)"
2. GitHub job URL is included in the message
3. Message is user-friendly

### Test 2: Old Format Fallback
Create test function that verifies:
1. Old format logs still work: `{job_name}/{step_number}_{step_name}.txt`
2. Backward compatibility is maintained
3. Logs display correctly with old format

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

### Test 1: Enhanced Error Message
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

### Test 2: Old Format Fallback (Backward Compatibility)
```python
def test_build_ci_error_details_fallback_to_old_format() -> None:
    """Test _build_ci_error_details falls back to old log format."""
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
                "steps": [{"name": "Run file-size", "conclusion": "failure", "number": 3}]
            }
        ]
    }

    mock_instance = MagicMock()
    # Use OLD format (pattern match will fail, fallback should work)
    mock_instance.get_run_logs.return_value = {
        "file-size/3_Run file-size.txt": "File size check failed (old format)"
    }

    result = _build_ci_error_details(mock_instance, status_result, False, 300)

    assert result is not None
    # Verify log content from old format is displayed
    assert "File size check failed (old format)" in result
    assert "## Job: file-size" in result
    assert "Failed step: Run file-size" in result
```

## Verification
```bash
# Run new tests (should FAIL)
pytest tests/checks/test_branch_status.py::test_build_ci_error_details_logs_not_available_with_url -v
pytest tests/checks/test_branch_status.py::test_build_ci_error_details_fallback_to_old_format -v
```

Expected: 
- First test fails because enhanced error message not yet implemented
- Second test fails because pattern matching not yet implemented (will try new format first)

## LLM Prompt
```
Review pr_info/steps/summary.md and decisions.md for context on issue #479.

Implement Step 3: Add tests for error handling and fallback.

File: tests/checks/test_branch_status.py

Add TWO new test functions after test_build_ci_error_details_includes_github_urls():

1. test_build_ci_error_details_logs_not_available_with_url()
   - Tests enhanced error message when logs not found
   - get_run_logs returns EMPTY dict
   - Verify message includes GitHub URL

2. test_build_ci_error_details_fallback_to_old_format()
   - Tests backward compatibility with old log format
   - get_run_logs returns old format: "file-size/3_Run file-size.txt"
   - Verify logs still display correctly

Use the complete test code provided in step_3.md for both tests.

Run both tests to verify they FAIL (expected before implementation).
```
