# Step 1: Setup Project Structure and Data Models

## Context
Following the summary in `pr_info/steps/summary.md`, create the basic project structure and data models for the task tracker parser using Test-Driven Development.

## WHERE: File Paths and Module Structure
```
src/mcp_coder/workflow_utils/
├── __init__.py          # New module initialization
└── task_tracker.py      # Main implementation

tests/workflow_utils/
├── __init__.py          # Test package initialization  
└── test_task_tracker.py # Unit tests
```

## WHAT: Main Functions with Signatures
```python
# Data model
@dataclass
class Task:
    name: str
    is_complete: bool

# Test infrastructure setup
def setup_test_markdown_file(content: str, temp_dir: Path) -> Path:
    """Helper to create test markdown files"""
```

## HOW: Integration Points
- Create new `workflow_utils` package in `src/mcp_coder/`
- Add imports: `from dataclasses import dataclass`
- Follow existing project structure patterns
- Add to gitignore if needed: `tests/workflow_utils/test_files/`

## ALGORITHM: Core Logic (Setup)
```python
# 1. Create workflow_utils module directory
# 2. Initialize __init__.py with exports
# 3. Define Task dataclass in task_tracker.py
# 4. Create test directory structure  
# 5. Setup test fixtures for markdown parsing
```

## DATA: Return Values and Data Structures
```python
# Task data model
Task(name="Step 1: Setup Project", is_complete=False)
Task(name="Step 2: Implementation", is_complete=True)

# Test helper return
Path: Path to created test markdown file
```

## LLM Prompt for Implementation
```
Create the basic project structure for a task tracker parser following the summary in pr_info/steps/summary.md.

Implement Step 1:
1. Create src/mcp_coder/workflow_utils/ package with __init__.py
2. Create task_tracker.py with Task dataclass
3. Create tests/workflow_utils/ with test_task_tracker.py
4. Write initial tests for Task dataclass creation and basic validation
5. Add proper imports and module structure
6. Follow existing project patterns for package organization

Use TDD approach - write tests first, then implement the minimal code to make tests pass.
```
