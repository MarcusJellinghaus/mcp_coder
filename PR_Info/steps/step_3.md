# Step 3: Implement Public API Functions

## Context
Following the summary and Steps 1-2, implement the main public API functions that provide the core functionality: getting incomplete tasks and checking task completion status.

## WHERE: File Paths and Module Structure
```
src/mcp_coder/utils/task_tracker.py     # Add: Public API functions  
tests/utils/test_task_tracker.py        # Add: Public API tests
tests/utils/test_data/                  # Add: Integration test files
├── real_world_tracker.md              # Realistic TASK_TRACKER.md example
└── edge_case_tracker.md               # Various edge cases combined
```

## WHAT: Main Functions with Signatures
```python
def get_incomplete_tasks(folder_path: str = "PR_Info") -> list[str]:
    """Get list of incomplete task names from Implementation Steps section.
    
    Args:
        folder_path: Path to folder containing TASK_TRACKER.md (default: "PR_Info")
        
    Returns:
        List of incomplete task names, empty list if file/section not found
    """

def is_task_done(task_name: str, folder_path: str = "PR_Info") -> bool:
    """Check if specific task is marked as complete.
    
    Args:
        task_name: Name of task to check (supports partial matching)
        folder_path: Path to folder containing TASK_TRACKER.md (default: "PR_Info")
        
    Returns:
        True if task is complete ([x] or [X]), False otherwise
    """

def _normalize_task_name(name: str) -> str:
    """Normalize task name for fuzzy matching."""
```

## HOW: Integration Points
- Build on all functions from Steps 1-2
- Use `_read_task_tracker()`, `_find_implementation_section()`, `_parse_task_lines()`
- Add fuzzy string matching for task name comparison
- Follow existing utils module patterns for default parameters
- Handle errors gracefully (return empty lists/False instead of exceptions)

## ALGORITHM: Public API Logic
```python
# get_incomplete_tasks():
# 1. Read TASK_TRACKER.md from folder_path
# 2. Find Implementation Steps section
# 3. Parse all tasks and filter incomplete ones (is_complete=False)
# 4. Return list of clean task names

# is_task_done():
# 1. Get all tasks from Implementation Steps section
# 2. Normalize input task_name for comparison
# 3. Find matching task using fuzzy name matching
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
list[str]: []  # When no incomplete tasks or file not found

# is_task_done() returns
bool: True   # Task found and marked complete [x]/[X]
bool: False  # Task incomplete [ ] or not found

# _normalize_task_name() returns  
str: "setup project structure"  # Lowercase, normalized spacing
```

## Tests to Implement (TDD)
```python
def test_get_incomplete_tasks_basic():
    """Test getting incomplete tasks from valid tracker file."""

def test_get_incomplete_tasks_empty_file():
    """Test behavior with missing or empty tracker file."""

def test_get_incomplete_tasks_no_incomplete():
    """Test when all tasks are complete."""

def test_is_task_done_complete_task():
    """Test checking completion status of completed task."""

def test_is_task_done_incomplete_task():
    """Test checking completion status of incomplete task."""

def test_is_task_done_fuzzy_matching():
    """Test partial/fuzzy task name matching."""

def test_is_task_done_nonexistent_task():
    """Test behavior when task doesn't exist."""

def test_integration_with_real_tracker():
    """End-to-end test with realistic TASK_TRACKER.md file."""
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

5. **Integration Testing**:
   - Test end-to-end workflow with realistic TASK_TRACKER.md files
   - Verify integration with existing project structure
   - Test with actual PR_Info folder structure

Keep implementation simple, robust, and user-friendly. Focus on graceful error handling and intuitive behavior.
```
