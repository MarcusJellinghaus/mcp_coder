# Step 3: Error Handling and Edge Cases

## Overview
Add robust error handling and edge case support with comprehensive tests.

## Tests to Add
**File**: `tests/utils/test_git_workflows.py`

### Test Cases
```python
@pytest.mark.git_integration
def test_get_git_diff_for_commit_empty_repository(self, git_repo: tuple[Repo, Path]) -> None:
    """Test handling of empty repository (no commits)."""
    # Empty repository with untracked files
    # Should handle gracefully and show untracked files
    
@pytest.mark.git_integration
def test_get_git_diff_for_commit_git_command_errors(self, git_repo: tuple[Repo, Path]) -> None:
    """Test handling of git command failures."""
    # Test scenarios that might cause git commands to fail
    # Verify function returns None with appropriate logging

@pytest.mark.git_integration
def test_get_git_diff_for_commit_unicode_filenames(self, git_repo: tuple[Repo, Path]) -> None:
    """Test handling of unicode filenames."""
    # Create files with unicode names
    # Verify diff generation works correctly

@pytest.mark.git_integration  
def test_get_git_diff_for_commit_large_files(self, git_repo: tuple[Repo, Path]) -> None:
    """Test handling of large text files."""
    # Create large text files
    # Verify performance is acceptable (basic check)
```

## Implementation Updates
**File**: `src/mcp_coder/utils/git_operations.py`

### Enhanced Error Handling
```python
def get_git_diff_for_commit(project_dir: Path) -> Optional[str]:
    """Generate comprehensive git diff without modifying repository state."""
    logger.debug("Generating git diff for: %s", project_dir)
    
    if not is_git_repository(project_dir):
        logger.error("Not a git repository: %s", project_dir)
        return None
    
    try:
        repo = Repo(project_dir, search_parent_directories=False)
        
        # Simple check for empty repository (KISS approach)
        has_commits = True
        try:
            list(repo.iter_commits(max_count=1))
        except:
            has_commits = False
            logger.debug("Empty repository detected, showing untracked files only")
        
        # Generate diff sections with individual error handling
        staged_diff = ""
        unstaged_diff = ""
        
        if has_commits:
            try:
                staged_diff = repo.git.diff("--cached", "--unified=5", "--no-prefix")
            except GitCommandError as e:
                logger.warning("Failed to get staged diff: %s", e)
            
            try:
                unstaged_diff = repo.git.diff("--unified=5", "--no-prefix")
            except GitCommandError as e:
                logger.warning("Failed to get unstaged diff: %s", e)
        
        # Always try to get untracked files
        untracked_diff = _generate_untracked_diff(repo, project_dir)
        
        return _format_diff_sections(staged_diff, unstaged_diff, untracked_diff)
        
    except (InvalidGitRepositoryError, GitCommandError) as e:
        logger.error("Git error generating diff: %s", e)
        return None
    except Exception as e:
        logger.error("Unexpected error generating diff: %s", e)
        return None


def _generate_untracked_diff(repo: Repo, project_dir: Path) -> str:
    """Generate diff for untracked files using git diff --no-index."""
    try:
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
                # Skip individual files that can't be diffed
                logger.debug("Skipping untracked file that couldn't be diffed: %s", file_path)
                continue
        
        return "\\n".join(untracked_diffs)
        
    except Exception as e:
        logger.warning("Error generating untracked file diff: %s", e)
        return ""
```

## Success Criteria
- [ ] Empty repositories handled gracefully
- [ ] Individual git command failures don't crash entire operation
- [ ] Unicode filenames supported
- [ ] Large files don't cause performance issues
- [ ] Comprehensive error logging
- [ ] All edge case tests pass
- [ ] No regressions in previous functionality

## Notes
- Use KISS approach for empty repository detection
- Individual error handling for each git operation allows partial success
- Log warnings for non-critical failures, errors for complete failures
- Continue processing even if some operations fail
