# Step 1: Create Simplified Test File Structure

## Objective
Create the new simplified test file structure with 2 focused test files and streamlined fixtures, establishing the foundation for integration-only testing.

## WHERE
- Create: `tests/utils/test_git_workflows.py`
- Create: `tests/utils/test_git_error_cases.py`
- Update: `tests/utils/conftest.py` (add simplified git fixtures)

## WHAT
Create test class skeletons with method signatures:

### test_git_workflows.py
```python
class TestGitWorkflows:
    def test_new_project_to_first_commit(self, git_repo): pass
    def test_modify_existing_files_workflow(self, git_repo_with_files): pass
    def test_mixed_file_operations_workflow(self, git_repo_with_files): pass
    def test_staging_specific_files_workflow(self, git_repo): pass
    def test_staging_all_changes_workflow(self, git_repo): pass
    def test_commit_workflows(self, git_repo): pass
    def test_multiple_commit_cycles(self, git_repo): pass
    def test_cross_platform_paths(self, git_repo): pass
    def test_unicode_and_binary_files(self, git_repo): pass
    def test_performance_with_many_files(self, git_repo): pass
    # ... 10 more workflow methods
```

### test_git_error_cases.py  
```python
class TestGitErrorCases:
    def test_non_git_directory_operations(self, tmp_path): pass
    def test_invalid_commit_scenarios(self, git_repo): pass
    def test_invalid_file_operations(self, git_repo): pass
    def test_git_command_failures(self, git_repo): pass
    def test_unicode_edge_cases(self, git_repo): pass
    def test_gitignore_behavior(self, git_repo): pass
    def test_file_deletion_handling(self, git_repo_with_files): pass
    def test_platform_compatibility(self, git_repo): pass
    def test_permission_errors(self, git_repo): pass
    def test_concurrent_access_simulation(self, git_repo_with_files): pass
```

## HOW
Add simplified fixtures to conftest.py:

```python
@pytest.fixture
def git_repo(tmp_path):
    """Create clean, empty git repository."""

@pytest.fixture  
def git_repo_with_files(tmp_path):
    """Create git repo with 2-3 committed files for modification tests."""
```

## ALGORITHM
```
1. Create 2 new test files with empty test classes
2. Define test method signatures for 30 total tests (20+10)
3. Add simplified git repository fixtures to conftest.py
4. Import required modules (pytest, pathlib, git)
5. Add placeholder assertions to prevent test collection errors
6. Verify test discovery and collection works
```

## DATA
### File Structure Created
```
tests/utils/
├── test_git_workflows.py         # 20 test method stubs
├── test_git_error_cases.py       # 10 test method stubs
└── conftest.py                   # 2 git fixtures added
```

### Test Method Distribution
- **Workflow tests**: 20 tests covering complete git operations
- **Error & edge cases**: 10 tests for failure scenarios and edge cases
- **Total**: 30 tests (vs 450 current)

## LLM Prompt for Implementation
```
Based on the Git Operations Test Simplification Summary, implement Step 1 to create the new test file structure.

Create 2 new test files in tests/utils/ with empty test classes and method stubs:
- test_git_workflows.py: 20 workflow test methods
- test_git_error_cases.py: 10 error scenario and edge case test methods

Add simplified git repository fixtures to conftest.py for creating test repositories.

Focus on creating the structure only - test implementations come in later steps. Each test method should have a docstring explaining what workflow it will test and a simple `pass` or `assert True` placeholder.

Ensure all imports are correct and the test files can be discovered by pytest.
```

## Verification
- [ ] Run `pytest --collect-only tests/utils/test_git_*` succeeds
- [ ] All 30 test methods are discovered
- [ ] No import errors in new test files
- [ ] Fixtures can be imported and used
- [ ] Test files follow consistent naming and structure
