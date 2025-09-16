# Step 4: Integration and Polish

## Overview
Final integration testing, performance validation, and documentation completion.

## Tests to Add/Update
**File**: `tests/utils/test_git_workflows.py`

### Integration Test Cases
```python
@pytest.mark.git_integration
def test_get_git_diff_integration_with_existing_functions(self, git_repo_with_files: tuple[Repo, Path]) -> None:
    """Test integration with existing git_operations functions."""
    # Use get_full_status, stage_specific_files, etc.
    # Call get_git_diff_for_commit at various stages
    # Verify diff output matches git repository state
    
@pytest.mark.git_integration
def test_get_git_diff_complete_workflow(self, git_repo: tuple[Repo, Path]) -> None:
    """Test complete workflow from empty repo to multiple commits."""
    # Simulate real development workflow
    # Add files, stage some, modify others
    # Verify diff output at each stage
    
@pytest.mark.git_integration
def test_get_git_diff_performance_basic(self, git_repo: tuple[Repo, Path]) -> None:
    """Basic performance test with reasonable file count."""
    # Create ~50 files with various states
    # Measure execution time (should be < 5 seconds)
    # Verify all files appear in output correctly
```

## Implementation Polish
**File**: `src/mcp_coder/utils/git_operations.py`

### Final Documentation Update
```python
def get_git_diff_for_commit(project_dir: Path) -> Optional[str]:
    """
    Generate comprehensive git diff without modifying repository state.
    
    Shows staged, unstaged, and untracked files in unified diff format
    suitable for LLM analysis and commit message generation.
    
    Args:
        project_dir: Path to the project directory containing git repository
        
    Returns:
        str: Unified diff format with sections for staged changes, unstaged 
             changes, and untracked files. Each section uses format:
             === SECTION NAME ===
             [diff content]
             
             Returns empty string if no changes detected.
        None: If error occurs (invalid repository, git command failure, etc.)
        
    Example:
        >>> diff_output = get_git_diff_for_commit(Path("/path/to/repo"))
        >>> if diff_output is not None:
        ...     print("Changes detected" if diff_output else "No changes")
        
    Note:
        - Uses read-only git operations, never modifies repository state
        - Binary files handled naturally by git (shows "Binary files differ")
        - Continues processing even if individual git operations fail
        - Empty repositories (no commits) supported
    """
```

### Import Statement Update
Add to existing import in test file:
```python
from mcp_coder.utils.git_operations import (
    # ... existing imports ...
    get_git_diff_for_commit,  # Add this line
)
```

## Validation Checklist

### Functional Validation
- [ ] Function generates correct diff output for all file states
- [ ] Output format matches LLM-friendly specification
- [ ] Returns empty string for clean repositories
- [ ] Returns None for error conditions
- [ ] No git repository state modifications occur

### Integration Validation  
- [ ] All existing git_operations tests still pass
- [ ] Function works with existing git operation workflows
- [ ] No conflicts with existing codebase patterns
- [ ] Proper logging follows established patterns

### Performance Validation
- [ ] Reasonable performance with typical repository sizes
- [ ] No memory leaks or resource issues
- [ ] Handles large repositories gracefully

### Documentation Validation
- [ ] Comprehensive docstring with examples
- [ ] Clear return value documentation
- [ ] Usage examples provided
- [ ] Edge cases documented

## Final Notes
- Run complete test suite: `pytest tests/utils/test_git_workflows.py -v`
- Verify no regressions: `pytest tests/utils/ -v`
- Check code quality follows existing patterns
- Ensure logging output is appropriate for production use

## Success Criteria
- [ ] All tests pass (new and existing)
- [ ] Function ready for production use
- [ ] Documentation complete and accurate
- [ ] Integration verified with existing codebase
- [ ] Performance acceptable for intended use cases
