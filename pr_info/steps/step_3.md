# Step 3: Configuration, CLI Flag, and Integration

## Objective
Add configuration support, CLI flag, and integrate the cache into the coordinator workflow.

## LLM Prompt
```
Based on the GitHub API caching implementation summary, implement Step 3: Configuration, CLI flag, and integration.

Requirements:
- Add `cache_refresh_minutes` configuration reading to coordinator
- Add `--force-refresh` CLI flag to coordinator run command
- Integrate get_cached_eligible_issues() into execute_coordinator_run()
- Replace direct get_eligible_issues() call with cached version
- Ensure graceful fallback on any cache errors
- Follow existing configuration patterns in the codebase
- Ensure backward compatibility with existing configs
- Write tests first following TDD approach

Use components from Steps 1-2. Refer to summary document for architecture context.
```

## WHERE
- **File**: `src/mcp_coder/cli/commands/coordinator.py` (argument parsing + integration)
- **Test File**: `tests/cli/commands/test_coordinator.py` (existing file)
- **Config System**: Uses existing `utils/user_config.py` patterns

## WHAT

### CLI Argument Addition
```python
# In coordinator subparser setup
run_parser.add_argument(
    "--force-refresh", 
    action="store_true",
    help="Force full cache refresh, bypass all caching"
)
```

### Configuration Reading
```python
def get_cache_refresh_minutes() -> int:
    """Get cache refresh threshold from config with default fallback."""
```

### Integration Change
```python
# In execute_coordinator_run(), replace:
# eligible_issues = get_eligible_issues(issue_manager)

# With:
eligible_issues = get_cached_eligible_issues(
    repo_name=repo_name,
    issue_manager=issue_manager, 
    force_refresh=args.force_refresh,
    cache_refresh_minutes=get_cache_refresh_minutes()
)
```

### Test Functions
```python
# Configuration tests
def test_coordinator_run_force_refresh_flag()
def test_coordinator_run_cache_config_default()
def test_coordinator_run_cache_config_custom()
def test_coordinator_run_missing_cache_config()

# Integration tests
def test_coordinator_run_with_cache_success()
def test_coordinator_run_with_cache_fallback()
def test_coordinator_run_force_refresh_integration()
def test_coordinator_run_multiple_repos_caching()
```

## HOW

### Integration Points
- **Import**: Use existing `from ...utils.user_config import get_config_value`
- **CLI Parser**: Modify existing `coordinator` subcommand argument setup
- **Config Section**: `[coordinator]` section, key `cache_refresh_minutes`
- **Location**: In `execute_coordinator_run()` within the repo processing loop

### Argument Parser Integration
```python
# Add to existing run_parser in coordinator command setup
run_parser.add_argument("--force-refresh", action="store_true", 
                       help="Force full cache refresh, bypass all caching")
```

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
1. Add --force-refresh flag to existing coordinator run argument parser
2. Create config reading function using existing get_config_value pattern
3. In execute_coordinator_run(), get cache configuration
4. Call get_cached_eligible_issues() with repo name and cache settings
5. If cache function raises any exception, catch and log warning
6. Fall back to existing get_eligible_issues() call on any cache error
7. Continue with existing workflow logic using eligible_issues list
```

## DATA

### CLI Arguments
- `args.force_refresh: bool` - Added to existing coordinator run namespace

### Configuration
- **Section**: `[coordinator]`
- **Key**: `cache_refresh_minutes`  
- **Type**: `int`
- **Default**: `1440` (24 hours)
- **Validation**: Must be positive integer

### Example Config
```toml
[coordinator]
cache_refresh_minutes = 720  # 12 hours
```

### Input Changes to execute_coordinator_run()
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
- **Backward compatible**: Missing config section/key uses default value
- **Validation**: Invalid config values (negative, non-integer) fall back to default
- **Consistent patterns**: Uses same config reading approach as existing coordinator settings
- **Zero breaking changes**: Existing behavior preserved on any cache failure
- **Transparent optimization**: Rest of coordinator logic unchanged
- **Fail-safe design**: Cache errors never prevent workflow execution
- **Minimal integration**: Only ~10-15 lines changed in execute_coordinator_run()
- **Consistent logging**: Uses existing logger and log levels
