# Step 3: Implement Error Cases and Edge Cases

## Objective
Implement the 10 error handling and edge case tests in `test_git_error_cases.py` that verify your git operations fail gracefully in error scenarios and handle edge cases correctly, focusing on real error conditions without mocking.

## WHERE
- File: `tests/utils/test_git_error_cases.py`
- Module: `mcp_coder.utils.git_operations`

## WHAT
Implement 10 test methods combining error scenarios and edge cases:

### Error Handling (6 tests)
```python
def test_non_git_directory_operations(self, tmp_path)
def test_invalid_commit_scenarios(self, git_repo)
def test_invalid_file_operations(self, git_repo)
def test_git_command_failures(self, git_repo)
def test_permission_errors_simulation(self, git_repo)
def test_concurrent_access_simulation(self, git_repo_with_files)
```

### Edge Cases (4 tests)
```python
def test_unicode_edge_cases(self, git_repo)
def test_gitignore_behavior(self, git_repo)
def test_file_deletion_handling(self, git_repo_with_files)
def test_platform_compatibility(self, git_repo)
```

## HOW
### Error Testing Pattern
- Create real error conditions (don't mock unless necessary)
- Verify functions return appropriate error indicators
- Check that operations fail gracefully without exceptions
- Ensure error states don't corrupt git repository

### Edge Case Testing Pattern
- Test cross-platform path separator handling
- Test unicode filename and content support
- Test gitignore file respect
- Test file deletion scenarios

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
7. Test edge cases with real scenarios (unicode, platform paths, etc.)
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

### Edge Case Scenarios
```python
# Unicode test files
unicode_files = {
    "测试文件.txt": "你好世界",
    "emoji_🚀.md": "# Hello 🌍 World!",
    "café.py": "# -*- coding: utf-8 -*-"
}

# Gitignore patterns
gitignore_content = "*.log\n*.tmp\n__pycache__/\n.env\n"

# Cross-platform paths
nested_paths = ["src/utils", "tests/unit", "docs/api"]
```

## LLM Prompt for Implementation
```
Based on the Git Operations Test Simplification Summary and previous steps, implement Step 3 to create the 10 error handling and edge case tests in test_git_error_cases.py.

Create realistic error scenario and edge case tests that:
- Test real error conditions (minimal mocking)
- Verify functions handle errors gracefully
- Check appropriate error return values
- Ensure git repository state remains consistent
- Cover edge cases your application needs to handle
- Test cross-platform compatibility
- Test unicode support
- Test gitignore behavior

Each test should:
1. Create a real error condition or edge case scenario
2. Call git_operations functions with the condition
3. Verify the function returns appropriate indicators
4. Check that no exceptions are raised for expected errors
5. Ensure git repository state is not corrupted
6. Test edge cases with realistic data

Focus on testing that your wrapper functions handle GitPython errors correctly and return appropriate indicators to your application.

Example test structures:

```python
def test_non_git_directory_operations(self, tmp_path):
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

def test_unicode_edge_cases(self, git_repo):
    \"\"\"Test Unicode support in filenames and content.\"\"\"
    repo, project_dir = git_repo
    
    # Create files with Unicode names and content
    unicode_files = {
        "测试文件.txt": "你好世界 Chinese content",
        "emoji_🚀.md": "# Hello 🌍 World! 🎉",
        "café.py": "# -*- coding: utf-8 -*-\\nprint('café')"
    }
    
    for filename, content in unicode_files.items():
        file_path = project_dir / filename
        file_path.write_text(content, encoding='utf-8')
    
    # Operations should handle Unicode correctly
    status = get_full_status(project_dir)
    assert len(status["untracked"]) == 3
    
    result = stage_all_changes(project_dir)
    assert result is True
    
    # Commit with Unicode message
    unicode_message = "Add Unicode files 🎯 测试"
    commit_result = commit_staged_files(unicode_message, project_dir)
    assert commit_result["success"] is True
    
    # Verify commit message preserved
    commits = list(repo.iter_commits())
    assert unicode_message in commits[0].message
```
```

## Verification
- [ ] All 10 error handling and edge case tests pass
- [ ] No exceptions raised for expected error conditions
- [ ] Functions return appropriate error indicators
- [ ] Git repository state remains consistent after errors
- [ ] Error messages are meaningful when provided
- [ ] Unicode filenames and content handled correctly
- [ ] Gitignore patterns are respected
- [ ] Cross-platform compatibility verified
- [ ] Tests complete quickly (no timeouts or hangs)
