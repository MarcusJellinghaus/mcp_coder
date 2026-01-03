# Issue #231: Coordinator Cache Invalidation Implementation

## Problem Statement

The coordinator's issue cache becomes stale after `dispatch_workflow()` changes labels on GitHub, causing potential duplicate workflow dispatches within the 1-minute duplicate protection window.

**Root Cause**: Cache is populated before dispatch, but label changes made during dispatch are not reflected in the local cache.

## Solution Overview

Implement **in-place cache label updates** immediately after successful workflow dispatch to keep cache synchronized with GitHub state.

### Design Decision: Update vs Remove

**Chosen Approach**: Update issue labels in cache (not remove entire issue)
- **Rationale**: More precise, preserves data integrity, easier debugging
- **Simplicity**: Single function, clear intent, minimal code changes
- **Maintainability**: Explicit about what changed, preserves metadata

## Architectural Changes

### Core Changes
1. **New Function**: `_update_issue_labels_in_cache()` - Updates cached issue labels after successful dispatch
2. **Integration Point**: `execute_coordinator_run()` - Calls cache update immediately after `dispatch_workflow()`
3. **Error Handling**: Cache update failures do not break main workflow

### Design Principles Applied
- **KISS Principle**: Single-purpose function, minimal complexity
- **Fail-Safe**: Cache errors don't affect workflow dispatch
- **Data Integrity**: Only updates what actually changed
- **Backward Compatibility**: No changes to existing cache structure or API

## Files Modified

### Core Implementation
- **`src/mcp_coder/cli/commands/coordinator.py`**
  - Add `_update_issue_labels_in_cache()` function
  - Integrate cache update in `execute_coordinator_run()`

### Test Implementation  
- **`tests/utils/test_coordinator_cache.py`**
  - Add tests for `_update_issue_labels_in_cache()`
  - Add integration tests for cache update in dispatch flow

### Documentation
- **`pr_info/steps/summary.md`** (this file)
- **`pr_info/steps/step_1.md`** - Test implementation
- **`pr_info/steps/step_2.md`** - Function implementation
- **`pr_info/steps/step_3.md`** - Integration and validation

## Implementation Strategy

### Test-Driven Development Approach
1. **Step 1**: Write comprehensive tests for cache update functionality
2. **Step 2**: Implement `_update_issue_labels_in_cache()` function
3. **Step 3**: Integrate cache update into dispatch workflow and validate

### Key Benefits
- **Prevents Duplicate Dispatches**: Cache reflects actual GitHub state
- **Preserves Performance**: No additional API calls required
- **Maintains Compatibility**: Existing cache structure unchanged
- **Simple Integration**: Single function call after dispatch
- **Robust Error Handling**: Cache failures don't break workflows

## Expected Behavior After Implementation

### Scenario: Successful Workflow Dispatch
1. **Before**: Cache contains issue with `status-02:awaiting-planning`
2. **Dispatch**: `dispatch_workflow()` changes GitHub labels: `status-02` → `status-03`
3. **Cache Update**: Local cache immediately updated with new labels
4. **Subsequent Run**: Within 1-minute window, cache has correct labels, no duplicate dispatch

### Integration with Existing `since` Logic
- **Run 1**: Cache updated in-place after dispatch
- **Run 2**: If within duplicate protection, uses updated cache (correct behavior)
- **Run 3**: If beyond protection window, `since` parameter fetches any additional GitHub changes

## Testing Strategy

### Unit Tests
- Cache update with valid issue and labels
- Cache update with missing issue (graceful handling)
- Cache update with invalid cache structure (error handling)
- Label operations (add/remove/replace scenarios)

### Integration Tests  
- End-to-end dispatch + cache update workflow
- Multiple issues processed in sequence
- Cache persistence across function calls
- Error scenarios (file permissions, corrupted cache)

## Risk Mitigation

### Minimal Risk Implementation
- **No Breaking Changes**: Existing cache API unchanged
- **Graceful Degradation**: Cache update failures logged, don't break dispatch
- **Backward Compatibility**: Works with existing cache files
- **Isolated Changes**: Single module modification, clear scope

### Rollback Strategy
- Changes are additive only - can be easily reverted
- No database schema or external API changes
- Self-contained function can be disabled if needed