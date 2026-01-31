# Step 3: Update Formatting and Refactor implement/core.py

## LLM Prompt

```
Implement Step 3 of Issue #374 (see pr_info/steps/summary.md for context).

Update output formatting and refactor the implement workflow:
1. First update tests for new output format
2. Modify format_for_human() and format_for_llm() methods
3. Refactor _get_rebase_target_branch() to use shared function

Follow the specifications below exactly.
```

## Overview

Update the formatting methods to display branch information and refactor `_get_rebase_target_branch()` in `implement/core.py` to use the shared `detect_base_branch()` function.

---

## WHERE: File Paths

### Modified Files
- `src/mcp_coder/workflow_utils/branch_status.py` - Update formatting methods
- `src/mcp_coder/workflows/implement/core.py` - Refactor rebase target detection
- `tests/workflow_utils/test_branch_status.py` - Update format tests

---

## WHAT: Updated format_for_human Method

```python
def format_for_human(self) -> str:
    """Format report for human consumption."""
    # ... existing icon setup ...

    # Build the report sections - NEW: Branch info first
    lines = [
        f"Branch: {self.branch_name}",
        f"Base Branch: {self.base_branch}",
        "",
        "Branch Status Report",
        "",
        f"CI Status: {ci_icon} {self.ci_status}",
    ]
    # ... rest of existing implementation ...
```

---

## WHAT: Updated format_for_llm Method

```python
def format_for_llm(self, max_lines: int = 300) -> str:
    """Format report for LLM consumption with truncation."""
    # Convert rebase_needed to status string
    rebase_status = "BEHIND" if self.rebase_needed else "UP_TO_DATE"
    tasks_status = "COMPLETE" if self.tasks_complete else "INCOMPLETE"

    # Build status summary line
    status_summary = (
        f"Branch Status: CI={self.ci_status}, Rebase={rebase_status}, "
        f"Tasks={tasks_status}"
    )
    recommendations_text = ", ".join(self.recommendations)

    # NEW: Branch info on first line
    lines = [
        f"Branch: {self.branch_name} | Base: {self.base_branch}",
        status_summary,
        f"GitHub Label: {self.current_github_label}",
        f"Recommendations: {recommendations_text}",
    ]
    # ... rest of existing implementation ...
```

---

## WHAT: Refactored _get_rebase_target_branch

```python
# src/mcp_coder/workflows/implement/core.py

from mcp_coder.workflow_utils.base_branch import detect_base_branch

def _get_rebase_target_branch(project_dir: Path) -> Optional[str]:
    """Determine the target branch for rebasing the current feature branch.

    Uses shared detect_base_branch() function for detection.

    Args:
        project_dir: Path to the project directory

    Returns:
        Branch name to rebase onto, or None if detection fails
    """
    result = detect_base_branch(project_dir)
    return None if result == "unknown" else result
```

---

## HOW: Integration Points

### Import Change in implement/core.py

```python
# Remove these (no longer needed directly):
# from mcp_coder.utils.github_operations.pr_manager import PullRequestManager

# Add this:
from mcp_coder.workflow_utils.base_branch import detect_base_branch
```

Note: Keep `get_current_branch_name` and `get_default_branch_name` imports as they may be used elsewhere in the file.

---

## ALGORITHM: format_for_human Changes

```
function format_for_human():
    # Setup icons (unchanged)
    
    lines = [
        "Branch: {branch_name}",      # NEW LINE 1
        "Base Branch: {base_branch}", # NEW LINE 2
        "",                            # NEW blank line
        "Branch Status Report",        # Was first line, now line 4
        "",
        "CI Status: {icon} {status}",
        # ... rest unchanged
    ]
    
    return join(lines, "\n")
```

---

## ALGORITHM: format_for_llm Changes

```
function format_for_llm(max_lines):
    # Calculate status strings (unchanged)
    
    lines = [
        "Branch: {branch_name} | Base: {base_branch}",  # NEW first line
        "Branch Status: CI={ci}, Rebase={rebase}, Tasks={tasks}",
        "GitHub Label: {label}",
        "Recommendations: {recs}",
    ]
    
    # Add CI details if present (unchanged)
    
    return join(lines, "\n")
```

---

## TEST UPDATES

### Updated format_for_human Tests

```python
def test_format_for_human_passed_status() -> None:
    """Test format_for_human with all systems green."""
    report = BranchStatusReport(
        branch_name="feature/123-test",
        base_branch="main",
        ci_status="PASSED",
        # ... rest of fields
    )

    formatted = report.format_for_human()

    # NEW assertions - branch info comes first
    assert "Branch: feature/123-test" in formatted
    assert "Base Branch: main" in formatted
    # Verify order: branch info before title
    branch_pos = formatted.find("Branch:")
    title_pos = formatted.find("Branch Status Report")
    assert branch_pos < title_pos

    # Existing assertions
    assert "CI Status: ✅ PASSED" in formatted
    # ...
```

### Updated format_for_llm Tests

```python
def test_format_for_llm_basic() -> None:
    """Test format_for_llm basic functionality."""
    report = BranchStatusReport(
        branch_name="feature/456-other",
        base_branch="develop",
        ci_status="PASSED",
        # ... rest of fields
    )

    formatted = report.format_for_llm()

    # NEW assertion - branch info on first line
    lines = formatted.split("\n")
    assert lines[0] == "Branch: feature/456-other | Base: develop"

    # Existing assertions
    assert "Branch Status: CI=PASSED" in formatted
    # ...
```

---

## IMPLEMENTATION CHECKLIST

- [ ] Update format tests to expect new output format
- [ ] Update `format_for_human()` to prepend branch info
- [ ] Update `format_for_llm()` to add branch info as first line
- [ ] Add import for `detect_base_branch` in `implement/core.py`
- [ ] Refactor `_get_rebase_target_branch()` to 2-line implementation
- [ ] Remove unused imports from `implement/core.py` (if any)
- [ ] Run all tests to verify everything passes
- [ ] Run mypy type checking
- [ ] Manually test `mcp-coder check branch-status` output
