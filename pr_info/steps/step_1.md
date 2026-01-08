# Step 1: Add Test for Conversations Directory Cleanup

## LLM Prompt

```
Implement Step 1 from pr_info/steps/step_1.md for Issue #259.
Reference: pr_info/steps/summary.md

This step adds a test to verify that the `cleanup_repository()` function 
deletes the `pr_info/.conversations/` directory. Follow TDD - write the 
test first, which will initially fail until Step 2 is implemented.
```

## WHERE: File Paths

- **Test file**: `tests/workflows/create_pr/test_repository.py`

## WHAT: Test Function

```python
def test_cleanup_repository_deletes_conversations_directory(self) -> None:
    """Test that cleanup_repository deletes pr_info/.conversations/ directory."""
```

## HOW: Integration Points

- Add test to existing `TestCleanupRepository` class
- Use `@patch` decorators for mocking (same pattern as existing tests in file)
- Mock all four cleanup helpers for consistent, isolated unit tests:
  - `delete_steps_directory`
  - `truncate_task_tracker`
  - `clean_profiler_output`
  - New conversations deletion logic
- Import `cleanup_repository` (already imported in test file)

## ALGORITHM: Test Pseudocode

```
1. Set up @patch decorators for all four cleanup helpers
2. Configure all mocks to return True (success case)
3. Call cleanup_repository(Path("/test/project"))
4. Assert function returned True
5. Assert all four mocked functions were called with correct arguments
```

## DATA: Test Structure

- **Input**: Temporary directory with `pr_info/.conversations/` containing test files
- **Expected**: Directory deleted, function returns `True`

## Test Cases to Add

1. **Happy path**: `.conversations/` exists and is deleted successfully
2. **No-op path**: `.conversations/` doesn't exist (should still succeed)

## Notes

- The test will FAIL initially (expected for TDD) until Step 2 implements the functionality
- Use mocks for consistency with existing tests in the file
- Also update existing tests to mock `clean_profiler_output` for full isolation
