# Task Tracker Parser Implementation Summary

## Overview
Implement a simple, focused task tracker parser to extract incomplete implementation tasks from `TASK_TRACKER.md` files. This enables automated workflow management and task status checking for development processes.

## Core Requirements
- Parse markdown files with GitHub-style task checkboxes (`[ ]`, `[x]`, `[X]`)
- Extract incomplete tasks from "Implementation Steps" section only
- Exclude tasks from "Pull Request" section
- Provide task completion status checking functionality
- Support configurable folder paths with "pr_info" default
- Clean error handling with specific exception types
- Simple case-insensitive exact task name matching

## Architecture & Design Changes

### New Module Structure
```
src/mcp_coder/workflow_utils/
├── task_tracker.py          # New: Task tracker parsing functionality
└── __init__.py             # New: Workflow utils exports

tests/workflow_utils/
├── test_task_tracker.py     # New: Unit tests for task tracker
├── test_data/              # New: Test markdown files
└── __init__.py             # New: Test package
```

### Core Components

#### 1. Data Models (Minimal)
```python
@dataclass
class TaskInfo:
    name: str
    is_complete: bool
    line_number: int
    indentation_level: int  # 0 for top-level, 1 for first indent, etc.
```

#### 2. Public API (2 functions only)
```python
def get_incomplete_tasks(folder_path: str = "pr_info") -> list[str]:
    """Get list of incomplete task names from Implementation Steps section"""

def is_task_done(task_name: str, folder_path: str = "pr_info") -> bool:
    """Check if specific task is marked as complete (case-insensitive exact match)"""
```

#### 3. Internal Helpers (Simple parsing)
```python
def _read_task_tracker(folder_path: str) -> str:
    """Read TASK_TRACKER.md content, raise TaskTrackerFileNotFoundError if missing"""

def _find_implementation_section(content: str) -> str:
    """Extract Implementation Steps section, raise TaskTrackerSectionNotFoundError if missing"""

def _parse_task_lines(section_content: str) -> list[TaskInfo]:
    """Parse task lines with [ ]/[x] markers, track indentation levels"""

# Additional helpers extracted during implementation if needed:
# _clean_task_name(), _is_task_line(), etc.
```

#### 4. Exception Types (Clean error handling)
```python
class TaskTrackerError(Exception):
    """Base exception for task tracker issues"""

class TaskTrackerFileNotFoundError(TaskTrackerError):
    """TASK_TRACKER.md file not found"""

class TaskTrackerSectionNotFoundError(TaskTrackerError):
    """Implementation Steps section not found"""
```

### Integration Points
- Add exports to `src/mcp_coder/workflow_utils/__init__.py`
- Follow existing project patterns for error handling
- Use standard library only (no external dependencies)
- Integrate with existing test infrastructure

### Design Principles Applied
- **KISS**: Only essential functionality, no over-engineering
- **Single Responsibility**: Each function has one clear purpose
- **Fail Fast**: Clear error messages for missing files/sections
- **Test-Driven**: Comprehensive test coverage for all scenarios

### Error Handling Strategy
- Explicit exceptions for different failure conditions
- Clear error messages for missing files/sections
- Robust section parsing (case-insensitive headers)
- Simple case-insensitive exact task name matching

## Benefits
- Enables automated task progress tracking
- Supports development workflow automation
- Simple API that's easy to use and maintain
- Integrates seamlessly with existing codebase patterns
- Follows established project conventions

## Implementation Approach
1. **Test-First Development**: Write comprehensive tests before implementation
2. **Incremental Development**: Build functionality step-by-step
3. **Clean Integration**: Follow existing project structure and patterns
4. **Minimal Dependencies**: Use only standard library functions
