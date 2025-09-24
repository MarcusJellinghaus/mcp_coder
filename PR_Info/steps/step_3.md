# Step 3: Implement Task Status Checking

## Context
Following the summary and previous steps, implement the task completion status checking functionality.

## WHERE: File Paths and Module Structure
```
src/mcp_coder/workflow_utils/task_tracker.py  # Add status checking function
tests/workflow_utils/test_task_tracker.py     # Add status checking tests
```

## WHAT: Main Functions with Signatures
```python
def is_task_done(task_name: str, pull_request_info_folder: str = "PR_Info") -> bool:
    """Check if specific task is marked as complete ([x] or [X])"""

def _get_all_tasks(pull_request_info_folder: str) -> list[Task]:
    """Internal helper to get all tasks (complete and incomplete)"""
```

## HOW: Integration Points
- Reuse existing parsing functions from Step 2
- Add case-insensitive task name matching
- Use existing file reading patterns
- Handle both `[x]` and `[X]` completion markers

## ALGORITHM: Task Status Logic  
```python
# 1. Read TASK_TRACKER.md and find Implementation Steps section
# 2. Parse all tasks (complete and incomplete) 
# 3. Search for task by name (case-insensitive, fuzzy matching)
# 4. Return completion status (True if [x]/[X], False if [ ])
# 5. Return False if task not found
```

## DATA: Return Values and Data Structures
```python
# is_task_done() returns
bool: True  # Task is complete [x] or [X]
bool: False # Task is incomplete [ ] or not found

# _get_all_tasks() returns
list[Task]: [
    Task("Setup project", is_complete=True),
    Task("Implement parser", is_complete=False)
]
```

## LLM Prompt for Implementation
```
Implement Step 3 of the task tracker parser following pr_info/steps/summary.md.

Building on Steps 1-2, add task status checking functionality:

1. Write tests first (TDD approach):
   - Test checking status of completed tasks [x] and [X]
   - Test checking status of incomplete tasks [ ]  
   - Test handling of non-existent tasks
   - Test case-insensitive task name matching

2. Implement the functions:
   - _get_all_tasks(): Extend parsing to include completed tasks
   - is_task_done(): Main status checking function with fuzzy name matching

3. Extend existing parsing logic:
   - Modify _parse_tasks_from_section() to handle [x]/[X] markers
   - Add task name normalization for matching

4. Handle edge cases: missing tasks, case variations, partial name matches

Keep implementation simple and reuse existing parsing infrastructure.
```
