# Step 15: Update Tests for New Error Handling

## Objective
Update unit tests that verify bare `Exception` handling, since this behavior has been removed.

## WHERE
- **Files**: 
  - `tests/utils/github_operations/test_issue_manager.py`
  - `tests/llm_providers/claude/test_claude_code_api_error_handling.py`

## WHAT
Tests that need updating:
```python
# Tests expecting CalledProcessError with long error messages
test_windows_path_length_error
test_cli_not_found_error_with_path_found
test_cli_not_found_error_without_path_found
test_file_not_found_error_handling
test_permission_error_handling
```

## HOW
- Update test expectations from `CalledProcessError` to `ClaudeAPIError`
- Update expected error message content (shorter, cleaner messages)
- Remove tests that verify bare Exception handling if they exist
- Keep tests for GithubException (401/403 raising, others returning empty)

## ALGORITHM
```
1. Identify tests that expect bare Exception handling
2. Update to expect ClaudeAPIError (already in diff)
3. Update error message expectations
4. Remove any tests specific to Exception catching
5. Verify all tests pass
```

## DATA
```python
# Error message expectations to update
"Windows path length limit exceeded"  # Keep
"Unable to execute Claude CLI"        # Keep
"Authentication/login problems"       # Keep
# Remove: "Move your project", "Enable long path", etc.
```

## LLM Prompt
```
Based on Steps 11-14, implement Step 15: Update Tests for New Error Handling.

Review and update tests affected by removing bare Exception catches:

1. In test_claude_code_api_error_handling.py:
   - Tests already updated for ClaudeAPIError
   - Verify error message expectations match new shorter messages
   
2. In test_issue_manager.py (and similar test files):
   - Remove any tests that specifically verify bare Exception handling
   - Keep all tests for GithubException (401/403 raising, others returning empty)
   - Verify all unit tests pass

Requirements:
- Run full test suite to identify failures
- Update test expectations, not implementation
- Ensure integration tests still pass
```
