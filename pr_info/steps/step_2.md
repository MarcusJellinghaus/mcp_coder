# Step 2: Add Repository Cleanup Functions with Tests

## WHERE
- **Test File**: `tests/test_create_pr.py` (new file)
- **Implementation**: `workflows/create_PR.py` (new file - utility functions only)

## WHAT
Add simple file operation functions for repository cleanup.

### Main Function Signatures
```python
def delete_steps_directory(project_dir: Path) -> bool
def truncate_task_tracker(project_dir: Path) -> bool
```

## HOW

### Integration Points
- **New Module**: Create `workflows/create_PR.py` with utility functions
- **Dependencies**: Standard library only (`shutil`, `pathlib`)
- **Error Handling**: Boolean returns with logging (follow implement.py patterns)
- **Testing**: Mock file operations for safety

### Function Behaviors
- `delete_steps_directory()`: Remove entire `pr_info/steps/` directory
- `truncate_task_tracker()`: Keep only content before "## Tasks" section
- Both return True on success, False on failure
- Log operations and errors clearly

## ALGORITHM (Pseudocode)

### delete_steps_directory()
```
1. Check if pr_info/steps/ exists
2. Use shutil.rmtree() to remove directory
3. Log operation and return success status
```

### truncate_task_tracker()  
```
1. Read pr_info/TASK_TRACKER.md content
2. Find "## Tasks" section header
3. Keep only content before that section
4. Write truncated content back to file
5. Return success status
```

## LLM Prompt

### Context
You are implementing Step 2 of the Create Pull Request Workflow. Review the summary document in `pr_info/steps/summary.md` for full context. This step builds on Step 1 (git diff functionality).

### Task
Create utility functions for repository cleanup operations in a new `workflows/create_PR.py` file.

### Requirements
1. **TDD Approach**: Write tests first in `tests/test_create_pr.py`
2. **Follow Existing Patterns**: Study `workflows/implement.py` for:
   - Function organization and structure
   - Error handling with boolean returns
   - Logging patterns and messages
   - Constants and helper function style
3. **Test Coverage**: Include tests for:
   - Successful directory deletion
   - Missing directories (should not fail)
   - Task tracker truncation
   - Missing task tracker file handling
   - File permission errors
4. **Safety**: Use temporary directories in tests

### Expected Output
- New test file with mock-based tests
- Two simple utility functions (~15 lines each)
- Proper error handling and logging
- Clear function documentation

### Success Criteria
- All tests pass with proper mocking
- Functions handle edge cases gracefully
- Clear logging for all operations
- Follows existing code style and patterns