# Step 1: Basic Diff Functionality

## Overview
Implement core diff functionality for staged and unstaged changes with basic tests.

## Tests to Implement
**File**: `tests/utils/test_git_workflows.py`

### Test Cases
```python
@pytest.mark.git_integration
def test_get_git_diff_for_commit_basic_functionality(self, git_repo: tuple[Repo, Path]) -> None:
    """Test basic diff generation with staged and unstaged changes."""
    # Create test files
    # Modify files and stage some changes
    # Call get_git_diff_for_commit()
    # Assert output contains staged and unstaged sections
    # Assert correct diff format with --unified=5 --no-prefix

@pytest.mark.git_integration  
def test_get_git_diff_for_commit_no_changes(self, git_repo: tuple[Repo, Path]) -> None:
    """Test function returns empty string when no changes exist."""
    # Clean repository with no changes
    # Call get_git_diff_for_commit()
    # Assert returns empty string ""

@pytest.mark.git_integration
def test_get_git_diff_for_commit_invalid_repository(self, tmp_path: Path) -> None:
    """Test function returns None for invalid git repository."""
    # Call on non-git directory
    # Assert returns None
```

## Implementation to Add
**File**: `src/mcp_coder/utils/git_operations.py`

### Function Signature
```python
def get_git_diff_for_commit(project_dir: Path) -> Optional[str]:
    """
    Generate comprehensive git diff without modifying repository state.
    
    Shows staged, unstaged, and untracked files in unified diff format.
    
    Args:
        project_dir: Path to the project directory containing git repository
        
    Returns:
        str: Unified diff format showing all changes. Returns empty string 
             if no changes detected.
        None: If error occurs (invalid repository, git command failure, etc.)
    """
```

### Core Implementation
```python
def get_git_diff_for_commit(project_dir: Path) -> Optional[str]:
    """Generate comprehensive git diff without modifying repository state."""
    logger.debug("Generating git diff for: %s", project_dir)
    
    if not is_git_repository(project_dir):
        logger.error("Not a git repository: %s", project_dir)
        return None
    
    try:
        repo = Repo(project_dir, search_parent_directories=False)
        
        # Generate diff sections
        staged_diff = repo.git.diff("--cached", "--unified=5", "--no-prefix")
        unstaged_diff = repo.git.diff("--unified=5", "--no-prefix")
        
        # Use helper function to format output
        return _format_diff_sections(staged_diff, unstaged_diff, "")
        
    except (InvalidGitRepositoryError, GitCommandError) as e:
        logger.error("Git error generating diff: %s", e)
        return None
    except Exception as e:
        logger.error("Unexpected error generating diff: %s", e)
        return None


def _format_diff_sections(staged_diff: str, unstaged_diff: str, untracked_diff: str) -> str:
    """Format diff sections with appropriate headers."""
    sections = []
    
    if staged_diff.strip():
        sections.append(f"=== STAGED CHANGES ===\\n{staged_diff}")
    
    if unstaged_diff.strip():
        sections.append(f"=== UNSTAGED CHANGES ===\\n{unstaged_diff}")
    
    if untracked_diff.strip():
        sections.append(f"=== UNTRACKED FILES ===\\n{untracked_diff}")
    
    return "\\n\\n".join(sections)
```

## Success Criteria
- [ ] Function handles basic staged/unstaged diffs
- [ ] Returns empty string for clean repositories  
- [ ] Returns None for invalid repositories
- [ ] Uses correct git command parameters
- [ ] All new tests pass
- [ ] No existing tests broken

## Notes
- Untracked diff parameter is empty string in this step (added in Step 2)
- Focus on core functionality and basic error handling
- Helper function structure ready for Step 2 extension
