# Step 2: Implement Section Parsing and Task Extraction

## Context
Following the summary and Step 1 foundation, implement the core markdown parsing functionality to find the "Implementation Steps" section and extract task information using Test-Driven Development.

## WHERE: File Paths and Module Structure
```
src/mcp_coder/workflow_utils/task_tracker.py     # Add: Section parsing functions
tests/workflow_utils/test_task_tracker.py        # Add: Section parsing tests
tests/workflow_utils/test_data/                  # Add: More complex test files
├── real_world_tracker.md                      # Realistic TASK_TRACKER.md example
└── case_insensitive.md                      # Test case variations in headers
```

## WHAT: Main Functions with Signatures
```python
import re
from typing import Tuple

def _find_implementation_section(content: str) -> str:
    """Find and extract Implementation Steps section, raise TaskTrackerSectionNotFoundError if missing."""

def _parse_task_lines(section_content: str) -> list[TaskInfo]:
    """Parse individual task lines and extract TaskInfo objects with indentation levels."""

# Additional helpers extracted if needed during implementation:
# def _clean_task_name(raw_line: str) -> str:
# def _is_task_line(line: str) -> Tuple[bool, bool]:
```

## HOW: Integration Points
- Import `re` for regex pattern matching if needed
- Use existing `TaskInfo` dataclass from Step 1  
- Build on `_read_task_tracker()` function from Step 1
- Raise TaskTrackerSectionNotFoundError for missing sections
- Follow existing error handling patterns in workflow_utils

## ALGORITHM: Section Parsing Logic
```python
# 1. Split content into sections by markdown headers (## or ###)
# 2. Find section with "Implementation Steps" in title (case-insensitive)
# 3. Stop at "Pull Request" section if encountered  
# 4. Parse each line for task patterns: "- [ ]" or "- [x]"/"- [X]"
# 5. Track indentation levels (count leading spaces/tabs)
# 6. Clean task names by removing prefixes and extra whitespace
# 7. Return list of TaskInfo objects with line numbers and indentation
```

## DATA: Return Values and Data Structures
```python
# _find_implementation_section() returns
str: "- [ ] Setup project\n- [x] Implement core\n..."
# Raises TaskTrackerSectionNotFoundError when section not found

# _parse_task_lines() returns
list[TaskInfo]: [
    TaskInfo("Setup project", False, 12, 0),      # Top-level task
    TaskInfo("Implement core", True, 13, 1)       # Indented task
]

# Helper functions (if extracted during implementation)
# _is_task_line() returns  
Tuple[bool, bool]: (True, False)   # Is task, not complete
Tuple[bool, bool]: (True, True)    # Is task, complete
Tuple[bool, bool]: (False, False)  # Not a task line
```

## Tests to Implement (TDD)
```python
def test_find_implementation_section_basic():
    """Test finding basic Implementation Steps section."""

def test_find_implementation_section_skip_pull_request():
    """Test that Pull Request section is excluded."""

def test_find_implementation_section_case_insensitive():
    """Test case-insensitive header matching."""

def test_parse_task_lines_mixed_status():
    """Test parsing lines with both complete and incomplete tasks."""

def test_clean_task_name_removes_formatting():
    """Test removal of markdown links and formatting."""

def test_is_task_line_various_formats():
    """Test task line detection with different checkbox formats."""
```

## LLM Prompt for Implementation
```
Implement Step 2 of the task tracker parser following pr_info/steps/summary.md and building on Step 1.

Create the core markdown parsing functionality:

1. **Write Tests First (TDD)**:
   - Test finding Implementation Steps section in various markdown structures
   - Test excluding Pull Request section from parsing
   - Test parsing task lines with different checkbox states ([ ], [x], [X])
   - Test cleaning task names (remove "- [ ]", links, extra whitespace)
   - Test edge cases: malformed tasks, missing sections, empty content

2. **Implement Section Parsing**:
   - _find_implementation_section(): Use string operations to find section
   - Handle case-insensitive headers ("implementation steps", "Implementation Steps")
   - Stop parsing when encountering "Pull Request" section
   - Return the raw section content for task parsing

3. **Implement Task Extraction**:
   - _parse_task_lines(): Parse each line for task patterns
   - _is_task_line(): Detect task lines and completion status
   - _clean_task_name(): Remove markdown formatting and normalize text
   - Create TaskInfo objects with proper line numbers

4. **Handle Edge Cases**:
   - Empty sections, malformed markdown, mixed task formats
   - Preserve task names while removing formatting
   - Handle both [x] and [X] for completion markers

Use simple string operations and basic regex. Keep functions focused and testable. Build on the TaskInfo model and file reading from Step 1.
```
