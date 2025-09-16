# Step 4: Add Comprehensive Error Handling and Edge Cases

## LLM Prompt
```
I'm implementing a git diff function as described in pr_info/steps/summary.md. This is Step 4 - add comprehensive error handling and edge cases.

The core diff generation from Step 3 should be working. Now I need to:
- Add proper exception handling for GitCommandError and other git errors
- Handle edge cases like empty repositories, no changes, binary files
- Ensure robust error logging following existing patterns
- Make sure function never crashes and always returns valid data

Refine the error handling to make the function production-ready.
```

## WHERE
- **File**: `src/mcp_coder/utils/git_operations.py`
- **Location**: Add try/catch blocks and edge case handling in `get_git_diff_for_commit()`

## WHAT
Add comprehensive error handling:
```python
try:
    repo = Repo(project_dir, search_parent_directories=False)
    
    # Handle empty repository case
    if not repo.heads:
        logger.debug("Empty repository with no commits")
        return handle_empty_repository(repo, project_dir)
    
    # Generate diffs with error handling for each section
    # ... existing diff logic with individual try/catch
    
except (InvalidGitRepositoryError, GitCommandError) as e:
    logger.error("Git error generating diff: %s", e)
    return None
except Exception as e:
    logger.error("Unexpected error generating diff: %s", e)
    return None
```

## HOW
- **Exception types**: Handle `GitCommandError`, `InvalidGitRepositoryError`
- **Edge cases**: Empty repos, no changes, binary files, permission errors
- **Logging**: Use existing logger patterns (`logger.debug`, `logger.error`)
- **Graceful degradation**: Return None or empty string for recoverable errors

## ALGORITHM
```
1. Wrap all git operations in try/catch blocks
2. Check for empty repository (no commits) case
3. Handle each diff section with individual error handling
4. Log specific errors for debugging
5. Return None only for unrecoverable errors
```

## DATA
**Error cases to handle**:
- `InvalidGitRepositoryError` - not a git repository
- `GitCommandError` - git command execution failed
- Empty repository - no commits exist yet
- No changes - all diffs are empty
- Permission errors - cannot read git objects

**Return values**:
- `None` - unrecoverable error (invalid repo, permission denied)
- `""` (empty string) - no changes to show
- `str` - valid diff content

**Logging levels**:
- `logger.debug` - normal operations, empty results
- `logger.error` - actual errors that prevent function completion
- Include error details in log messages for debugging
