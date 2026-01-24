# Step 3: Implement Branch Status Collection Logic

## LLM Prompt
```
Based on the summary document and this step, implement the core logic for collecting branch status information from multiple sources.

Create `collect_branch_status()` function in `src/mcp_coder/utils/branch_status.py` that orchestrates gathering CI status, rebase info, task tracker status, and GitHub labels. Write comprehensive tests first, then implement the collection logic.

Reference the summary document for integration points with existing CIResultsManager, task_tracker, and GitHub utilities.
```

## WHERE
- **File**: `src/mcp_coder/utils/branch_status.py` (extend existing)
- **Test File**: `tests/utils/test_branch_status.py` (extend existing)

## WHAT

### Main Collection Function
```python
def collect_branch_status(
    project_dir: Path,
    truncate_logs: bool = False,
    max_log_lines: int = 200
) -> BranchStatusReport:
    """Collect comprehensive branch status from all sources.
    
    Args:
        project_dir: Path to git repository
        truncate_logs: Whether to truncate CI logs for LLM consumption
        max_log_lines: Maximum log lines when truncating
    
    Returns:
        BranchStatusReport with all collected information
    """
```

### Helper Functions
```python
def _collect_ci_status(project_dir: Path, branch: str, truncate: bool, max_lines: int) -> Tuple[str, Optional[str]]:
    """Collect CI status and error details."""

def _collect_rebase_status(project_dir: Path) -> Tuple[bool, bool]:
    """Collect rebase requirements."""

def _collect_task_status(project_dir: Path) -> bool:
    """Collect task tracker completion status."""

def _collect_github_label(project_dir: Path) -> str:
    """Collect current GitHub workflow status label."""

def _generate_recommendations(report_data: dict) -> List[str]:
    """Generate actionable recommendations based on status."""
```

### Test Functions
```python
def test_collect_branch_status_all_good()
def test_collect_branch_status_ci_failed()
def test_collect_branch_status_rebase_needed()
def test_collect_branch_status_tasks_incomplete()
def test_collect_ci_status_with_truncation()
def test_collect_rebase_status_edge_cases()
def test_generate_recommendations_logic()
```

## HOW

### Integration Points
```python
# Import existing utilities
from ..github_operations.ci_results_manager import CIResultsManager
from ..github_operations.labels_manager import LabelsManager
from ..git_operations.branches import needs_rebase, get_current_branch_name
from ...workflow_utils.task_tracker import has_incomplete_work
```

### Algorithm (collect_branch_status)
```
1. Get current branch name and validate git repo
2. Collect CI status using CIResultsManager
3. Collect rebase status using needs_rebase()
4. Collect task tracker status using has_incomplete_work()
5. Collect GitHub label using LabelsManager
6. Generate recommendations based on collected data
```

## DATA

### Internal Data Flow
```python
# CI Collection Result
ci_status: str  # "PASSED", "FAILED", "NOT_CONFIGURED", "PENDING"
ci_details: Optional[str]  # Raw or truncated logs

# Rebase Collection Result  
rebase_needed: bool
conflicts_expected: bool

# Task Collection Result
tasks_incomplete: bool

# GitHub Collection Result
current_label: str  # e.g., "status-03:implementing"
```

### Recommendation Logic
```python
# Priority order for recommendations:
1. Fix CI failures (if CI failed)
2. Complete incomplete tasks (if tasks not done)
3. Review conflicts before rebase (if conflicts expected)
4. Ready for next workflow step (if all checks pass)
```

### Error Handling Strategy
```python
# Graceful degradation for each collection:
# CI: Return "NOT_CONFIGURED" if API fails
# Rebase: Return (False, False) if git operations fail  
# Tasks: Return False if task tracker missing
# GitHub: Return "unknown" if API fails
```

## Implementation Notes
- **Parallel Independence**: Each collection function handles its own errors
- **Logging Strategy**: Use INFO for successful collections, WARNING for failures
- **Performance**: Use existing caching in CIResultsManager and other utilities
- **Extensibility**: Easy to add new status collections without breaking existing flow
- **Testing Strategy**: Mock external dependencies (GitHub API, git operations) for reliable tests