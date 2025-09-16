# Step 3: Implement Error Handling Tests

## Objective
Implement the 10 error handling tests in `test_git_error_handling.py` that verify your git operations fail gracefully in error scenarios, focusing on real error conditions without mocking.

## WHERE
- File: `tests/utils/test_git_error_handling.py`
- Module: `mcp_coder.utils.git_operations`

## WHAT
Implement 10 test methods for error scenarios:

### Repository Errors (3 tests)
```python
def test_operations_on_non_git_directory(self, tmp_path)
def test_operations_on_corrupted_git_repository(self, tmp_path)  
def test_operations_outside_repository_boundary(self, git_repo)
```

### Commit Errors (3 tests)
```python
def test_commit_with_empty_message(self, git_repo)
def test_commit_with_whitespace_only_message(self, git_repo)
def test_commit_with_no_staged_files(self, git_repo)
```

### File Operation Errors (4 tests)
```python
def test_stage_nonexistent_files(self, git_repo)
def test_stage_files_outside_repository(self, git_repo)
def test_stage_mix_of_valid_and_invalid_files(self, git_repo)
def test_stage_empty_file_list(self, git_repo)
```

## HOW
### Error Testing Pattern
- Create real error conditions (don't mock)
- Verify functions return appropriate error indicators
- Check that operations fail gracefully without exceptions
- Ensure error states don't corrupt git repository

### Integration Points
```python
# Error return patterns to verify
CommitResult = {"success": False, "commit_hash": None, "error": str}
stage_operations() -> False  # Boolean failure indicator
status_operations() -> [] or {"modified": [], "untracked": []}  # Empty results
```

## ALGORITHM
```
1. Create real error conditions (non-git dirs, invalid files, etc.)
2. Call git operations functions with error conditions
3. Verify functions return error indicators (False, None, error messages)
4. Check that git repository state remains consistent
5. Ensure no exceptions are raised for expected error cases
6. Verify error messages are meaningful when provided
```

## DATA
### Error Scenarios and Expected Results
```python
# Non-git directory operations
is_git_repository(non_git_path) -> False
get_full_status(non_git_path) -> {"staged": [], "modified": [], "untracked": []}
stage_all_changes(non_git_path) -> False

# Invalid commit scenarios  
commit_staged_files("", project_dir) -> {"success": False, "error": "..."}
commit_staged_files("   ", project_dir) -> {"success": False, "error": "..."}
commit_staged_files("msg", empty_repo) -> {"success": False, "error": "..."}

# File operation errors
stage_specific_files([nonexistent], project_dir) -> False
stage_specific_files([outside_file], project_dir) -> False
stage_specific_files([], project_dir) -> True  # Empty list is valid no-op
```

## LLM Prompt for Implementation
```
Based on the Git Operations Test Simplification Summary and previous steps, implement Step 3 to create the 10 error handling tests in test_git_error_handling.py.

Create realistic error scenario tests that:
- Test real error conditions (no mocking)
- Verify functions handle errors gracefully
- Check appropriate error return values
- Ensure git repository state remains consistent
- Cover error scenarios your application needs to handle

Each test should:
1. Create a real error condition (non-git directory, invalid files, etc.)
2. Call git_operations functions with the error condition
3. Verify the function returns appropriate error indicators
4. Check that no exceptions are raised for expected errors
5. Ensure git repository state is not corrupted

Focus on testing that your wrapper functions handle GitPython errors correctly and return appropriate error indicators to your application.

Example test structure:
```python
def test_operations_on_non_git_directory(self, tmp_path):
    \"\"\"Test git operations fail gracefully on non-git directories.\"\"\"
    # Create regular directory (not git repo)
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    
    # All operations should return appropriate error indicators
    assert is_git_repository(tmp_path) is False
    
    status = get_full_status(tmp_path)
    assert status == {"staged": [], "modified": [], "untracked": []}
    
    assert stage_all_changes(tmp_path) is False
    assert stage_specific_files([test_file], tmp_path) is False
    
    commit_result = commit_all_changes("Should fail", tmp_path)
    assert commit_result["success"] is False
    assert commit_result["commit_hash"] is None
    assert "git repository" in commit_result["error"].lower()

def test_commit_with_empty_message(self, git_repo):
    \"\"\"Test commit rejects empty commit messages.\"\"\"
    repo, project_dir = git_repo
    
    # Create and stage a file
    test_file = project_dir / "test.txt"
    test_file.write_text("content")
    assert stage_specific_files([test_file], project_dir) is True
    
    # Empty message should fail
    result = commit_staged_files("", project_dir)
    assert result["success"] is False
    assert result["commit_hash"] is None
    assert "message" in result["error"].lower()
    
    # Whitespace-only should also fail
    result = commit_staged_files("   \\n\\t  ", project_dir)
    assert result["success"] is False
    
    # File should still be staged after failed commit
    staged = get_staged_changes(project_dir)
    assert "test.txt" in staged
```
```

## Verification
- [ ] All 10 error handling tests pass
- [ ] No exceptions raised for expected error conditions
- [ ] Functions return appropriate error indicators
- [ ] Git repository state remains consistent after errors
- [ ] Error messages are meaningful when provided
- [ ] Tests complete quickly (no timeouts or hangs)
