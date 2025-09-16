# Step 2: Implement Core Workflow Tests

## Objective  
Implement the 20 core workflow tests in `test_git_workflows.py` that cover the main git operations your application uses, focusing on complete end-to-end scenarios without mocking.

## WHERE
- File: `tests/utils/test_git_workflows.py`
- Module: `mcp_coder.utils.git_operations`

## WHAT
Implement 20 test methods that cover complete workflows:

### Core Workflows (8 tests)
```python
def test_new_project_to_first_commit(self, git_repo)
def test_modify_existing_files_workflow(self, git_repo_with_files)  
def test_mixed_file_operations_workflow(self, git_repo_with_files)
def test_staging_specific_files_workflow(self, git_repo)
def test_staging_all_changes_workflow(self, git_repo)
def test_commit_workflows(self, git_repo)
def test_multiple_commit_cycles(self, git_repo)
def test_git_status_tracking_workflow(self, git_repo)
```

### Advanced Workflows (6 tests)
```python
def test_subdirectory_operations_workflow(self, git_repo)
def test_file_deletion_workflow(self, git_repo_with_files)
def test_partial_staging_workflow(self, git_repo_with_files)
def test_commit_message_variations(self, git_repo)
def test_repository_state_transitions(self, git_repo)
def test_realistic_development_cycle(self, git_repo)
```

### Cross-Platform & Performance (6 tests)
```python
def test_cross_platform_path_handling(self, git_repo)
def test_unicode_filenames_and_content(self, git_repo)
def test_binary_file_operations(self, git_repo)
def test_gitignore_integration(self, git_repo)
def test_performance_with_many_files(self, git_repo)
def test_realistic_project_simulation(self, git_repo)
```

## HOW
### Integration Points
- Import all functions from `mcp_coder.utils.git_operations`
- Use `git.Repo` directly for setup/verification only
- Use simplified pytest fixtures (git_repo, git_repo_with_files)
- Assert on return values and git repository state
- No mocking of GitPython calls

### Test Pattern
```python
def test_workflow_name(self, fixture):
    # Setup: Create files/modify state (inline, not complex fixtures)
    # Action: Call your git operation functions in sequence
    # Verify: Check return values AND git repo state
    # Assert: Multiple assertions on outcomes
```

## ALGORITHM
```
1. Create test files and directories in git repository (inline setup)
2. Call git_operations functions in realistic sequence
3. Verify function return values match expectations
4. Check actual git repository state using GitPython
5. Assert on both wrapper function behavior and git state
6. Test complete workflows, not individual function calls
```

## DATA
### Simplified Fixture Usage
```python
# Use git_repo for clean start scenarios
def test_new_project_workflow(self, git_repo):
    repo, project_dir = git_repo
    
# Use git_repo_with_files for modification scenarios  
def test_modify_files_workflow(self, git_repo_with_files):
    repo, project_dir = git_repo_with_files
    
# Create complex states inline when needed
def test_complex_workflow(self, git_repo):
    repo, project_dir = git_repo
    # Create complex state inline rather than fixture
    setup_complex_repository_state(project_dir)
```

### Return Value Verification
```python
# Function return types to verify
is_git_repository() -> bool
get_staged_changes() -> list[str] 
get_unstaged_changes() -> dict[str, list[str]]
get_full_status() -> dict[str, list[str]]
stage_specific_files() -> bool
stage_all_changes() -> bool
commit_staged_files() -> CommitResult
commit_all_changes() -> CommitResult
```

## LLM Prompt for Implementation
```
Based on the Git Operations Test Simplification Summary and Step 1 structure, implement Step 2 to create the 20 core workflow tests in test_git_workflows.py.

Create realistic git workflow tests that:
- Test complete operations from start to finish
- Use real git repositories (no mocking)
- Use simplified fixtures (git_repo, git_repo_with_files)
- Create complex states inline rather than complex fixtures
- Verify both function return values AND actual git repository state
- Cover the main workflows your application uses

Each test should:
1. Set up realistic file scenarios using simple fixtures + inline setup
2. Call multiple git_operations functions in sequence 
3. Verify return values match expectations
4. Check actual git repository state using GitPython
5. Use descriptive assertions with clear error messages

Focus on integration testing of workflows rather than unit testing of individual functions.

Example test structure:
```python
def test_new_project_to_first_commit(self, git_repo):
    \"\"\"Test complete new project setup workflow.\"\"\"
    repo, project_dir = git_repo
    
    # Create project files inline
    files = {
        "main.py": "print('hello')",
        "README.md": "# Project",
        "src/utils.py": "def helper(): pass"
    }
    
    for path, content in files.items():
        file_path = project_dir / path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
    
    # Test workflow: check status → stage files → commit
    status = get_full_status(project_dir)
    assert len(status["untracked"]) == 3
    assert status["staged"] == []
    
    result = stage_all_changes(project_dir)
    assert result is True
    
    staged = get_staged_changes(project_dir) 
    assert len(staged) == 3
    assert all(filename in str(staged) for filename in files.keys())
    
    commit_result = commit_staged_files("Initial commit", project_dir)
    assert commit_result["success"] is True
    assert len(commit_result["commit_hash"]) == 7
    
    # Verify git state
    assert len(list(repo.iter_commits())) == 1
    final_status = get_full_status(project_dir)
    assert final_status == {"staged": [], "modified": [], "untracked": []}
```
```

## Verification
- [ ] All 20 workflow tests pass
- [ ] Tests complete in under 2 seconds total
- [ ] No GitPython mocking used anywhere
- [ ] Each test verifies both return values and git state
- [ ] Tests cover realistic application workflows
- [ ] Line coverage of git_operations.py maintained at 90%+
- [ ] Complex states created inline, not in fixtures
