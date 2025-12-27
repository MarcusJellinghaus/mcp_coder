# Step 3: Add Configuration Support

## Objective
Add configuration support for `cache_refresh_minutes` setting and `--force-refresh` CLI flag.

## LLM Prompt
```
Based on the GitHub API caching implementation summary, implement Step 3: Configuration support for caching.

Requirements:
- Add `cache_refresh_minutes` configuration reading to coordinator
- Add `--force-refresh` CLI flag to coordinator run command
- Follow existing configuration patterns in the codebase
- Ensure backward compatibility with existing configs
- Write tests first following TDD approach

Refer to the summary document and previous steps for context.
```

## WHERE
- **File**: `src/mcp_coder/cli/commands/coordinator.py` (argument parsing)
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

### Test Functions
```python
def test_coordinator_run_force_refresh_flag()
def test_coordinator_run_cache_config_default()
def test_coordinator_run_cache_config_custom()
def test_coordinator_run_missing_cache_config()
```

## HOW
### Integration Points
- **Import**: Use existing `from ...utils.user_config import get_config_value`
- **CLI Parser**: Modify existing `coordinator` subcommand argument setup
- **Config Section**: `[coordinator]` section, key `cache_refresh_minutes`

### Argument Parser Integration
```python
# Add to existing run_parser in coordinator command setup
run_parser.add_argument("--force-refresh", action="store_true", 
                       help="Force full cache refresh, bypass all caching")
```

## ALGORITHM
```
1. Add --force-refresh flag to existing coordinator run argument parser
2. Create config reading function using existing get_config_value pattern
3. Pass both values to get_cached_eligible_issues() function
4. Handle missing config gracefully with default value (1440 minutes)
5. Validate config value is positive integer, use default on invalid
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

### Configuration Reading
```python
def get_cache_refresh_minutes() -> int:
    """Returns cache_refresh_minutes from config or default 1440"""
```

## Implementation Notes
- **Backward compatible**: Missing config section/key uses default value
- **Validation**: Invalid config values (negative, non-integer) fall back to default
- **Consistent patterns**: Uses same config reading approach as existing coordinator settings
- **Minimal scope**: Only adds necessary configuration, no over-engineering
- **Error handling**: Config reading errors are logged but don't prevent execution