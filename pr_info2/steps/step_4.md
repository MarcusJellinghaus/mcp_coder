# Step 4: Implement Edge Case Tests

## Objective
Implement the 5 edge case tests in `test_git_edge_cases.py` that verify cross-platform compatibility and special scenarios your application might encounter.

## WHERE
- File: `tests/utils/test_git_edge_cases.py`
- Module: `mcp_coder.utils.git_operations`

## WHAT
Implement 5 focused edge case tests:

### Platform Compatibility (2 tests)
```python
def test_cross_platform_path_handling(self, git_repo)
def test_unicode_filenames_and_content(self, git_repo)
```

### Special File Types (2 tests)
```python
def test_binary_file_operations(self, git_repo)
def test_gitignore_behavior(self, git_repo)
```

### Performance Edge Case (1 test)
```python
def test_reasonable_performance_with_many_files(self, git_repo)
```

## HOW
### Edge Case Testing Focus
- Cross-platform path separator handling (Windows vs Unix)
- Unicode filename and content support
- Binary file staging and committing
- Gitignore file respect
- Reasonable performance with moderate file counts

### Integration Points
```python
# Path handling verification
Path("/") vs Path("\\")  # Platform differences
file_path.as_posix()     # Consistent path format
relative_to(project_dir) # Relative path conversion

# Unicode support
filename = "测试文件.txt"  # Unicode filename
content = "Hello 🌍 World!"  # Unicode content
commit_message = "Add files 🚀"  # Unicode commit message
```

## ALGORITHM
```
1. Create edge case scenarios (unicode files, binary content, etc.)
2. Perform git operations using your wrapper functions
3. Verify operations complete successfully
4. Check that git repository handles edge cases correctly
5. Ensure cross-platform compatibility
6. Validate reasonable performance characteristics
```

## DATA
### Edge Case Scenarios
```python
# Unicode test files
unicode_files = {
    "chinese.txt": "你好世界",
    "emoji.md": "# Hello 🌍 World! 🚀",
    "accents.py": "# café naïve résumé"
}

# Binary file simulation
binary_content = bytes(range(256)) + b"binary data" * 100

# Gitignore patterns
gitignore_content = """
*.log
*.tmp
__pycache__/
.env
build/
dist/
"""

# Performance test scale
moderate_file_count = 50  # Reasonable test size
```

## LLM Prompt for Implementation
```
Based on the Git Operations Test Simplification Summary and previous steps, implement Step 4 to create the 5 edge case tests in test_git_edge_cases.py.

Create focused edge case tests that:
- Test cross-platform compatibility
- Verify Unicode filename and content support
- Handle binary files correctly
- Respect gitignore patterns
- Ensure reasonable performance

Each test should:
1. Create a specific edge case scenario
2. Use your git_operations functions to handle the scenario
3. Verify the operations complete successfully
4. Check that git repository state is correct
5. Focus on edge cases your application might encounter

Example test structure:
```python
def test_cross_platform_path_handling(self, git_repo):
    \"\"\"Test path handling works on both Windows and Unix.\"\"\"
    repo, project_dir = git_repo
    
    # Create nested directory structure
    nested_dirs = [
        project_dir / "src" / "utils",
        project_dir / "tests" / "unit",
        project_dir / "docs" / "api"
    ]
    
    for dir_path in nested_dirs:
        dir_path.mkdir(parents=True)
        test_file = dir_path / "test.py"
        test_file.write_text(f"# {dir_path.name}")
    
    # Stage all files
    result = stage_all_changes(project_dir)
    assert result is True
    
    # Check staged files use consistent path format
    staged_files = get_staged_changes(project_dir)
    assert len(staged_files) == 3
    
    # Verify paths work regardless of platform
    for staged_file in staged_files:
        assert not str(project_dir) in staged_file  # Should be relative
        assert ("/" in staged_file or "\\\\" in staged_file)  # Has separators
    
    # Commit should work
    commit_result = commit_staged_files("Add nested files", project_dir)
    assert commit_result["success"] is True

def test_unicode_filenames_and_content(self, git_repo):
    \"\"\"Test Unicode support in filenames and content.\"\"\"
    repo, project_dir = git_repo
    
    # Create files with Unicode names and content
    unicode_files = {
        "测试文件.txt": "你好世界 Chinese content",
        "emoji_🚀.md": "# Hello 🌍 World! 🎉\\n\\nUnicode content",
        "café.py": "# -*- coding: utf-8 -*-\\nprint('café naïve résumé')"
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
- [ ] All 5 edge case tests pass
- [ ] Unicode filenames and content handled correctly
- [ ] Binary files can be staged and committed
- [ ] Gitignore patterns are respected
- [ ] Cross-platform path handling works
- [ ] Performance test completes in reasonable time
- [ ] Tests work on both Windows and Unix systems
