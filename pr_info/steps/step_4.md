# Step 4: Integrate Label Updates into Workflow Success Paths

## Context
CLI flags are in place (Step 3), core method implemented (Step 2). Now we connect everything by adding label update calls at the end of each workflow's success path. This completes the feature implementation.

**Reference**: See `pr_info/steps/summary.md` for architectural overview.

## Objective
Add label update logic to three workflow functions, calling `update_workflow_label()` when the flag is set and workflow succeeds. Must be non-blocking - workflow success is independent of label update success.

## WHERE: Files to Modify

```
src/mcp_coder/workflows/implement/core.py     (MODIFY - add at end)
src/mcp_coder/workflows/create_plan.py        (MODIFY - add at end)
src/mcp_coder/workflows/create_pr/core.py     (MODIFY - add at end)
```

## WHAT: Integration Points for Each Workflow

### 1. Implement Workflow

**File**: `src/mcp_coder/workflows/implement/core.py`

**Location**: End of `run_implement_workflow()`, after all push operations complete successfully, before final return statement (around line 350)

**Label Transition**: `implementing` → `code_review`

**Condition**: `update_labels=True AND completed_tasks > 0 AND not error_occurred`

```python
# Add at end of run_implement_workflow(), before final return 0
# After Step 6 (show final progress summary)

# Step 7: Update GitHub issue label if requested
if update_labels and completed_tasks > 0 and not error_occurred:
    logger.info("Updating GitHub issue label...")
    try:
        from mcp_coder.utils.github_operations.issue_manager import IssueManager
        
        issue_manager = IssueManager(project_dir)
        success = issue_manager.update_workflow_label(
            from_label_id="implementing",
            to_label_id="code_review",
        )
        
        if success:
            logger.info("✓ Issue label updated: implementing → code-review")
        else:
            logger.warning("✗ Failed to update issue label (non-blocking)")
            
    except Exception as e:
        logger.error(f"Error updating issue label (non-blocking): {e}")

return 0
```

### 2. Create Plan Workflow

**File**: `src/mcp_coder/workflows/create_plan.py`

**Location**: End of `run_create_plan_workflow()`, after successful push, before final success message (around line 370)

**Label Transition**: `planning` → `plan_review`

**Condition**: `update_labels=True AND push was successful`

```python
# Add after push_result success check, before final logger.info()

# Update GitHub issue label if requested
if update_labels:
    logger.info("Updating GitHub issue label...")
    try:
        from mcp_coder.utils.github_operations.issue_manager import IssueManager
        
        issue_manager = IssueManager(project_dir)
        success = issue_manager.update_workflow_label(
            from_label_id="planning",
            to_label_id="plan_review",
        )
        
        if success:
            logger.info("✓ Issue label updated: planning → plan-review")
        else:
            logger.warning("✗ Failed to update issue label (non-blocking)")
            
    except Exception as e:
        logger.error(f"Error updating issue label (non-blocking): {e}")

logger.info("Create plan workflow completed successfully!")
return 0
```

### 3. Create PR Workflow

**File**: `src/mcp_coder/workflows/create_pr/core.py`

**Location**: End of `run_create_pr_workflow()`, after cleanup push completes, before final success message (around line 320)

**Label Transition**: `pr_creating` → `pr_created`

**Condition**: `update_labels=True AND workflow completed successfully`

```python
# Add after cleanup push completes, before final log_step()

# Update GitHub issue label if requested
if update_labels:
    log_step("Updating GitHub issue label...")
    try:
        from mcp_coder.utils.github_operations.issue_manager import IssueManager
        
        issue_manager = IssueManager(project_dir)
        success = issue_manager.update_workflow_label(
            from_label_id="pr_creating",
            to_label_id="pr_created",
        )
        
        if success:
            log_step("✓ Issue label updated: pr-creating → pr-created")
        else:
            logger.warning("✗ Failed to update issue label (non-blocking)")
            
    except Exception as e:
        logger.error(f"Error updating issue label (non-blocking): {e}")

log_step("Create PR workflow completed successfully!")
return 0
```

## HOW: Integration Pattern

### Common Pattern Across All Workflows
```python
if update_labels:  # Only when flag is set
    logger.info("Updating GitHub issue label...")
    try:
        from mcp_coder.utils.github_operations.issue_manager import IssueManager
        
        issue_manager = IssueManager(project_dir)
        success = issue_manager.update_workflow_label(
            from_label_id="...",
            to_label_id="...",
        )
        
        if success:
            logger.info("✓ Issue label updated: ... → ...")
        else:
            logger.warning("✗ Failed to update issue label (non-blocking)")
            
    except Exception as e:
        logger.error(f"Error updating issue label (non-blocking): {e}")
```

### Import Strategy
**Lazy import inside the conditional block** to avoid import overhead when flag is not used:
```python
if update_labels:
    # Import only when needed
    from mcp_coder.utils.github_operations.issue_manager import IssueManager
```

### Error Handling
**Triple-layer safety:**
1. `update_workflow_label()` catches all exceptions internally
2. Try-except around the call for extra safety
3. Non-blocking: workflow always returns success (0) if it got this far

## ALGORITHM: Integration Logic

```pseudocode
# At end of successful workflow execution

IF update_labels flag is True:
    Log "Updating GitHub issue label..."
    
    TRY:
        1. Import IssueManager (lazy)
        2. Create IssueManager instance with project_dir
        3. Call update_workflow_label(from_id, to_id)
        4. IF success returned:
              Log INFO "Label updated: from → to"
           ELSE:
              Log WARNING "Failed to update (non-blocking)"
    
    CATCH any exception:
        Log ERROR "Error updating label (non-blocking): {exception}"
    
    # Continue workflow - never fail here

Return 0 (success)
```

## DATA: Label Transition Mappings

### Workflow → Label Transition Map
```python
{
    "implement": {
        "from": "implementing",      # status-06:implementing
        "to": "code_review",         # status-07:code-review
    },
    "create_plan": {
        "from": "planning",          # status-03:planning
        "to": "plan_review",         # status-04:plan-review
    },
    "create_pr": {
        "from": "pr_creating",       # status-09:pr-creating
        "to": "pr_created",          # status-10:pr-created
    },
}
```

## Implementation Details

### Placement Considerations

**Implement Workflow**:
- After: Final mypy check, formatting, and push
- Before: Final "workflow completed" message
- Condition: `completed_tasks > 0 and not error_occurred`

**Create Plan Workflow**:
- After: Successful git_push() of generated plan
- Before: Final "workflow completed" message
- Condition: Always (if flag set and reached this point)

**Create PR Workflow**:
- After: PR creation and cleanup push complete
- Before: Final "workflow completed" message
- Condition: Always (if flag set and reached this point)

### Logging Conventions

```python
# Success case
logger.info("✓ Issue label updated: implementing → code-review")

# Failure case (non-blocking)
logger.warning("✗ Failed to update issue label (non-blocking)")

# Exception case (non-blocking)
logger.error(f"Error updating issue label (non-blocking): {e}")
```

The "(non-blocking)" suffix makes it clear to users that the workflow succeeded regardless.

### No Imports at Module Level
Keep imports lazy to avoid overhead when feature is not used:
```python
# DON'T add to top of file:
# from mcp_coder.utils.github_operations.issue_manager import IssueManager

# DO import inside conditional:
if update_labels:
    from mcp_coder.utils.github_operations.issue_manager import IssueManager
```

## Validation Checklist
- [ ] Implement workflow: Label update after push, before return
- [ ] Create plan workflow: Label update after push, before return
- [ ] Create PR workflow: Label update after cleanup, before return
- [ ] All use lazy import pattern (import inside if block)
- [ ] All use identical error handling structure
- [ ] All use consistent logging format with ✓/✗ symbols
- [ ] All include "(non-blocking)" in failure messages
- [ ] Correct label IDs for each workflow
- [ ] No changes to return values (always 0 on success)
- [ ] No changes to existing error handling paths
- [ ] Code compiles without errors
- [ ] Mypy type checking passes

## Testing Strategy

### Manual Integration Testing
```bash
# Test implement workflow with label update
cd /path/to/feature/branch
mcp-coder implement --update-labels

# Verify:
# 1. Workflow completes successfully
# 2. Log shows "Updating GitHub issue label..."
# 3. GitHub issue label changed (check web UI)
# 4. If update fails, workflow still succeeds

# Repeat for create-plan and create-pr
```

### Code Quality Checks
```bash
# Type checking
mcp__code-checker__run_mypy_check()

# Code quality
mcp__code-checker__run_pylint_check()

# Fast unit tests (ensure no regression)
mcp__code-checker__run_pytest_check(
    extra_args=["-n", "auto", "-m", "not git_integration and not claude_integration and not formatter_integration and not github_integration"]
)
```

## Edge Cases Handled

| Scenario | Behavior |
|----------|----------|
| Flag not passed | Skip label update entirely (no log message) |
| Flag passed but branch name invalid | Log WARNING, continue workflow |
| Flag passed but branch not linked | Log WARNING, continue workflow |
| Flag passed but GitHub API fails | Log ERROR, continue workflow |
| Label already in correct state | Log INFO (idempotent), continue workflow |
| Exception during update | Caught, logged ERROR, continue workflow |

## Next Step Preview
**Step 5** will create comprehensive documentation and perform final validation testing to ensure the feature works end-to-end.

---

## LLM Prompt for This Step

```
You are implementing Step 4 of the auto-label update feature for mcp-coder.

CONTEXT:
Read pr_info/steps/summary.md for architectural overview.
This is the final integration step - connecting CLI flags to core functionality.

TASK:
Add label update calls to three workflow files at their success paths.

FILES TO MODIFY:
1. src/mcp_coder/workflows/implement/core.py
   - Location: End of run_implement_workflow(), after push, before return 0
   - Transition: implementing → code_review
   - Condition: update_labels AND completed_tasks > 0 AND not error_occurred

2. src/mcp_coder/workflows/create_plan.py
   - Location: End of run_create_plan_workflow(), after push, before final message
   - Transition: planning → plan_review
   - Condition: update_labels is True

3. src/mcp_coder/workflows/create_pr/core.py
   - Location: End of run_create_pr_workflow(), after cleanup, before final message
   - Transition: pr_creating → pr_created
   - Condition: update_labels is True

REQUIREMENTS:
- Use lazy import pattern (import inside if block)
- Identical error handling structure across all three
- Triple-layer safety: internal + try/except + non-blocking
- Consistent logging with ✓/✗ symbols and "(non-blocking)" suffix
- No changes to return values or existing error paths

CRITICAL:
Label update failures must NEVER fail the workflow. Always return 0 (success) if workflow reached this point.

REFERENCE THIS STEP:
pr_info/steps/step_4.md (contains exact code snippets and placement)

After implementation, run code quality checks:
1. mcp__code-checker__run_mypy_check
2. mcp__code-checker__run_pylint_check
3. mcp__code-checker__run_pytest_check (fast unit tests only)

Then perform manual integration testing if possible.
```
