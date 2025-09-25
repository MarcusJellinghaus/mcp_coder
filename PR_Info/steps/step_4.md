# Step 4: Update Task Processing and File Operations Functions

## Overview
Modify the remaining functions that handle task processing, file operations, and conversations to accept and use the `project_dir` parameter. This completes the migration from hardcoded current working directory usage.

## WHERE
- **File**: `workflows/implement.py`
- **Functions**: `get_next_task()`, `save_conversation()`, `run_formatters()`, `process_single_task()`

## WHAT

### Modified Function Signatures
```python
def get_next_task(project_dir: Path) -> Optional[str]
def save_conversation(project_dir: Path, content: str, step_num: int) -> None
def run_formatters(project_dir: Path) -> bool
def process_single_task(project_dir: Path) -> bool
```

### Core Changes
- Update task tracker operations to use `project_dir`
- Fix conversation directory path resolution 
- Update formatter operations to use `project_dir` as root
- Update all internal function calls to pass `project_dir`

## HOW

### Integration Points
- **task_tracker**: `get_incomplete_tasks(str(project_dir / PR_INFO_DIR))`
- **formatters**: `format_code(project_dir, formatters=["black", "isort"])`
- **Path operations**: Conversation directory relative to `project_dir`
- **Function calls**: All internal calls must pass `project_dir` parameter

### Path Resolution Updates
```python
# Old approach
conversations_dir = Path(CONVERSATIONS_DIR)
pr_info_dir = PR_INFO_DIR

# New approach
conversations_dir = project_dir / CONVERSATIONS_DIR  
pr_info_dir = str(project_dir / PR_INFO_DIR)
```

## ALGORITHM

### save_conversation() Update (5-6 steps)
```pseudocode
1. Add project_dir parameter to function signature
2. Update conversations_dir = project_dir / CONVERSATIONS_DIR
3. Create directory relative to project_dir if needed
4. Generate filename and full path relative to project_dir
5. Write conversation content to resolved path
6. Log the absolute path where conversation was saved
```

### run_formatters() Update
```pseudocode
1. Add project_dir parameter to function signature  
2. Call format_code(project_dir, formatters=["black", "isort"])
3. Remove hardcoded Path.cwd() usage
4. Return success/failure status as before
```

## DATA

### Function Parameters
```python
# All modified functions receive:
project_dir: Path  # Absolute path to project root

# save_conversation() specific:
content: str       # Conversation content (unchanged)
step_num: int     # Step number (unchanged)
# Note: project_dir is now first parameter
```

### Path Operations
```python
# Conversation directory
conversations_dir: Path = project_dir / CONVERSATIONS_DIR

# Task tracker operations
pr_info_dir: str = str(project_dir / PR_INFO_DIR)

# Formatter root directory
formatter_root: Path = project_dir
```

### Return Values (unchanged)
```python
get_next_task() -> Optional[str]
save_conversation() -> None
run_formatters() -> bool  
process_single_task() -> bool
```

## Function Call Chain Updates

### process_single_task() internal calls
```python
def process_single_task(project_dir: Path) -> bool:
    next_task = get_next_task(project_dir)                    # Pass project_dir
    # ... LLM processing ...
    save_conversation(project_dir, conversation_content, step_num)  # Pass project_dir
    run_formatters(project_dir)                               # Pass project_dir
    # ... other operations ...
```

### Updated call site in main()
```python
def main() -> None:
    # ... setup ...
    while True:
        success = process_single_task(project_dir)            # Pass project_dir
        if not success:
            break
```

## Constants Update

### CONVERSATIONS_DIR path resolution
```python
# Update usage from:
CONVERSATIONS_DIR = f"{PR_INFO_DIR}/.conversations"

# To be used as:  
conversations_dir = project_dir / PR_INFO_DIR / ".conversations"
```

## LLM PROMPT

Please read the **summary.md** file and implement **Step 4** exactly as specified.

**Context**: We've updated argument parsing (Step 2) and git operations (Step 3). Now we need to complete the migration by updating task processing and file operations functions.

**Your Task**: Modify these functions in `workflows/implement.py`:

1. **`get_next_task(project_dir: Path)`** - Update task tracker operations to use `project_dir / PR_INFO_DIR`
2. **`save_conversation(project_dir: Path, content, step_num)`** - Update conversation directory to `project_dir / CONVERSATIONS_DIR`
3. **`run_formatters(project_dir: Path)`** - Update to use `format_code(project_dir, ...)` instead of `Path.cwd()`
4. **`process_single_task(project_dir: Path)`** - Update all internal function calls to pass `project_dir`
5. **Update function calls in `main()`** - Pass `project_dir` to `process_single_task()`

**Specific Requirements**:
- Add `project_dir: Path` parameter to all function signatures
- Update `get_incomplete_tasks()` call: `str(project_dir / PR_INFO_DIR)`
- Fix conversation directory path: `project_dir / PR_INFO_DIR / ".conversations"`
- Update `format_code()` call to use `project_dir` as root directory
- Chain `project_dir` parameter through all function calls
- Maintain all existing functionality and return types

**Path Resolution Pattern**:
```python
# Old: Path(CONVERSATIONS_DIR)
# New: project_dir / PR_INFO_DIR / ".conversations"
```

After this step, the workflow should work with any project directory specified via `--project-dir` parameter.
