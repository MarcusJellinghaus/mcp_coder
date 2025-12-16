# Step 1: Add `validated_issue_number` Parameter to `update_workflow_label()`

## LLM Prompt

```
Implement Step 1 of Issue #203: Add `validated_issue_number` parameter to `update_workflow_label()`.

Read pr_info/steps/summary.md for context, then implement the changes described in this step.
Follow TDD: write tests first, then implement functionality.
```

## Overview

Add an optional `validated_issue_number` parameter to `IssueManager.update_workflow_label()` that allows callers to provide a pre-validated issue number, skipping the branch-to-issue linkage validation.

## WHERE: Files to Modify

1. `tests/utils/github_operations/test_issue_manager_label_update.py` - Add new tests
2. `src/mcp_coder/utils/github_operations/issue_manager.py` - Add parameter

## WHAT: Function Signature Change

```python
# BEFORE
def update_workflow_label(
    self,
    from_label_id: str,
    to_label_id: str,
    branch_name: Optional[str] = None,
) -> bool:

# AFTER
def update_workflow_label(
    self,
    from_label_id: str,
    to_label_id: str,
    branch_name: Optional[str] = None,
    validated_issue_number: Optional[int] = None,
) -> bool:
```

## HOW: Integration Points

- No new imports required
- Existing decorator `@log_function_call` remains unchanged
- Backward compatible: all existing callers work without modification

## ALGORITHM: Core Logic (in `update_workflow_label`)

```python
# At start of method:
if validated_issue_number is not None:
    # Skip steps 1-3: branch detection, issue extraction, linkage validation
    issue_number = validated_issue_number
    # Jump directly to step 4: Load label config
else:
    # Existing logic: detect branch, extract issue, validate linkage
    ...
```

## DATA: Return Values

- Returns `bool`: `True` if label updated successfully, `False` otherwise
- No change to return type or behavior

## Tests to Add

### Test 1: `test_update_workflow_label_with_validated_issue_number`

**Purpose**: Verify that providing `validated_issue_number` skips branch validation.

```python
def test_update_workflow_label_with_validated_issue_number(
    self, mock_github: Mock, tmp_path: Path
) -> None:
    """Tests that validated_issue_number skips branch linkage validation."""
    # Setup: Mock get_linked_branches to return empty (simulating post-PR state)
    # Call: update_workflow_label(..., validated_issue_number=123)
    # Assert: Returns True (label updated successfully)
    # Assert: get_linked_branches was NOT called
```

### Test 2: `test_update_workflow_label_validated_issue_number_invalid`

**Purpose**: Verify that invalid validated_issue_number still fails gracefully.

```python
def test_update_workflow_label_validated_issue_number_invalid(
    self, mock_github: Mock, tmp_path: Path
) -> None:
    """Tests that invalid validated_issue_number (non-existent issue) fails gracefully."""
    # Setup: Mock get_issue to return empty IssueData (issue not found)
    # Call: update_workflow_label(..., validated_issue_number=99999)
    # Assert: Returns False
    # Assert: Appropriate error logged
```

### Test 3: `test_update_workflow_label_race_condition_scenario`

**Purpose**: Simulate the exact race condition from the bug report.

```python
def test_update_workflow_label_race_condition_scenario(
    self, mock_github: Mock, tmp_path: Path
) -> None:
    """Tests the race condition: linkedBranches empty after PR creation.
    
    Simulates:
    1. Branch was linked to issue before PR creation
    2. PR was created (GitHub removes linkedBranches)
    3. Caller provides validated_issue_number from earlier validation
    4. Label update succeeds despite empty linkedBranches
    """
    # Setup: 
    #   - Mock get_linked_branches to return [] (post-PR state)
    #   - Mock get_issue to return valid issue data
    # Call: update_workflow_label(..., validated_issue_number=123)
    # Assert: Returns True
    # Assert: Label was updated correctly
```

## Implementation Details

### Modified Method Structure

```python
@log_function_call
def update_workflow_label(
    self,
    from_label_id: str,
    to_label_id: str,
    branch_name: Optional[str] = None,
    validated_issue_number: Optional[int] = None,
) -> bool:
    """Update workflow label after successful workflow completion.

    [... existing docstring ...]

    Args:
        from_label_id: Internal ID of source label (e.g., "implementing")
        to_label_id: Internal ID of target label (e.g., "code_review")
        branch_name: Optional branch name. If None, detects current branch.
        validated_issue_number: Optional pre-validated issue number. If provided,
            skips branch detection and linkage validation. Use this when the
            branch-issue linkage has been verified earlier in the workflow
            (e.g., before PR creation when GitHub removes the linkage).

    Returns:
        True if label updated successfully, False otherwise
    """
    try:
        # NEW: Check for pre-validated issue number
        if validated_issue_number is not None:
            issue_number = validated_issue_number
            # Skip to step 4 (label config loading)
        else:
            # Step 1: Get branch name (existing logic)
            # Step 2: Extract issue number from branch name (existing logic)
            # Step 3: Verify branch is linked to the issue (existing logic)
            ...
        
        # Step 4: Load label config and build lookups (existing logic)
        # Step 5-9: Label transition logic (existing logic, unchanged)
        ...
```

## Verification

After implementation:
1. Run existing tests: `pytest tests/utils/github_operations/test_issue_manager_label_update.py -v`
2. Run new tests specifically
3. Verify no regressions in other issue manager tests
