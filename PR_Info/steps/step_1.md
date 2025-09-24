# Step 1: Setup Data Models and Test Infrastructure

## Context
Following the summary in `pr_info/steps/summary.md`, establish the foundation for task tracker parsing by creating data models and comprehensive test infrastructure using Test-Driven Development.

## WHERE: File Paths and Module Structure
```
src/mcp_coder/utils/task_tracker.py     # New: Core implementation module
tests/utils/test_task_tracker.py        # New: Unit tests
tests/utils/test_data/                  # New: Test markdown files
├── valid_tracker.md                   # Sample valid TASK_TRACKER.md
├── no_implementation_section.md       # Edge case testing
└── empty_tasks.md                     # Edge case testing
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

def _read_task_tracker(folder_path: str) -> Optional[str]:
    """Read TASK_TRACKER.md file content safely."""
    
# Test helper functions
def create_test_tracker_content(tasks: list[tuple[str, bool]]) -> str:
    """Helper to generate test markdown content."""
```

## HOW: Integration Points
- Import `dataclasses.dataclass` for simple data modeling
- Import `pathlib.Path` for file operations
- Import `typing.Optional` for None-safe returns
- Follow existing project patterns in `src/mcp_coder/utils/`
- Use pytest fixtures from existing `tests/conftest.py`

## ALGORITHM: Core Setup Logic
```python
# 1. Define TaskInfo dataclass with name, completion status, line number
# 2. Create _read_task_tracker() for safe file reading
# 3. Setup test data directory with sample markdown files
# 4. Create test helpers for generating markdown content
# 5. Write initial tests for data model validation
```

## DATA: Return Values and Data Structures
```python
# TaskInfo instances
TaskInfo(name="Setup project structure", is_complete=False, line_number=15)
TaskInfo(name="Implement parser", is_complete=True, line_number=16)

# File reading function
Optional[str]: "# Task Status Tracker\n\n## Implementation Steps\n..." 
Optional[str]: None  # When file doesn't exist

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
    """Test handling of missing TASK_TRACKER.md file."""

def test_create_test_tracker_content():
    """Test helper function for generating test content."""
```

## LLM Prompt for Implementation
```
Implement Step 1 of the task tracker parser following the summary in pr_info/steps/summary.md.

Create the foundation for task tracking functionality:

1. **Setup Module Structure (TDD Approach)**:
   - Create src/mcp_coder/utils/task_tracker.py with proper imports
   - Create tests/utils/test_task_tracker.py for unit testing
   - Create tests/utils/test_data/ directory for test markdown files

2. **Define Data Model**:
   - Implement TaskInfo dataclass with name, is_complete, line_number fields
   - Add proper type hints and docstrings

3. **Implement File Reading**:
   - Write _read_task_tracker() function for safe file operations
   - Handle missing files gracefully (return None)
   - Use pathlib.Path for cross-platform file handling

4. **Create Test Infrastructure**:
   - Write comprehensive tests for TaskInfo creation
   - Test file reading with existing and missing files
   - Create sample test data files for various scenarios
   - Add test helper function for generating markdown content

5. **Follow Project Patterns**:
   - Use existing conftest.py fixtures where applicable
   - Follow naming conventions from other utils modules
   - Add proper error handling and logging if needed

Focus on Test-Driven Development: write tests first, then implement minimal code to make them pass. Keep implementation simple and focused on the core requirements.
```
