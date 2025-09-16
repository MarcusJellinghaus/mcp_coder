# Step 1: Write Failing Tests for Git Diff Functionality

## LLM Prompt
```
I'm implementing a git diff function as described in pr_info/steps/summary.md. This is Step 1 - write failing tests for the new `get_git_diff_for_commit()` function.

Requirements:
- Follow TDD approach - write tests that will initially fail
- Add tests to existing `tests/utils/test_git_workflows.py` 
- Use existing `@pytest.mark.git_integration` marker
- Leverage existing fixtures (`git_repo`, `git_repo_with_files`)
- Keep tests focused on core functionality only

Please implement the failing tests first, then I'll implement the actual function in the next step.
```

## WHERE
- **File**: `tests/utils/test_git_workflows.py`
- **Location**: Add new test methods to existing `TestGitWorkflows` class

## WHAT
Add test methods:
```python
@pytest.mark.git_integration
def test_get_git_diff_for_commit_basic(self, git_repo: tuple[Repo, Path]) -> None:
    """Test basic git diff generation with mixed file states."""

@pytest.mark.git_integration  
def test_get_git_diff_for_commit_edge_cases(self, git_repo: tuple[Repo, Path]) -> None:
    """Test edge cases: no changes, not git repo, etc."""
```

## HOW
- **Import**: Add `get_git_diff_for_commit` to existing import statement
- **Test structure**: Follow existing test patterns in the file
- **Fixtures**: Use existing `git_repo` and `git_repo_with_files` fixtures

## ALGORITHM
```
1. Create test files (staged, unstaged, untracked)
2. Call get_git_diff_for_commit(project_dir)
3. Assert diff contains all file changes
4. Assert no git state was modified
5. Test edge cases (empty repo, no changes)
```

## DATA
**Test expects function signature**:
```python
def get_git_diff_for_commit(project_dir: Path) -> Optional[str]
```

**Return value**: String containing unified diff output or None on error

**Test assertions**:
- Diff string contains staged file changes
- Diff string contains unstaged file changes  
- Diff string contains untracked files as new files
- Function returns None for invalid git repository
- Git repository state unchanged after function call
