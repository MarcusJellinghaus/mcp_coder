# Step 4: Integrate Cache into Coordinator

## Objective
Integrate the caching function into the coordinator run command, replacing the current direct `get_eligible_issues()` calls.

## LLM Prompt
```
Based on the GitHub API caching implementation summary, implement Step 4: Integrate cache into coordinator workflow.

Requirements:
- Replace get_eligible_issues() call with get_cached_eligible_issues() 
- Pass configuration and CLI flags to cache function
- Maintain existing error handling and logging patterns
- Ensure backward compatibility - cache failures fall back to current behavior
- Write integration tests following TDD approach

Use components from Steps 1-3. Refer to summary document for architecture context.
```

## WHERE  
- **File**: `src/mcp_coder/cli/commands/coordinator.py` 
- **Function**: `execute_coordinator_run()` (line ~614)
- **Test File**: `tests/cli/commands/test_coordinator.py`

## WHAT
### Modified Function Call
```python
# Replace this line in execute_coordinator_run():
# eligible_issues = get_eligible_issues(issue_manager)

# With this:
eligible_issues = get_cached_eligible_issues(
    repo_name=repo_name,
    issue_manager=issue_manager, 
    force_refresh=args.force_refresh,
    cache_refresh_minutes=get_cache_refresh_minutes()
)
```

### Test Functions  
```python
def test_coordinator_run_with_cache_success()
def test_coordinator_run_with_cache_fallback()
def test_coordinator_run_force_refresh_integration()
def test_coordinator_run_multiple_repos_caching()
```

## HOW
### Integration Points
- **Location**: In `execute_coordinator_run()` within the repo processing loop
- **Error Handling**: Wrap cache call in try-except, fallback to existing `get_eligible_issues()`
- **Logging**: Use existing logger for cache-related messages

### Fallback Strategy
```python
try:
    eligible_issues = get_cached_eligible_issues(
        repo_name, issue_manager, args.force_refresh, get_cache_refresh_minutes()
    )
except Exception as e:
    logger.warning(f"Cache failed for {repo_name}: {e}, using direct fetch")
    eligible_issues = get_eligible_issues(issue_manager)
```

## ALGORITHM
```
1. Get cache configuration (refresh minutes) using config reading function
2. Call get_cached_eligible_issues() with repo name and cache settings
3. If cache function raises any exception, catch and log warning
4. Fall back to existing get_eligible_issues() call on any cache error
5. Continue with existing workflow logic using eligible_issues list
```

## DATA
### Input Changes
- **Added**: `args.force_refresh` from CLI arguments
- **Added**: `cache_refresh_minutes` from configuration
- **Added**: `repo_name` (already available in loop context)

### Return Value
- **Same**: `List[IssueData]` - No change to downstream processing
- **Behavior**: Cache optimization is transparent to rest of workflow

### Error Scenarios
- **Cache file corruption**: Logs warning, falls back to direct fetch
- **Permission errors**: Logs warning, falls back to direct fetch  
- **Network timeouts**: Existing error handling in get_eligible_issues()
- **GitHub API errors**: Existing error handling in IssueManager

## Implementation Notes
- **Zero breaking changes**: Existing behavior preserved on any cache failure
- **Transparent optimization**: Rest of coordinator logic unchanged
- **Fail-safe design**: Cache errors never prevent workflow execution
- **Minimal integration**: Only 4-5 lines changed in execute_coordinator_run()
- **Consistent logging**: Uses existing logger and log levels