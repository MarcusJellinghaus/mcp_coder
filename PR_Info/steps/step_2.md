# Step 2: Untracked Files Support

## Overview
Add support for untracked files in diff output with comprehensive tests.

## Tests to Add
**File**: `tests/utils/test_git_workflows.py`

### Test Cases
```python
@pytest.mark.git_integration
def test_get_git_diff_for_commit_with_untracked_files(self, git_repo: tuple[Repo, Path]) -> None:
    """Test diff generation includes untracked files."""
    # Create mix of staged, unstaged, and untracked files
    # Call get_git_diff_for_commit()
    # Assert output contains all three sections
    # Assert untracked files shown as new files (diff from /dev/null)

@pytest.mark.git_integration
def test_get_git_diff_for_commit_untracked_only(self, git_repo: tuple[Repo, Path]) -> None:
    """Test diff with only untracked files."""
    # Clean repo + add untracked files
    # Assert only untracked section appears

@pytest.mark.git_integration
def test_get_git_diff_for_commit_binary_files(self, git_repo: tuple[Repo, Path]) -> None:
    """Test handling of binary files in diff."""
    # Add binary file (untracked)
    # Assert git's binary file message appears naturally
```

## Implementation Updates
**File**: `src/mcp_coder/utils/git_operations.py`

### Add Untracked File Helper
```python
def _generate_untracked_diff(repo: Repo, project_dir: Path) -> str:
    """Generate diff for untracked files using git diff --no-index."""
    untracked_files = repo.untracked_files
    if not untracked_files:
        return ""
    
    untracked_diffs = []
    for file_path in untracked_files:
        try:
            # Generate diff from /dev/null to show as new file
            diff = repo.git.diff("--no-index", "--unified=5", "--no-prefix", 
                               "/dev/null", file_path)
            untracked_diffs.append(diff)
        except GitCommandError:
            # Skip files that can't be diffed (e.g., binary files might still show basic info)
            continue
    
    return "\\n".join(untracked_diffs)
```

### Update Main Function
```python
def get_git_diff_for_commit(project_dir: Path) -> Optional[str]:
    """Generate comprehensive git diff without modifying repository state."""
    logger.debug("Generating git diff for: %s", project_dir)
    
    if not is_git_repository(project_dir):
        logger.error("Not a git repository: %s", project_dir)
        return None
    
    try:
        repo = Repo(project_dir, search_parent_directories=False)
        
        # Generate all diff sections
        staged_diff = repo.git.diff("--cached", "--unified=5", "--no-prefix")
        unstaged_diff = repo.git.diff("--unified=5", "--no-prefix")
        untracked_diff = _generate_untracked_diff(repo, project_dir)
        
        return _format_diff_sections(staged_diff, unstaged_diff, untracked_diff)
        
    except (InvalidGitRepositoryError, GitCommandError) as e:
        logger.error("Git error generating diff: %s", e)
        return None
    except Exception as e:
        logger.error("Unexpected error generating diff: %s", e)
        return None
```

## Success Criteria
- [x] Function includes untracked files in diff output
- [x] Untracked files shown as new files (diff from /dev/null)
- [x] Binary files handled naturally by git
- [x] All three sections (staged/unstaged/untracked) work together
- [x] All new tests pass
- [x] No regressions in Step 1 functionality

## Notes
- Use `git diff --no-index /dev/null filename` for untracked files
- Let git handle binary file detection naturally
- Skip files that can't be diffed (continue on GitCommandError)
