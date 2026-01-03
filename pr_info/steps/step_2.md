# Step 2: Core Implementation - Graceful Branch Handling

## LLM Prompt
```
I'm implementing a fix for issue #232 where the coordinator crashes when no linked branch is found.

Please review the summary in `pr_info/steps/summary.md` and implement Step 2: Modify the `dispatch_workflow()` function in `src/mcp_coder/cli/commands/coordinator.py` to handle missing branch scenarios gracefully instead of raising ValueError.

The tests from Step 1 should now pass with this implementation.

Requirements:
- Replace ValueError with warning log and early return
- Preserve all existing behavior for valid branch cases
- Follow existing logging patterns in the codebase
- Maintain function signature and overall structure
```

## WHERE: Implementation Location  
- **File**: `src/mcp_coder/cli/commands/coordinator.py`
- **Function**: `dispatch_workflow()` (around line 332)
- **Scope**: Replace exception handling for missing branch scenario

## WHAT: Function Modification
```python
def dispatch_workflow(
    issue: IssueData,
    workflow_name: str,
    repo_config: dict[str, str],
    jenkins_client: JenkinsClient,
    issue_manager: IssueManager,
    branch_manager: IssueBranchManager,
    log_level: str,
) -> None:
    """Trigger Jenkins job for workflow and update issue label.
    
    Now handles missing branch scenarios gracefully by logging warning
    and returning early instead of raising ValueError.
    """
```

## HOW: Integration Points
- **Logging**: Use existing `logger.warning()` for missing branch scenario
- **Early Return**: Replace `raise ValueError()` with `return` statement  
- **Preserve**: All existing logic for valid branch cases unchanged
- **Maintain**: Function signature and docstring updated to reflect new behavior

## ALGORITHM: Core Logic Change
```
1. Find current workflow label from issue (existing)
2. Determine branch strategy (existing) 
3. If from_issue strategy: call get_linked_branches()
4. If branches empty: log warning + return (NEW - replaces ValueError)
5. If branches found: continue with existing logic (unchanged)
6. Process remaining workflow steps (existing)
```

## DATA: Code Changes
```python
# Current code (around line 332):
if not branches:
    raise ValueError(f"No linked branch found for issue #{issue['number']}")

# New code:
if not branches:
    logger.warning(
        f"No linked branch found for issue #{issue['number']}, skipping workflow dispatch"
    )
    return
```

## Implementation Details
- **Line Location**: Around line 332 in coordinator.py
- **Change Type**: Replace 1 line (raise) with 2 lines (log + return)
- **Scope**: Only affects the missing branch error case
- **Backward Compatibility**: Full - all existing behavior preserved

## Verification Checklist
- [ ] Tests from Step 1 pass
- [ ] No changes to function signature
- [ ] Warning message includes issue number for debugging
- [ ] Early return prevents downstream processing of invalid case
- [ ] Existing valid branch processing unchanged