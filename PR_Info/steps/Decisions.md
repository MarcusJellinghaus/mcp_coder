# Project Plan Review Decisions

## Discussion Summary
Interactive review of the task tracker parser implementation plan with step-by-step decision making on complexity and scope.

## Key Decisions Made

### 1. Project Structure
- **Decision:** Keep original 4 detailed steps (vs simplified 2-step approach)
- **Rationale:** Maintains clear separation of concerns and follows established development process

### 2. Testing Strategy
- **Decision:** Moderate testing approach (Option C)
- **Rationale:** Keep important edge cases but reduce redundant tests
- **Specifics:** 5 essential test files: valid_tracker.md, missing_section.md, empty_tracker.md, real_world_tracker.md, case_insensitive.md

### 3. Data Model Complexity
- **Decision:** Keep TaskInfo dataclass (Option A) + add indentation_level
- **Rationale:** Clean, typed, readable approach
- **Final Model:**
  ```python
  @dataclass
  class TaskInfo:
      name: str
      is_complete: bool
      line_number: int
      indentation_level: int  # For future hierarchy support
  ```

### 4. Helper Functions Strategy
- **Decision:** Plan core helpers + extract more during implementation if needed (Option B)
- **Core Helpers:** `_read_task_tracker()`, `_find_implementation_section()`, `_parse_task_lines()`
- **Rationale:** Respect clean code and YAGNI - plan predictable reuse, extract others as needed

### 5. Task Name Matching
- **Decision:** Simple case-insensitive exact matching (Option B)
- **Rationale:** Much simpler implementation than fuzzy matching
- **Example:** `is_task_done("setup project")` matches "Setup Project" but not partial matches

### 6. Error Handling Strategy  
- **Decision:** Use specific exceptions (Option B - cleanest)
- **Rationale:** Follows clean code principles - explicit, fail-fast, Pythonic
- **Exception Types:**
  - `TaskTrackerError` (base)
  - `TaskTrackerFileNotFoundError` 
  - `TaskTrackerSectionNotFoundError`

### 7. Folder Path Configuration
- **Decision:** Keep folder_path parameter with lowercase default (Option A + modification)
- **Final API:** `folder_path: str = "pr_info"`
- **Rationale:** Maintains flexibility while using standard lowercase convention

### 8. Test File Consolidation
- **Decision:** Essential 5 test files (Option B)
- **Files:** valid_tracker.md, missing_section.md, empty_tracker.md, real_world_tracker.md, case_insensitive.md
- **Rationale:** Covers core functionality and important edge cases without excessive test bloat

### 8. Package Structure
- **Decision:** Create new `workflow_utils` package instead of using existing `utils`
- **Rationale:** Better organization for workflow-related utilities, future-ready for more workflow tools
- **Implementation:** `src/mcp_coder/workflow_utils/task_tracker.py` instead of `src/mcp_coder/utils/task_tracker.py`

## Implementation Impact

### Updated Public API
```python
def get_incomplete_tasks(folder_path: str = "pr_info") -> list[str]:
    """Get list of incomplete task names from Implementation Steps section"""

def is_task_done(task_name: str, folder_path: str = "pr_info") -> bool:  
    """Check if specific task is marked as complete (case-insensitive exact match)"""
```

### New Package Structure
```
src/mcp_coder/
├── utils/                    # Existing utilities (unchanged)
└── workflow_utils/           # NEW - Workflow automation
    ├── task_tracker.py      # NEW - Task tracking functionality
    └── __init__.py          # NEW - Package exports
```

### Clean Error Handling
- All functions raise specific exceptions for different failure conditions
- Caller can distinguish between file not found vs section not found vs other issues
- Follows Python best practices for error handling

### Future-Ready Design
- TaskInfo includes indentation_level for future hierarchy support
- Modular helper structure allows extension
- Exception hierarchy supports additional error types

## Next Steps
Proceed with implementation using the original 4-step structure with all agreed modifications integrated into the step files.
