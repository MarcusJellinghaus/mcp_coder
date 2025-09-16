# Step 2: Implement Core Integration Workflow Tests

## Objective  
Implement the 25 core workflow tests in `test_git_integration.py` that cover the main git operations your application uses, focusing on complete end-to-end scenarios without mocking.

## WHERE
- File: `tests/utils/test_git_integration.py`
- Module: `mcp_coder.utils.git_operations`

## WHAT
Implement 25 test methods that cover complete workflows:

### Primary Workflows (10 tests)
```python
def test_new_project_workflow(self, git_repo)
def test_modify_existing_files_workflow(self, git_repo_with_commits)  
def test_add_new_files_workflow(self, git_repo_with_commits)
def test_delete_files_workflow(self, git_repo_with_commits)
def test_mixed_operations_workflow(self, git_repo_with_commits)
def test_staging_specific_files_only(self, git_repo)
def test_staging_all_changes_workflow(self, git_repo)
def test_commit_staged_files_workflow(self, git_repo)
def test_commit_all_changes_workflow(self, git_repo)
def test_git_status_tracking_workflow(self, git_repo)
```

### Advanced Workflows (10 tests)
```python
def test_multiple_commit_cycle_workflow(self, git_repo)
def test_partial_staging_workflow(self, git_repo_with_commits)
def test_subdirectory_operations_workflow(self, git_repo)
def test_file_move_operations_workflow(self, git_repo_with_commits)
def test_empty_repository_first_commit(self, git_repo)
def test_mixed_file_types_workflow(self, git_repo)
def test_commit_message_variations_workflow(self, git_repo)
def test_staging_after_commit_workflow(self, git_repo_with_commits)
def test_status_consistency_workflow(self, git_repo)
def test_repository_state_transitions(self, git_repo)
```

### Complex Scenarios (5 tests)
```python
def test_realistic_development_cycle(self, git_repo)
def test_feature_branch_simulation(self, git_repo)
def test_project_structure_creation(self, git_repo)
def test_refactoring_workflow_simulation(self, git_repo_with_commits)
def test_comprehensive_git_operations(self, git_repo)
```

## HOW
### Integration Points
- Import all functions from `mcp_coder.utils.git_operations`
- Use `git.Repo` directly for setup/verification only
- Use pytest fixtures for repository creation
- Assert on return values and git repository state
- No mocking of GitPython calls

### Test Pattern
```python
def test_workflow_name(self, fixture):
    # Setup: Create files/modify state
    # Action: Call your git operation functions
    # Verify: Check return values AND git repo state
    # Assert: Multiple assertions on outcomes
```

## ALGORITHM
```
1. Create test files and directories in git repository
2. Call git_operations functions in realistic sequence
3. Verify function return values match expectations
4. Check actual git repository state using GitPython
5. Assert on both wrapper function behavior and git state
6. Test complete workflows, not individual function calls
```

## DATA
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

### Repository State Checks
```python
# Git state verification using GitPython
repo.index.diff("HEAD")  # Staged changes
repo.index.diff(None)    # Working directory changes  
repo.untracked_files     # Untracked files
list(repo.iter_commits()) # Commit history
```

## LLM Prompt for Implementation
```
Based on the Git Operations Test Simplification Summary and Step 1 structure, implement Step 2 to create the 25 core integration workflow tests in test_git_integration.py.

Create realistic git workflow tests that:
- Test complete operations from start to finish
- Use real git repositories (no mocking)
- Verify both function return values AND actual git repository state
- Cover the main workflows your application uses
- Follow the test method signatures defined in Step 1

Each test should:
1. Set up realistic file scenarios using the git_repo fixtures
2. Call multiple git_operations functions in sequence 
3. Verify return values match expectations
4. Check actual git repository state using GitPython
5. Use descriptive assertions with clear error messages

Focus on integration testing of workflows rather than unit testing of individual functions. Test scenarios that your application actually encounters.

Example test structure:
```python
def test_new_project_workflow(self, git_repo):
    \"\"\"Test complete new project setup workflow.\"\"\"
    repo, project_dir = git_repo
    
    # Create project files
    (project_dir / "main.py").write_text("print('hello')")
    (project_dir / "README.md").write_text("# Project")
    
    # Test workflow: check status → stage files → commit
    status = get_full_status(project_dir)
    assert len(status["untracked"]) == 2
    
    result = stage_all_changes(project_dir)
    assert result is True
    
    staged = get_staged_changes(project_dir) 
    assert "main.py" in staged and "README.md" in staged
    
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
- [ ] All 25 integration tests pass
- [ ] Tests complete in under 5 seconds total
- [ ] No GitPython mocking used anywhere
- [ ] Each test verifies both return values and git state
- [ ] Tests cover realistic application workflows
- [ ] Line coverage of git_operations.py maintained at 90%+
