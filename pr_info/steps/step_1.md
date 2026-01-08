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
- Use `TemporaryDirectory` for real filesystem testing (same pattern as `test_file_operations.py`)
- Import `cleanup_repository` (already imported in test file)

## ALGORITHM: Test Pseudocode

```
1. Create temp directory as project_dir
2. Create pr_info/.conversations/ with test files inside
3. Create pr_info/TASK_TRACKER.md (required by cleanup_repository)
4. Call cleanup_repository(project_dir)
5. Assert .conversations directory no longer exists
6. Assert function returned True
```

## DATA: Test Structure

- **Input**: Temporary directory with `pr_info/.conversations/` containing test files
- **Expected**: Directory deleted, function returns `True`

## Test Cases to Add

1. **Happy path**: `.conversations/` exists and is deleted successfully
2. **No-op path**: `.conversations/` doesn't exist (should still succeed)

## Notes

- The test will FAIL initially (expected for TDD) until Step 2 implements the functionality
- Use real filesystem operations, not mocks, for this integration-style test
