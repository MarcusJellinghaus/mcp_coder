# Step 3: Update Git Operations Functions for Project Directory

## Overview
Modify all functions that perform git operations to accept and use the `project_dir` parameter instead of hardcoded `Path.cwd()`. This includes git status checking, prerequisite validation, and path resolution for git-related operations.

## WHERE
- **File**: `workflows/implement.py`
- **Functions**: `check_git_clean()`, `check_prerequisites()`, `has_implementation_tasks()`, `prepare_task_tracker()`

## WHAT

### Modified Function Signatures
```python
def check_git_clean(project_dir: Path) -> bool
def check_prerequisites(project_dir: Path) -> bool  
def has_implementation_tasks(project_dir: Path) -> bool
def prepare_task_tracker(project_dir: Path) -> bool
```

### Core Changes
- Replace all `Path.cwd()` calls with `project_dir` parameter
- Update git operation calls to use `project_dir` 
- Fix path resolution for `PR_INFO_DIR` relative to `project_dir`
- Update task tracker path operations

## HOW

### Integration Points
- **git_operations**: `is_working_directory_clean(project_dir)`, `get_full_status(project_dir)`
- **task_tracker**: `get_incomplete_tasks(str(project_dir / PR_INFO_DIR))`
- **Path operations**: All paths relative to `project_dir` instead of current working directory
- **Function calls**: Update all callers to pass `project_dir`

### Path Resolution Changes
```python
# Old approach
task_tracker_path = Path(PR_INFO_DIR) / "TASK_TRACKER.md"
steps_dir = Path(PR_INFO_DIR) / "steps"

# New approach  
task_tracker_path = project_dir / PR_INFO_DIR / "TASK_TRACKER.md"
steps_dir = project_dir / PR_INFO_DIR / "steps"
```

## ALGORITHM

### Function Update Pattern (5-6 steps)
```pseudocode
1. Add project_dir: Path parameter to function signature
2. Replace Path.cwd() calls with project_dir usage
3. Update all path operations to be relative to project_dir
4. Update calls to external functions with project_dir parameter
5. Update function documentation to reflect new parameter
6. Test path resolution works correctly
```

### Git Operations Flow
```pseudocode
1. check_git_clean(project_dir) -> is_working_directory_clean(project_dir)
2. check_prerequisites(project_dir) -> validate git_dir = project_dir / ".git"
3. has_implementation_tasks(project_dir) -> get_incomplete_tasks(project_dir / PR_INFO_DIR)
4. prepare_task_tracker(project_dir) -> all operations relative to project_dir
```

## DATA

### Function Parameters
```python
# All modified functions receive:
project_dir: Path  # Absolute path to project root directory
```

### Path Operations
```python
# Git repository validation
git_dir: Path = project_dir / ".git"

# Task tracker operations  
pr_info_dir: str = str(project_dir / PR_INFO_DIR)
task_tracker_path: Path = project_dir / PR_INFO_DIR / "TASK_TRACKER.md"
steps_dir: Path = project_dir / PR_INFO_DIR / "steps"
```

### Return Values (unchanged)
```python
check_git_clean() -> bool
check_prerequisites() -> bool  
has_implementation_tasks() -> bool
prepare_task_tracker() -> bool
```

## Function Call Updates

### Updated call sites in main()
```python
def main() -> None:
    # ... argument parsing ...
    
    if not check_git_clean(project_dir):          # Pass project_dir
        sys.exit(1)
    
    if not check_prerequisites(project_dir):      # Pass project_dir
        sys.exit(1)
    
    if not prepare_task_tracker(project_dir):     # Pass project_dir
        sys.exit(1)
```

## LLM PROMPT

Please read the **summary.md** file and implement **Step 3** exactly as specified.

**Context**: We've added `--project-dir` parameter parsing (Step 2). Now we need to update git-related functions to use the project directory instead of current working directory.

**Your Task**: Modify these functions in `workflows/implement.py`:

1. **`check_git_clean(project_dir: Path)`** - Update to use `is_working_directory_clean(project_dir)` instead of `Path.cwd()`
2. **`check_prerequisites(project_dir: Path)`** - Update git directory check to `project_dir / ".git"`
3. **`has_implementation_tasks(project_dir: Path)`** - Update to use `project_dir / PR_INFO_DIR` for task tracker operations
4. **`prepare_task_tracker(project_dir: Path)`** - Update all path operations and git calls to use `project_dir`
5. **Update function calls in `main()`** - Pass `project_dir` to all modified functions

**Specific Requirements**:
- Add `project_dir: Path` parameter to all four function signatures
- Replace `Path.cwd()` with `project_dir` throughout these functions
- Update path operations: `project_dir / PR_INFO_DIR / "TASK_TRACKER.md"`, etc.
- Update `get_incomplete_tasks()` call to use `str(project_dir / PR_INFO_DIR)`
- Update `get_full_status()` and `commit_all_changes()` calls to use `project_dir`
- Update function calls in `main()` to pass the resolved `project_dir`

**Path Resolution Pattern**:
```python
# Old: Path(PR_INFO_DIR) / "file"
# New: project_dir / PR_INFO_DIR / "file"
```

This step should maintain all existing functionality while making it work with any project directory.
