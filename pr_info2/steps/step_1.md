# Step 1: Create Integration Test File Structure

## Objective
Create the new simplified test file structure with 3 focused test files and shared fixtures, establishing the foundation for integration-only testing.

## WHERE
- Create: `tests/utils/test_git_integration.py`
- Create: `tests/utils/test_git_error_handling.py`  
- Create: `tests/utils/test_git_edge_cases.py`
- Update: `tests/utils/conftest.py` (add git fixtures)

## WHAT
Create test class skeletons with method signatures:

### test_git_integration.py
```python
class TestGitIntegration:
    def test_new_project_workflow(self, git_repo): pass
    def test_modify_and_commit_workflow(self, git_repo_with_commits): pass
    def test_mixed_file_operations_workflow(self, git_repo_with_commits): pass
    def test_staging_specific_files_workflow(self, git_repo): pass
    def test_commit_all_changes_workflow(self, git_repo): pass
    # ... 20 more workflow methods
```

### test_git_error_handling.py  
```python
class TestGitErrorHandling:
    def test_operations_on_non_git_directory(self, tmp_path): pass
    def test_empty_commit_message_rejected(self, git_repo): pass
    def test_commit_with_no_staged_files(self, git_repo): pass
    def test_stage_files_outside_repository(self, git_repo): pass
    # ... 6 more error methods
```

### test_git_edge_cases.py
```python
class TestGitEdgeCases:
    def test_cross_platform_path_handling(self, git_repo): pass
    def test_unicode_filenames_and_content(self, git_repo): pass
    def test_binary_file_operations(self, git_repo): pass
    def test_gitignore_behavior(self, git_repo): pass
    def test_reasonable_performance_with_many_files(self, git_repo): pass
```

## HOW
Add shared fixtures to conftest.py:

```python
@pytest.fixture
def git_repo(tmp_path):
    """Create clean git repository."""

@pytest.fixture  
def git_repo_with_commits(tmp_path):
    """Create git repo with sample committed files."""

@pytest.fixture
def complex_git_state(tmp_path):
    """Create repo with mixed staged/modified/untracked files."""
```

## ALGORITHM
```
1. Create 3 new test files with empty test classes
2. Define test method signatures for 40 total tests (25+10+5)
3. Add git repository fixtures to conftest.py
4. Import required modules (pytest, pathlib, git)
5. Add placeholder assertions to prevent test collection errors
6. Verify test discovery and collection works
```

## DATA
### File Structure Created
```
tests/utils/
├── test_git_integration.py       # 25 test method stubs
├── test_git_error_handling.py    # 10 test method stubs  
├── test_git_edge_cases.py        # 5 test method stubs
└── conftest.py                   # 3 git fixtures added
```

### Test Method Distribution
- **Integration workflows**: 25 tests covering complete git operations
- **Error handling**: 10 tests for failure scenarios
- **Edge cases**: 5 tests for platform/special cases
- **Total**: 40 tests (vs 450 current)

## LLM Prompt for Implementation
```
Based on the Git Operations Test Simplification Summary, implement Step 1 to create the new test file structure.

Create 3 new test files in tests/utils/ with empty test classes and method stubs:
- test_git_integration.py: 25 workflow test methods
- test_git_error_handling.py: 10 error scenario test methods  
- test_git_edge_cases.py: 5 edge case test methods

Add git repository fixtures to conftest.py for creating test repositories.

Focus on creating the structure only - test implementations come in later steps. Each test method should have a docstring explaining what workflow it will test and a simple `pass` or `assert True` placeholder.

Ensure all imports are correct and the test files can be discovered by pytest.
```

## Verification
- [ ] Run `pytest --collect-only tests/utils/test_git_*` succeeds
- [ ] All 40 test methods are discovered
- [ ] No import errors in new test files
- [ ] Fixtures can be imported and used
- [ ] Test files follow consistent naming and structure
