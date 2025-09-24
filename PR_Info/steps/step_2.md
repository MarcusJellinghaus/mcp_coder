# Step 2: Implement Task Parsing Functions

## Context
Following the summary and Step 1, implement the core task parsing functionality using Test-Driven Development.

## WHERE: File Paths and Module Structure
```
src/mcp_coder/workflow_utils/task_tracker.py  # Add parsing functions
tests/workflow_utils/test_task_tracker.py     # Add parsing tests
```

## WHAT: Main Functions with Signatures
```python
def _find_implementation_section(content: str) -> str:
    """Extract Implementation Steps section from markdown content"""

def _parse_tasks_from_section(section: str) -> list[Task]:
    """Parse task list from markdown section"""

def _clean_task_name(raw_task: str) -> str:
    """Clean task name by removing markdown formatting and links"""

def get_incomplete_tasks(pull_request_info_folder: str = "PR_Info") -> list[str]:
    """Return list of incomplete task names from Implementation Steps section"""
```

## HOW: Integration Points
- Add imports: `from pathlib import Path`
- Use existing project patterns for file operations
- Internal helper functions prefixed with `_`
- Public API functions without underscore prefix

## ALGORITHM: Core Parsing Logic
```python
# 1. Read TASK_TRACKER.md from specified folder
# 2. Find "Implementation Steps" section (skip "Pull Request")
# 3. Extract lines starting with "- [ ]" (incomplete tasks)
# 4. Clean task names (remove "- [ ]", links, extra whitespace)
# 5. Return list of clean task names
```

## DATA: Return Values and Data Structures
```python
# get_incomplete_tasks() returns
list[str]: ["Setup project structure", "Implement parser functions"]

# _parse_tasks_from_section() returns  
list[Task]: [Task("Setup", False), Task("Parse", True)]

# _find_implementation_section() returns
str: "### Implementation Steps\n- [ ] Task 1\n- [x] Task 2"
```

## LLM Prompt for Implementation
```
Implement Step 2 of the task tracker parser following pr_info/steps/summary.md.

Based on Step 1's foundation, implement the core parsing functions:

1. Write comprehensive tests first (TDD approach):
   - Test parsing markdown with various task formats
   - Test finding Implementation Steps section (not Pull Request)  
   - Test incomplete task extraction
   - Test task name cleaning (remove links, formatting)

2. Implement the functions to make tests pass:
   - _find_implementation_section(): Use string operations to find section
   - _parse_tasks_from_section(): Parse lines with "- [ ]" and "- [x]"
   - _clean_task_name(): Remove markdown formatting
   - get_incomplete_tasks(): Main public API function

3. Handle edge cases: missing files, empty sections, malformed tasks

Keep implementation simple using basic string operations and Path for file handling.
```
