# Step 1: Setup Data Models and Test Infrastructure

## Context
Following the summary in `pr_info/steps/summary.md`, establish the foundation for task tracker parsing by creating data models and comprehensive test infrastructure using Test-Driven Development.

## WHERE: File Paths and Module Structure
```
src/mcp_coder/workflow_utils/task_tracker.py     # New: Core implementation module
tests/workflow_utils/test_task_tracker.py        # New: Unit tests
tests/workflow_utils/test_data/                  # New: Test markdown files
├── valid_tracker.md                          # Sample valid TASK_TRACKER.md
├── missing_section.md                       # Edge case testing
└── empty_tracker.md                         # Edge case testing
```

## WHAT: Main Functions with Signatures
```python
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

@dataclass
class TaskInfo:
    """Simple data model for task information."""
    name: str
    is_complete: bool
    line_number: int
    indentation_level: int  # 0 for top-level, 1 for first indent, etc.

class TaskTrackerError(Exception):
    """Base exception for task tracker issues"""

class TaskTrackerFileNotFoundError(TaskTrackerError):
    """TASK_TRACKER.md file not found"""

class TaskTrackerSectionNotFoundError(TaskTrackerError):
    """Implementation Steps section not found"""

def _read_task_tracker(folder_path: str) -> str:
    """Read TASK_TRACKER.md file content, raise exception if missing."""
    
# Test helper functions
def create_test_tracker_content(tasks: list[tuple[str, bool]]) -> str:
    """Helper to generate test markdown content."""
```

## HOW: Integration Points
- Import `dataclasses.dataclass` for simple data modeling
- Import `pathlib.Path` for file operations
- Create new `workflow_utils` package following existing project patterns
- Setup exception hierarchy for clean error handling
- Use pytest for testing following existing patterns

## ALGORITHM: Core Setup Logic
```python
# 1. Create workflow_utils package with __init__.py
# 2. Define TaskInfo dataclass with name, completion, line_number, indentation_level
# 3. Setup exception hierarchy (TaskTrackerError base + specific exceptions)
# 4. Create _read_task_tracker() with proper exception handling
# 5. Setup test data directory with 5 essential test markdown files
# 6. Create test helpers for generating markdown content
# 7. Write initial tests for data model and file reading
```

## DATA: Return Values and Data Structures
```python
# TaskInfo instances
TaskInfo(name="Setup project structure", is_complete=False, line_number=15, indentation_level=0)
TaskInfo(name="Implement parser", is_complete=True, line_number=16, indentation_level=1)

# File reading function
str: "# Task Status Tracker\n\n## Implementation Steps\n..." 
# Raises TaskTrackerFileNotFoundError when file doesn't exist

# Test helper
str: "### Implementation Steps\n- [ ] Task 1\n- [x] Task 2\n"
```

## Tests to Implement (TDD)
```python
def test_task_info_creation():
    """Test TaskInfo dataclass creation and attributes."""

def test_read_task_tracker_existing_file():
    """Test reading existing TASK_TRACKER.md file."""

def test_read_task_tracker_missing_file():
    """Test TaskTrackerFileNotFoundError for missing TASK_TRACKER.md file."""

def test_create_test_tracker_content():
    """Test helper function for generating test content."""
```

## LLM Prompt for Implementation
```
Implement Step 1 of the task tracker parser following the summary in pr_info/steps/summary.md.

Create the foundation for task tracking functionality:

1. **Setup New Package Structure**:
   - Create src/mcp_coder/workflow_utils/ directory
   - Create src/mcp_coder/workflow_utils/__init__.py 
   - Create src/mcp_coder/workflow_utils/task_tracker.py with proper imports
   - Create tests/workflow_utils/ directory structure
   - Create tests/workflow_utils/test_task_tracker.py for unit testing

2. **Define Data Model & Exceptions**:
   - Implement TaskInfo dataclass with name, is_complete, line_number, indentation_level fields
   - Create exception hierarchy: TaskTrackerError, TaskTrackerFileNotFoundError, TaskTrackerSectionNotFoundError
   - Add proper type hints and docstrings

3. **Implement File Reading**:
   - Write _read_task_tracker() function with exception handling
   - Raise TaskTrackerFileNotFoundError for missing files
   - Use pathlib.Path for cross-platform file handling

4. **Create Test Infrastructure**:
   - Write comprehensive tests for TaskInfo creation and exceptions
   - Test file reading with existing files and proper exception handling
   - Create 5 essential test data files: valid_tracker.md, missing_section.md, empty_tracker.md, real_world_tracker.md, case_insensitive.md
   - Add test helper function for generating markdown content

5. **Follow Project Patterns**:
   - Use existing project conventions for package structure
   - Add proper error handling with specific exceptions
   - Focus on clean, explicit error handling over graceful fallbacks

Focus on Test-Driven Development: write tests first, then implement minimal code to make them pass. Keep implementation simple and focused on the core requirements.
```
