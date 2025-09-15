# Step 4: Implement File Staging Functions (TDD)

## WHERE
- **File**: `src/mcp_coder/utils/git_operations.py` (extend existing)
- **Test File**: `tests/utils/test_git_operations.py` (extend existing)

## WHAT
Add functions to stage files for commit operations.

### Main Functions
```python
def stage_specific_files(files: list[Path], project_dir: Path) -> bool
def stage_all_changes(project_dir: Path) -> bool
```

## HOW
### Integration Points
- Extend existing git_operations.py module
- Use existing `is_git_repository()` for validation
- Use `get_files_to_commit()` from Step 3 for validation
- Import `git.Repo` for staging operations

### Dependencies
- GitPython `Repo.index.add()` for staging operations
- Path validation and conversion utilities

## ALGORITHM
### stage_specific_files()
```
1. Validate project_dir is git repository 
2. Convert file paths to relative paths from project_dir
3. Filter files to only existing files within project
4. Use repo.index.add() to stage specified files
5. Return True if staging successful, False otherwise
```

### stage_all_changes()
```
1. Validate project_dir is git repository
2. Get current status using get_unstaged_changes()
3. Combine modified and untracked files for staging
4. Call stage_specific_files() with all unstaged files
5. Return True if staging successful, False otherwise
```

## DATA
### Function Signatures
```python
def stage_specific_files(files: list[Path], project_dir: Path) -> bool
    # files: List of file paths to stage (absolute or relative)
    # project_dir: Git repository root directory
    # Returns: True if all files staged successfully

def stage_all_changes(project_dir: Path) -> bool  
    # project_dir: Git repository root directory
    # Returns: True if all changes staged successfully
```

### Error Handling
- Return False if not a git repository
- Handle FileNotFoundError for missing files
- Handle GitCommandError for staging failures
- Log appropriate warnings/errors

### Validation Rules
- Files must exist and be within project directory
- Skip files that are already staged (no error)
- Handle both absolute and relative file paths

---

## LLM PROMPT
```
Reference the summary in pr_info/steps/summary.md and decisions in pr_info/steps/Decisions.md for context.

Implement Step 4 using Test-Driven Development: First write comprehensive tests for file staging functions, then implement the functions.

Write tests for:
1. stage_specific_files() - test staging specific files, non-existent files, files outside repo
2. stage_all_changes() - test staging all changes, empty repo, already staged files  
3. Error cases - not a git repo, git staging errors, permission issues
4. Edge cases - relative vs absolute paths, already staged files

Then implement the functions in src/mcp_coder/utils/git_operations.py:
- stage_specific_files(files: list[Path], project_dir: Path) -> bool
- stage_all_changes(project_dir: Path) -> bool

Key requirements:
- Use existing is_git_repository() for validation
- Use get_unstaged_changes() to check current status  
- stage_all_changes() should call stage_specific_files() as wrapper
- Use GitPython's repo.index.add() for staging
- Handle both relative and absolute file paths
- Return False for errors, True for success
- Follow existing error handling and logging patterns

Ensure all tests pass and functions integrate properly with existing code.
```
