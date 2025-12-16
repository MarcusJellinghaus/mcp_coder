# Step 2: Add Early Validation to Create-PR Workflow

## LLM Prompt

```
Implement Step 2 of Issue #203: Add early validation to create-pr workflow.

Read pr_info/steps/summary.md for context, then implement the changes described in this step.
Follow TDD: write tests first, then implement functionality.

Prerequisite: Step 1 must be completed first (validated_issue_number parameter added).
```

## Overview

Add a `validate_branch_issue_linkage()` helper function to cache the branch-issue linkage before PR creation, then use the cached issue number when calling `update_workflow_label()` after PR creation.

## WHERE: Files to Modify

1. `tests/workflows/create_pr/test_workflow.py` - Add new tests
2. `src/mcp_coder/workflows/create_pr/core.py` - Add helper function and integrate

## WHAT: New Function and Modified Call

### New Helper Function

```python
def validate_branch_issue_linkage(project_dir: Path) -> Optional[int]:
    """Validate current branch is linked to an issue.
    
    Args:
        project_dir: Path to the project directory
        
    Returns:
        Issue number if branch is linked, None otherwise
    """
```

### Modified Workflow Call

```python
# In run_create_pr_workflow(), before update_labels section:
# Cache the result of validation BEFORE PR creation

# After PR creation, in update_labels section:
issue_manager.update_workflow_label(
    from_label_id="pr_creating",
    to_label_id="pr_created",
    validated_issue_number=cached_issue_number,  # NEW
)
```

## HOW: Integration Points

### New Imports in `core.py`

```python
import re
from mcp_coder.utils.github_operations.issue_branch_manager import IssueBranchManager
```

### Workflow Integration

The helper is called early in the workflow (after prerequisites, before PR creation) and the result is passed to `update_workflow_label()` later.

## ALGORITHM: `validate_branch_issue_linkage()`

```python
def validate_branch_issue_linkage(project_dir: Path) -> Optional[int]:
    # 1. Get current branch name
    branch_name = get_current_branch_name(project_dir)
    if not branch_name:
        return None
    
    # 2. Extract issue number from branch name using regex
    match = re.match(r"^(\d+)-", branch_name)
    if not match:
        return None
    issue_number = int(match.group(1))
    
    # 3. Query linked branches via GitHub API
    branch_manager = IssueBranchManager(project_dir=project_dir)
    linked_branches = branch_manager.get_linked_branches(issue_number)
    
    # 4. Check if current branch is in linked branches
    if branch_name in linked_branches:
        return issue_number
    return None
```

## ALGORITHM: Modified `run_create_pr_workflow()`

```python
def run_create_pr_workflow(..., update_labels: bool = False) -> int:
    # ... existing steps 1-3 ...
    
    # NEW: Cache branch-issue linkage before PR creation
    cached_issue_number: Optional[int] = None
    if update_labels:
        cached_issue_number = validate_branch_issue_linkage(project_dir)
        if cached_issue_number:
            log_step(f"Branch linked to issue #{cached_issue_number}")
        else:
            logger.warning("Branch not linked to any issue, label update will be skipped")
    
    # Step 4: Create pull request (GitHub removes linkedBranches here)
    # ... existing logic ...
    
    # Update labels section (modified)
    if update_labels:
        if cached_issue_number is None:
            logger.warning("Skipping label update: branch was not linked to an issue")
        else:
            issue_manager = IssueManager(project_dir)
            success = issue_manager.update_workflow_label(
                from_label_id="pr_creating",
                to_label_id="pr_created",
                validated_issue_number=cached_issue_number,  # Use cached value
            )
            # ... existing success/failure logging ...
```

## DATA: Return Values

- `validate_branch_issue_linkage()` returns `Optional[int]`:
  - `int`: Issue number if branch is linked
  - `None`: If branch is not linked or detection fails

## Tests to Add

### Test 1: `test_validate_branch_issue_linkage_success`

```python
def test_validate_branch_issue_linkage_success(tmp_path: Path) -> None:
    """Tests successful validation when branch is linked to issue."""
    # Setup: Mock branch name "123-feature", linked branches ["123-feature"]
    # Call: validate_branch_issue_linkage(tmp_path)
    # Assert: Returns 123
```

### Test 2: `test_validate_branch_issue_linkage_not_linked`

```python
def test_validate_branch_issue_linkage_not_linked(tmp_path: Path) -> None:
    """Tests validation fails when branch is not linked."""
    # Setup: Mock branch name "123-feature", linked branches []
    # Call: validate_branch_issue_linkage(tmp_path)
    # Assert: Returns None
```

### Test 3: `test_validate_branch_issue_linkage_no_issue_number`

```python
def test_validate_branch_issue_linkage_no_issue_number(tmp_path: Path) -> None:
    """Tests validation fails when branch name has no issue number."""
    # Setup: Mock branch name "feature-branch" (no issue number prefix)
    # Call: validate_branch_issue_linkage(tmp_path)
    # Assert: Returns None
```

### Test 4: `test_workflow_caches_issue_number_before_pr_creation`

```python
@patch("mcp_coder.workflows.create_pr.core.validate_branch_issue_linkage")
@patch("mcp_coder.workflows.create_pr.core.IssueManager")
def test_workflow_caches_issue_number_before_pr_creation(
    mock_issue_manager_class: MagicMock,
    mock_validate: MagicMock,
    ...
) -> None:
    """Tests that workflow caches issue number before PR creation."""
    # Setup: Mock validate_branch_issue_linkage to return 123
    # Call: run_create_pr_workflow(..., update_labels=True)
    # Assert: update_workflow_label called with validated_issue_number=123
```

### Test 5: `test_workflow_skips_label_update_when_not_linked`

```python
@patch("mcp_coder.workflows.create_pr.core.validate_branch_issue_linkage")
def test_workflow_skips_label_update_when_not_linked(
    mock_validate: MagicMock,
    ...
) -> None:
    """Tests that workflow skips label update when branch not linked."""
    # Setup: Mock validate_branch_issue_linkage to return None
    # Call: run_create_pr_workflow(..., update_labels=True)
    # Assert: update_workflow_label NOT called
    # Assert: Warning logged about skipping
```

## Implementation Notes

1. **Error Handling**: All errors in `validate_branch_issue_linkage()` should be caught and logged, returning `None` (fail-safe)

2. **Logging**: 
   - INFO: "Branch linked to issue #X" when validation succeeds
   - WARNING: "Branch not linked to any issue" when validation fails
   - WARNING: "Skipping label update: branch was not linked" in workflow

3. **Backward Compatibility**: If `update_labels=False`, no validation is performed (existing behavior)

## Verification

After implementation:
1. Run workflow tests: `pytest tests/workflows/create_pr/test_workflow.py -v`
2. Run full test suite to check for regressions
3. Manual test with actual GitHub repository (optional integration test)
