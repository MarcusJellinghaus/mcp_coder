# Step 3: Integration and Workflow Validation

## LLM Prompt
```
Review the summary at pr_info/steps/summary.md for context on Issue #231 coordinator cache invalidation.

Integrate the _update_issue_labels_in_cache() function from Step 2 into the execute_coordinator_run() workflow to fix the cache staleness issue.

Key requirements:
- Call cache update immediately after successful dispatch_workflow()
- Handle cache update failures gracefully (don't break main workflow)
- Validate the complete fix works end-to-end
- Add any missing error handling or logging
- Ensure integration follows existing patterns

Focus on the minimal integration point in execute_coordinator_run() around line 1300 where dispatch_workflow() is called.
```

## WHERE: File Location
- **Primary**: `src/mcp_coder/cli/commands/coordinator.py`
- **Function**: `execute_coordinator_run()` around line 1300
- **Section**: Step 4d - Dispatch workflows for each eligible issue

## WHAT: Integration Changes

### Core Integration Point
```python
# In execute_coordinator_run() - Step 4d section
try:
    dispatch_workflow(
        issue=issue,
        workflow_name=workflow_name,
        repo_config=validated_config,
        jenkins_client=jenkins_client,
        issue_manager=issue_manager,
        branch_manager=branch_manager,
        log_level=args.log_level,
    )
    
    # NEW: Update cache with new labels immediately after successful dispatch
    _update_issue_labels_in_cache(
        repo_full_name=repo_full_name,
        issue_number=issue["number"],
        old_label=current_label,
        new_label=workflow_config["next_label"]
    )
    
except Exception as e:
    # Existing error handling unchanged
    logger.error(f"Failed processing issue #{issue['number']}: {e}", exc_info=True)
    print(f"Error: Failed to process issue #{issue['number']}: {e}", file=sys.stderr)
    return 1
```

## HOW: Integration Details

### Context Variables Available
```python
# Already available in execute_coordinator_run() scope:
repo_full_name: str           # Created from repo_identifier  
issue: IssueData             # Current issue being processed
current_label: str           # Found in workflow loop
workflow_config: dict        # Contains "next_label"
```

### Error Handling Strategy
- Cache update happens AFTER successful `dispatch_workflow()`
- Cache failures logged but don't affect dispatch success
- Existing exception handling unchanged
- No new try/catch blocks needed

## ALGORITHM: Integration Logic

### Workflow Integration
```
1. execute_coordinator_run() processes each eligible issue
2. dispatch_workflow() succeeds → GitHub labels updated
3. _update_issue_labels_in_cache() → local cache updated
4. Continue to next issue OR handle dispatch failure
5. Cache stays synchronized with GitHub state
```

### Error Flow Handling
```
1. If dispatch_workflow() fails → cache not updated (correct)
2. If cache update fails → logged as warning, dispatch success preserved
3. If both fail → dispatch error takes priority (existing behavior)
4. Next cache refresh will fetch correct data from GitHub
```

## DATA: Integration Context

### Available Variables in Loop
```python
# From execute_coordinator_run() context:
for issue in eligible_issues:
    # Find current bot_pickup label to determine workflow  
    current_label = None
    for label in issue["labels"]:
        if label in WORKFLOW_MAPPING:
            current_label = label
            break
            
    workflow_config = WORKFLOW_MAPPING[current_label]
    workflow_name = workflow_config["workflow"]
    
    # Variables available for cache update:
    # - repo_full_name
    # - issue["number"] 
    # - current_label
    # - workflow_config["next_label"]
```

### Cache Update Parameters
```python
_update_issue_labels_in_cache(
    repo_full_name=repo_full_name,        # "owner/repo"
    issue_number=issue["number"],         # int
    old_label=current_label,              # "status-02:awaiting-planning"
    new_label=workflow_config["next_label"]  # "status-03:planning"
)
```

## Detailed Integration Implementation

### Exact Code Changes
```python
# In execute_coordinator_run() around line 1320-1350:

# Step 4d: Dispatch workflows for each eligible issue (fail-fast)
for issue in eligible_issues:
    # Find current bot_pickup label to determine workflow
    current_label = None
    for label in issue["labels"]:
        if label in WORKFLOW_MAPPING:
            current_label = label
            break

    if not current_label:
        logger.error(
            f"Issue #{issue['number']} has no workflow label, skipping"
        )
        continue

    workflow_config = WORKFLOW_MAPPING[current_label]
    workflow_name = workflow_config["workflow"]

    try:
        dispatch_workflow(
            issue=issue,
            workflow_name=workflow_name,
            repo_config=validated_config,
            jenkins_client=jenkins_client,
            issue_manager=issue_manager,
            branch_manager=branch_manager,
            log_level=args.log_level,
        )
        
        # UPDATE CACHE: Synchronize local cache with GitHub label changes
        _update_issue_labels_in_cache(
            repo_full_name=repo_full_name,
            issue_number=issue["number"],
            old_label=current_label,
            new_label=workflow_config["next_label"]
        )
        
    except Exception as e:
        # Fail-fast: log error and exit immediately
        logger.error(
            f"Failed processing issue #{issue['number']}: {e}",
            exc_info=True,
        )
        print(
            f"Error: Failed to process issue #{issue['number']}: {e}",
            file=sys.stderr,
        )
        return 1
```

## Validation Requirements

### End-to-End Testing
1. **Before Fix**: Cache contains stale labels → duplicate dispatch possible
2. **After Integration**: Cache updated immediately → duplicate dispatch prevented
3. **Error Cases**: Cache update failures don't break dispatch workflow

### Integration Tests to Add
```python
def test_execute_coordinator_run_updates_cache_after_dispatch(self):
    """Test that successful dispatch updates cache labels."""
    
def test_cache_update_failure_does_not_break_dispatch(self):  
    """Test that cache update errors don't affect dispatch success."""
    
def test_multiple_dispatches_keep_cache_synchronized(self):
    """Test processing multiple issues keeps cache in sync."""
```

### Manual Validation Scenarios
1. **Single Issue**: Dispatch one issue, verify cache updated
2. **Multiple Issues**: Process several issues, verify all cache updates
3. **Cache Error**: Simulate cache permission error, verify dispatch still works
4. **Duplicate Protection**: Run twice within 1-minute window, verify no duplicates

## Success Criteria

### Functional Requirements
- ✅ Cache updated immediately after successful dispatch
- ✅ Cache failures don't break dispatch workflow  
- ✅ Duplicate dispatches prevented within 1-minute window
- ✅ Integration follows existing error handling patterns

### Non-Functional Requirements
- ✅ Minimal code changes (< 10 lines added)
- ✅ No performance impact (single file operation)
- ✅ Backward compatible (no breaking changes)
- ✅ Follows existing logging and error patterns

### Issue Resolution
- ✅ **Root Cause Fixed**: Cache staleness after label changes
- ✅ **Requirements Met**: No duplicate dispatches in protection window
- ✅ **Implementation Approach**: Simple, robust, maintainable
- ✅ **Integration Quality**: Clean, minimal, follows existing patterns