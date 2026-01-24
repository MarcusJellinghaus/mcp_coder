# Step 2: Create Branch Status Data Structures

## LLM Prompt
```
Based on the summary document and this step, create the data structures needed for branch status reporting. 

Create a new module `src/mcp_coder/utils/branch_status.py` with the `BranchStatusReport` dataclass and related utilities. Write comprehensive tests first, then implement the data structures and helper functions.

Reference the summary document for the exact data structure requirements and integration points.
```

## WHERE
- **New File**: `src/mcp_coder/utils/branch_status.py`
- **Test File**: `tests/utils/test_branch_status.py`

## WHAT

### Main Data Structure
```python
@dataclass
class BranchStatusReport:
    """Branch readiness status report."""
    ci_status: str                    # "PASSED", "FAILED", "NOT_CONFIGURED", "PENDING"
    ci_details: Optional[str]         # Error logs or None
    rebase_needed: bool               # True if rebase required
    rebase_reason: str                # Reason for rebase status
    tasks_complete: bool              # True if all tracker tasks done
    current_github_label: str         # Current workflow status label
    recommendations: List[str]        # List of suggested actions
    
    def format_for_human(self) -> str:
        """Format report for human consumption."""
    
    def format_for_llm(self, max_lines: int = 200) -> str:
        """Format report for LLM consumption with truncation."""
```

### Helper Functions
```python
def create_empty_report() -> BranchStatusReport:
    """Create empty report with default values."""

def truncate_ci_details(details: str, max_lines: int = 200) -> str:
    """Truncate CI details using existing logic from implement workflow."""
```

### Test Functions
```python
def test_branch_status_report_creation()
def test_format_for_human()
def test_format_for_llm_truncation()
def test_create_empty_report()
def test_truncate_ci_details()
```

## HOW

### Integration Points
- Import `List`, `Optional` from typing
- Import `dataclass` from dataclasses
- Reference existing truncation logic from `workflows/implement/core.py._extract_log_excerpt()`

### Algorithm (format_for_human)
```
1. Create formatted header with status indicators
2. Add CI section with status and details
3. Add rebase section with conflict warnings
4. Add task tracker section with completion status
5. Add recommendations list with action items
```

## DATA

### Status Constants
```python
# CI Status Values
CI_PASSED = "PASSED"
CI_FAILED = "FAILED"  
CI_NOT_CONFIGURED = "NOT_CONFIGURED"
CI_PENDING = "PENDING"

# Default Values
DEFAULT_LABEL = "unknown"
EMPTY_RECOMMENDATIONS = []
```

### Format Examples
```python
# Human format:
"""
Branch Status Report for: feature/awesome-feature

CI Status: ❌ FAILED
- Job 'test' failed at step 'Run tests'
- 2 other jobs passed

CI Error Details:
FAILED tests/test_example.py::test_function - AssertionError
[... error logs ...]

Rebase Status: ⚠️ BEHIND  
- 3 commits behind origin/main

Task Tracker: ✅ COMPLETE
- All 5 tasks completed

GitHub Status: status-03:implementing

Recommendations:
- Fix CI test failures before proceeding
- Rebase onto origin/main when ready
"""

# LLM format (truncated CI logs only):
"""
Branch Status: CI=FAILED, Rebase=BEHIND, Tasks=COMPLETE
CI Errors: [truncated to ~200 lines]
"""
```

## Implementation Notes
- **Immutable Design**: Use dataclass with frozen=True for immutability
- **Rich Formatting**: Use emoji indicators (✅❌⚠️) for visual clarity
- **Truncation Strategy**: Reuse existing `_extract_log_excerpt()` logic
- **Extensible**: Easy to add new fields without breaking existing code