# Step 3: Implement Public API Functions

## Context
Following the summary and Steps 1-2, implement the main public API functions that provide the core functionality: getting incomplete tasks and checking task completion status.

## WHERE: File Paths and Module Structure
```
src/mcp_coder/workflow_utils/task_tracker.py     # Add: Public API functions  
tests/workflow_utils/test_task_tracker.py        # Add: Public API tests
```

## WHAT: Main Functions with Signatures
```python
def get_incomplete_tasks(folder_path: str = "pr_info") -> list[str]:
    """Get list of incomplete task names from Implementation Steps section.
    
    Args:
        folder_path: Path to folder containing TASK_TRACKER.md (default: "pr_info")
        
    Returns:
        List of incomplete task names
        
    Raises:
        TaskTrackerFileNotFoundError: If TASK_TRACKER.md not found
        TaskTrackerSectionNotFoundError: If Implementation Steps section not found
    """

def is_task_done(task_name: str, folder_path: str = "pr_info") -> bool:
    """Check if specific task is marked as complete.
    
    Args:
        task_name: Name of task to check (case-insensitive exact match)
        folder_path: Path to folder containing TASK_TRACKER.md (default: "pr_info")
        
    Returns:
        True if task is complete ([x] or [X]), False if incomplete or not found
        
    Raises:
        TaskTrackerFileNotFoundError: If TASK_TRACKER.md not found
        TaskTrackerSectionNotFoundError: If Implementation Steps section not found
    """

def _normalize_task_name(name: str) -> str:
    """Normalize task name for case-insensitive exact matching."""
```

## HOW: Integration Points
- Build on all functions from Steps 1-2
- Use `_read_task_tracker()`, `_find_implementation_section()`, `_parse_task_lines()`
- Add case-insensitive exact matching for task name comparison
- Follow existing workflow_utils patterns for default parameters
- Raise specific exceptions instead of returning empty results

## ALGORITHM: Public API Logic
```python
# get_incomplete_tasks():
# 1. Read TASK_TRACKER.md from folder_path
# 2. Find Implementation Steps section
# 3. Parse all tasks and filter incomplete ones (is_complete=False)
# 4. Return list of clean task names

# is_task_done():
# 1. Get all tasks from Implementation Steps section
# 2. Normalize input task_name for comparison (lowercase, strip whitespace)
# 3. Find exact matching task using case-insensitive comparison
# 4. Return completion status or False if not found
```

## DATA: Return Values and Data Structures
```python
# get_incomplete_tasks() returns
list[str]: [
    "Setup project structure",
    "Implement core parser", 
    "Add integration tests"
]
# Raises exceptions for missing file/section

# is_task_done() returns
bool: True   # Task found and marked complete [x]/[X]
bool: False  # Task incomplete [ ] or not found
# Raises exceptions for missing file/section

# _normalize_task_name() returns  
str: "setup project structure"  # Lowercase, normalized spacing
```

## Tests to Implement (TDD)
```python
# Main API tests in tests/utils/test_task_tracker.py
def test_get_incomplete_tasks_basic():
    """Test getting incomplete tasks from valid tracker file."""

def test_get_incomplete_tasks_empty_file():
    """Test behavior with missing or empty tracker file."""

def test_is_task_done_complete_task():
    """Test checking completion status of completed task."""

def test_is_task_done_incomplete_task():
    """Test checking completion status of incomplete task."""

# Simple integration tests in tests/test_integration_task_tracker.py
def test_imports_work():
    """Test importing task tracker functions from utils package."""

def test_basic_functionality():
    """Test basic end-to-end functionality."""

def test_missing_file_raises_error():
    """Test error handling for missing tracker file."""
```

## LLM Prompt for Implementation
```
Implement Step 3 of the task tracker parser following pr_info/steps/summary.md and building on Steps 1-2.

Create the main public API functions:

1. **Write Comprehensive Tests First (TDD)**:
   - Test get_incomplete_tasks() with various scenarios (normal, empty, missing file)
   - Test is_task_done() with exact and fuzzy task name matching
   - Test error handling: missing files, malformed content, edge cases
   - Create realistic test data that mirrors actual TASK_TRACKER.md files

2. **Implement get_incomplete_tasks()**:
   - Use all helper functions from Steps 1-2
   - Read file → Find section → Parse tasks → Filter incomplete
   - Return clean task names as simple string list
   - Handle errors gracefully (return empty list, don't raise exceptions)

3. **Implement is_task_done()**:
   - Parse all tasks (complete and incomplete)
   - Implement fuzzy task name matching for user convenience
   - Normalize task names for comparison (case-insensitive, whitespace-tolerant)
   - Return False for non-existent tasks (don't raise exceptions)

4. **Add Fuzzy Matching**:
   - Implement _normalize_task_name() for consistent comparisons
   - Support partial task name matches (e.g., "Setup" matches "Setup project structure")
   - Handle case variations and extra whitespace

5. **Simple Integration Testing**:
   - Create simple integration tests (3 focused tests)
   - Verify imports work from mcp_coder.utils package
   - Test basic end-to-end functionality with simple test data
   - Test basic error handling (missing file)

Keep implementation simple, robust, and user-friendly. Focus on graceful error handling and intuitive behavior.
Keep integration tests minimal and focused on core functionality.
```
