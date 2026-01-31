# Step 2: Update BranchStatusReport and collect_branch_status

## LLM Prompt

```
Implement Step 2 of Issue #374 (see pr_info/steps/summary.md for context).

Update the BranchStatusReport dataclass and collect_branch_status function:
1. First update the existing tests to expect new fields
2. Then modify the implementation to include branch info

Follow the specifications below exactly.
```

## Overview

Add `branch_name` and `base_branch` fields to `BranchStatusReport` dataclass and update `collect_branch_status()` to populate them efficiently.

---

## WHERE: File Paths

### Modified Files
- `src/mcp_coder/workflow_utils/branch_status.py` - Add fields, update collection
- `tests/workflow_utils/test_branch_status.py` - Update existing tests

---

## WHAT: Updated Data Structure

```python
# src/mcp_coder/workflow_utils/branch_status.py

@dataclass(frozen=True)
class BranchStatusReport:
    """Branch readiness status report."""

    branch_name: str  # NEW: Current git branch name
    base_branch: str  # NEW: Detected parent/base branch
    ci_status: str  # "PASSED", "FAILED", "NOT_CONFIGURED", "PENDING"
    ci_details: Optional[str]  # Error logs or None
    rebase_needed: bool  # True if rebase required
    rebase_reason: str  # Reason for rebase status
    tasks_complete: bool  # True if all tracker tasks done
    current_github_label: str  # Current workflow status label
    recommendations: List[str]  # List of suggested actions
```

---

## WHAT: Updated Function Signature

```python
def _collect_github_label(
    project_dir: Path,
    branch_name: Optional[str] = None,
    issue_data: Optional[IssueData] = None,  # NEW parameter
) -> str:
    """Collect current GitHub workflow status label.
    
    Args:
        project_dir: Path to the git repository
        branch_name: Optional branch name. If not provided, will be fetched from git.
        issue_data: Optional pre-fetched issue data (avoids duplicate API calls)
    """
```

---

## HOW: Integration Points

### New Import in branch_status.py
```python
from mcp_coder.workflow_utils.base_branch import detect_base_branch
```

---

## ALGORITHM: Updated collect_branch_status (Pseudocode)

```
function collect_branch_status(project_dir, truncate_logs, max_log_lines):
    branch_name = get_current_branch_name(project_dir) or "unknown"
    
    # Fetch issue data once for sharing
    issue_data = None
    issue_number = extract_issue_number_from_branch(branch_name)
    if issue_number:
        try: issue_data = IssueManager(project_dir).get_issue(issue_number)
        except: pass
    
    # Use shared issue_data and branch_name
    base_branch = detect_base_branch(project_dir, branch_name, issue_data)
    current_label = _collect_github_label(project_dir, branch_name, issue_data)
    
    # ... rest of existing collection logic ...
    
    return BranchStatusReport(
        branch_name=branch_name,
        base_branch=base_branch,
        ci_status=ci_status,
        # ... rest unchanged
    )
```

---

## ALGORITHM: Updated _collect_github_label (Pseudocode)

```
function _collect_github_label(project_dir, branch_name, issue_data):
    if branch_name is None:
        branch_name = get_current_branch_name(project_dir)
        if not branch_name: return DEFAULT_LABEL
    
    # Use provided issue_data if available
    if issue_data is None:
        issue_number = extract_issue_number_from_branch(branch_name)
        if not issue_number: return DEFAULT_LABEL
        try: issue_data = IssueManager(project_dir).get_issue(issue_number)
        except: return DEFAULT_LABEL
    
    # Extract status label from issue_data
    for label in issue_data.get("labels", []):
        if label.startswith("status-"): return label
    
    return DEFAULT_LABEL
```

---

## DATA: Updated create_empty_report

```python
def create_empty_report() -> BranchStatusReport:
    """Create empty report with default values."""
    return BranchStatusReport(
        branch_name="unknown",  # NEW
        base_branch="unknown",  # NEW
        ci_status=CI_NOT_CONFIGURED,
        ci_details=None,
        rebase_needed=False,
        rebase_reason="Unknown",
        tasks_complete=False,
        current_github_label=DEFAULT_LABEL,
        recommendations=EMPTY_RECOMMENDATIONS,
    )
```

---

## TEST UPDATES

### Updates to `tests/workflow_utils/test_branch_status.py`

All existing tests that create `BranchStatusReport` need two new fields:

```python
# Before:
report = BranchStatusReport(
    ci_status="PASSED",
    ci_details=None,
    # ...
)

# After:
report = BranchStatusReport(
    branch_name="feature/123-test",  # NEW
    base_branch="main",               # NEW
    ci_status="PASSED",
    ci_details=None,
    # ...
)
```

### New Test Cases to Add

```python
def test_collect_branch_status_includes_branch_info() -> None:
    """Test that collect_branch_status includes branch_name and base_branch."""
    # Mock all dependencies
    # Verify result.branch_name and result.base_branch are populated


def test_collect_github_label_uses_provided_issue_data() -> None:
    """Test _collect_github_label uses pre-fetched issue_data."""
    # Pass issue_data with labels
    # Verify IssueManager.get_issue is NOT called
    # Verify correct label is returned
```

---

## IMPLEMENTATION CHECKLIST

- [ ] Update existing test cases to include new fields
- [ ] Add new test cases for branch info
- [ ] Add `branch_name` and `base_branch` fields to `BranchStatusReport`
- [ ] Update `create_empty_report()` with new fields
- [ ] Add import for `detect_base_branch`
- [ ] Update `_collect_github_label()` to accept `issue_data` parameter
- [ ] Update `collect_branch_status()` to:
  - Fetch issue data once
  - Call `detect_base_branch()` with issue_data
  - Call `_collect_github_label()` with issue_data
  - Include new fields in returned report
- [ ] Run tests to verify all pass
- [ ] Run mypy type checking
