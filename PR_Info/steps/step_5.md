# Step 5: Implement Git Commit Functions (TDD)

## WHERE
- **File**: `src/mcp_coder/utils/git_operations.py` (extend existing)
- **Test File**: `tests/utils/test_git_operations.py` (extend existing)

## WHAT
Add core commit functionality for creating git commits.

### Main Functions
```python
def commit_staged_files(message: str, project_dir: Path) -> CommitResult
def commit_all_changes(message: str, project_dir: Path) -> CommitResult
```

## HOW
### Integration Points
- Extend existing git_operations.py module  
- Use `is_git_repository()`, `stage_files()`, `get_files_to_commit()` from previous steps
- Import `git.Repo` for commit operations
- Return detailed commit information

### Dependencies
- GitPython `Repo.index.commit()` for commit operations
- Validation functions from previous steps

## ALGORITHM
### commit_staged_files()
```
1. Validate project_dir is git repository
2. Check if there are staged files using get_staged_changes()
3. Validate commit message is not empty/None
4. Execute repo.index.commit(message) 
5. Return simple commit result (success, hash, error)
```

### commit_all_changes()
```
1. Validate project_dir is git repository and commit message
2. Stage all changes using stage_all_changes()
3. Check staging was successful
4. Execute commit_staged_files() to create commit
5. Return commit result
```

## DATA
### Return Values
```python
# Both functions return simple CommitResult:
{
    "success": bool,                    # True if commit successful
    "commit_hash": str | None,          # Git commit SHA (first 7 chars)
    "error": str | None                # Error message if failed
}
```

### Validation Rules
- commit_message must be non-empty string
- Must be in a git repository
- Must have staged changes to commit
- Files (if specified) must exist and be stageable

### Error Scenarios
- Not a git repository → success=False, error="Not a git repository"
- Empty commit message → success=False, error="Commit message required"  
- No staged changes → success=False, error="No changes to commit"
- Git commit error → success=False, error=<git error message>

---

## LLM PROMPT  
```
Reference the summary in pr_info/steps/summary.md and decisions in pr_info/steps/Decisions.md for context.

Implement Step 5 using Test-Driven Development: First write comprehensive tests for git commit functions, then implement the functions.

Write tests for:
1. commit_staged_files() - test successful commit, no staged files, empty message
2. commit_files() - test with specific files, with all files, empty repo
3. Error cases - not git repo, invalid commit message, git commit failures  
4. Edge cases - empty commits, large commit messages, special characters

Then implement the functions in src/mcp_coder/utils/git_operations.py:
- commit_staged_files(message: str, project_dir: Path) -> CommitResult
- commit_all_changes(message: str, project_dir: Path) -> CommitResult

Key requirements:
- Use functions from previous steps (is_git_repository, stage_all_changes, get_staged_changes)
- commit_all_changes() should call stage_all_changes() then commit_staged_files()
- Use GitPython's repo.index.commit() for actual commits
- Return simple commit information as per Decisions.md
- Handle all error cases gracefully with informative messages
- Follow existing logging and error handling patterns

Ensure all tests pass and integration with existing functions works correctly.
```
