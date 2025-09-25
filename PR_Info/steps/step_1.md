# Step 1: Write Tests for Branch Name Functions

## Objective
Implement comprehensive tests for the three branch name functions following TDD methodology.

**Note**: These tests provide complete coverage - no additional edge case testing needed (Step 5 removed).

## WHERE
- **File**: `tests/utils/test_git_workflows.py`  
- **Test Class**: Add `TestGitBranchOperations` class within existing file
- **Integration**: Add to existing `@pytest.mark.git_integration` test suite

## WHAT
### Test Methods to Implement
```python
def test_get_current_branch_name_success(self, git_repo: tuple[Repo, Path]) -> None
def test_get_current_branch_name_invalid_repo(self, tmp_path: Path) -> None  
def test_get_current_branch_name_detached_head(self, git_repo: tuple[Repo, Path]) -> None

def test_get_main_branch_name_with_main(self, git_repo: tuple[Repo, Path]) -> None
def test_get_main_branch_name_with_master(self, git_repo: tuple[Repo, Path]) -> None  
def test_get_main_branch_name_invalid_repo(self, tmp_path: Path) -> None

def test_get_parent_branch_name_returns_main(self, git_repo: tuple[Repo, Path]) -> None
def test_get_parent_branch_name_invalid_repo(self, tmp_path: Path) -> None
def test_get_parent_branch_name_no_main_branch(self, git_repo: tuple[Repo, Path]) -> None
```

## HOW
### Integration Points
- Import the functions (will fail initially): 
```python
from mcp_coder.utils.git_operations import (
    get_current_branch_name,
    get_main_branch_name, 
    get_parent_branch_name,
    # ... existing imports
)
```
- Use existing fixtures: `git_repo`, `git_repo_with_files`, `tmp_path`
- Follow existing test patterns in the file

## ALGORITHM
### Test Logic Pseudocode
```
1. Test current branch returns expected branch name
2. Test invalid repo returns None  
3. Test detached HEAD returns None
4. Test main branch detection with main/master branches
5. Test parent branch returns main branch name
```

## DATA
### Test Assertions Expected
- **Success cases**: `assert result == "expected_branch_name"`
- **Error cases**: `assert result is None`
- **Type validation**: `assert isinstance(result, str) or result is None`

## LLM Prompt for Implementation
```
Based on the summary.md, implement Step 1 by adding a TestGitBranchOperations class to tests/utils/test_git_workflows.py. 

Write comprehensive tests for three functions that don't exist yet:
- get_current_branch_name(project_dir: Path) -> Optional[str]  
- get_main_branch_name(project_dir: Path) -> Optional[str]
- get_parent_branch_name(project_dir: Path) -> Optional[str]

Follow the existing test patterns in the file, use existing fixtures, and ensure all tests will initially fail since the functions don't exist yet. This is proper TDD - write failing tests first.

The tests should cover success cases, invalid repo cases, and edge cases like detached HEAD and missing main/master branches.
```
