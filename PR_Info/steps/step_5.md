# Step 5: Update Git Commit and Push Operations Functions

## Overview
Modify the git commit and push functions to use the `project_dir` parameter instead of hardcoded `Path.cwd()`. This completes the git operations migration and ensures all git actions work with the specified project directory.

## WHERE
- **File**: `workflows/implement.py`
- **Functions**: `commit_changes()`, `push_changes()`

## WHAT

### Modified Function Signatures
```python
def commit_changes(project_dir: Path) -> bool
def push_changes(project_dir: Path) -> bool
```

### Core Changes
- Replace `Path.cwd()` with `project_dir` parameter in git operations
- Update `generate_commit_message_with_llm()` call to use `project_dir`
- Update `commit_all_changes()` call to use `project_dir`
- Update `git_push()` call to use `project_dir`

## HOW

### Integration Points
- **commit**: `generate_commit_message_with_llm(project_dir)`
- **commit**: `commit_all_changes(commit_message, project_dir)`  
- **push**: `git_push(project_dir)`
- **Function calls**: Update calls in `process_single_task()` to pass `project_dir`

### Git Operations Chain
```python
# Old approach
project_dir = Path.cwd()
generate_commit_message_with_llm(project_dir)

# New approach  
generate_commit_message_with_llm(project_dir)  # project_dir from parameter
```

## ALGORITHM

### commit_changes() Update (5-6 steps)
```pseudocode
1. Add project_dir: Path parameter to function signature
2. Remove project_dir = Path.cwd() assignment
3. Call generate_commit_message_with_llm(project_dir) with parameter
4. Call commit_all_changes(commit_message, project_dir) with parameter
5. Handle errors and log results as before
6. Return success/failure boolean
```

### push_changes() Update
```pseudocode
1. Add project_dir: Path parameter to function signature
2. Remove project_dir = Path.cwd() assignment  
3. Call git_push(project_dir) with parameter
4. Handle errors and log results as before
5. Return success/failure boolean
```

## DATA

### Function Parameters
```python
# Both functions receive:
project_dir: Path  # Absolute path to project root directory
```

### Git Operation Calls
```python
# Commit operations
success, commit_message, error = generate_commit_message_with_llm(project_dir)
commit_result = commit_all_changes(commit_message, project_dir)

# Push operations
push_result = git_push(project_dir)
```

### Return Values (unchanged)
```python
commit_changes() -> bool
push_changes() -> bool
```

## Function Call Updates

### Updated calls in process_single_task()
```python
def process_single_task(project_dir: Path) -> bool:
    # ... task processing ...
    
    # Step 7: Commit changes
    if not commit_changes(project_dir):           # Pass project_dir
        return False
    
    # Step 8: Push changes to remote
    if not push_changes(project_dir):             # Pass project_dir
        return False
```

## Error Handling (unchanged)

### Exception handling remains the same
```python
# Both functions maintain existing error handling:
try:
    # git operations
except Exception as e:
    logger.error(f"Error ...: {e}")
    return False
```

## LLM PROMPT

Please read the **summary.md** file and implement **Step 5** exactly as specified.

**Context**: We've updated argument parsing (Step 2), git operations (Step 3), and task processing (Step 4). Now we need to complete the git operations by updating commit and push functions.

**Your Task**: Modify these functions in `workflows/implement.py`:

1. **`commit_changes(project_dir: Path)`** - Add project_dir parameter and update git commit operations
2. **`push_changes(project_dir: Path)`** - Add project_dir parameter and update git push operations  
3. **Update calls in `process_single_task()`** - Pass `project_dir` to both commit and push functions

**Specific Requirements**:
- Add `project_dir: Path` parameter to both function signatures
- Remove `project_dir = Path.cwd()` lines from both functions
- Update `generate_commit_message_with_llm(project_dir)` call
- Update `commit_all_changes(commit_message, project_dir)` call
- Update `git_push(project_dir)` call
- Update function calls in `process_single_task()` to pass `project_dir`
- Maintain all existing error handling and logging
- Keep return types and behavior unchanged

**Before/After Pattern**:
```python
# Before:
def commit_changes() -> bool:
    project_dir = Path.cwd()
    generate_commit_message_with_llm(project_dir)

# After:  
def commit_changes(project_dir: Path) -> bool:
    generate_commit_message_with_llm(project_dir)
```

This completes the migration - all functions will now work with the specified project directory instead of assuming current working directory.
