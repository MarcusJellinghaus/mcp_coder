# Step 3: Implement Git Status Functions (TDD)

## WHERE
- **File**: `src/mcp_coder/utils/git_operations.py` (extend existing)
- **Test File**: `tests/utils/test_git_operations.py` (extend existing)

## WHAT
Add functions to check git repository status with structured information.

### Main Functions
```python
def get_staged_changes(project_dir: Path) -> list[str]
def get_unstaged_changes(project_dir: Path) -> dict[str, list[str]]
```

## HOW
### Integration Points
- Extend existing git_operations.py module
- Use existing `is_git_repository()` for validation
- Import `git.Repo` (already available from Step 1)
- Add to module exports in `__init__.py` files

### Dependencies
- GitPython `Repo.git` commands for status operations
- Existing logging patterns from module

## ALGORITHM
### get_staged_changes()
```
1. Validate project_dir is git repository using is_git_repository()
2. Create Repo instance and get staged files
3. Parse staged files using repo.git.diff("--cached", "--name-only")
4. Return list of staged file paths
```

### get_unstaged_changes()
```
1. Validate project_dir is git repository using is_git_repository()
2. Create Repo instance and get status information
3. Parse modified files using repo.git.diff("--name-only") 
4. Parse untracked files using repo.untracked_files
5. Return structured dict: {"modified": [...], "untracked": [...]}
```

## DATA
### Return Values
```python
# get_staged_changes() returns:
list[str]  # Files currently staged for commit

# get_unstaged_changes() returns:
{
    "modified": list[str],    # Modified but unstaged files
    "untracked": list[str]   # New files not tracked by git
}
```

### Error Handling
- Return empty dict if not a git repository
- Handle GitCommandError gracefully
- Log warnings for git operation failures

---

## LLM PROMPT
```
Reference the summary in pr_info/steps/summary.md and decisions in pr_info/steps/Decisions.md for context.

Implement Step 3 using Test-Driven Development: First write comprehensive tests for git status functions, then implement the functions.

Write tests for:
1. get_staged_changes() - test with staged files, no staged files, empty repo
2. get_unstaged_changes() - test with modified files, untracked files, combinations, empty repo
3. Error cases - not a git repo, git command errors

Then implement the functions in src/mcp_coder/utils/git_operations.py:
- get_staged_changes(project_dir: Path) -> list[str]
- get_unstaged_changes(project_dir: Path) -> dict[str, list[str]]

Key requirements:
- Use existing is_git_repository() for validation
- Use GitPython's Repo.git commands for status operations
- Return structured data as per Decisions.md
- Handle errors gracefully with proper logging
- Follow existing code patterns in the module
- Return empty list/dict for non-git directories

Ensure all tests pass before proceeding.
```
