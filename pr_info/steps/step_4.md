# Step 4: Cache Robustness and Metrics Improvements

## Objective
Improve cache robustness with better URL parsing, fallback logic, and add performance metrics logging based on code review findings.

## LLM Prompt
```
Based on the GitHub API caching implementation summary and code review findings, implement Step 4: Cache robustness and metrics improvements.

Requirements:
- Fix repo URL parsing with owner=None fallback handling
- Add warning logging for cache naming fallback scenarios
- Add detailed cache performance metrics at DEBUG level
- Improve cache file naming for edge cases
- Follow existing code patterns and error handling in coordinator.py
- Write comprehensive tests first (TDD approach)

Refer to the summary document and previous steps for overall context and architecture decisions.
```

## WHERE
- **File**: `src/mcp_coder/cli/commands/coordinator.py`
- **Test File**: `tests/utils/test_coordinator_cache.py` (extend existing)

## WHAT
### Enhanced Helper Functions
```python
def _parse_repo_identifier(repo_url: str, repo_name: str) -> tuple[str, str | None]:
    """Parse repository URL to extract owner and repo name with fallback."""

def _get_cache_file_path(repo_full_name: str, owner: str | None = None) -> Path:
    """Get cache file path with enhanced naming for missing owner."""

def _log_cache_metrics(action: str, repo_name: str, **kwargs) -> None:
    """Log detailed cache performance metrics at DEBUG level."""
```

### Enhanced Main Function
```python
def get_cached_eligible_issues(
    repo_full_name: str,
    issue_manager: IssueManager,
    force_refresh: bool = False,
    cache_refresh_minutes: int = 1440,
) -> List[IssueData]:
    """Enhanced with robust URL parsing and metrics logging."""
```

### Test Functions
```python
def test_parse_repo_identifier_standard_url()
def test_parse_repo_identifier_ssh_url()
def test_parse_repo_identifier_no_owner_fallback()
def test_cache_file_path_with_owner_none()
def test_cache_metrics_logging_hit_miss()
def test_get_cached_eligible_issues_url_parsing_fallback()
```

## HOW
### Integration Points
- **Imports**: Existing imports in coordinator.py, no new dependencies
- **Position**: Modify existing helper functions and add new ones before `get_cached_eligible_issues()`
- **Logging**: Use existing `logger` instance from coordinator.py
- **Error Handling**: Maintain existing broad exception handling with enhanced logging

### URL Parsing Enhancement
```python
def _parse_repo_identifier(repo_url: str, repo_name: str) -> tuple[str, str | None]:
    """Parse various Git URL formats to extract owner and repo."""
    # Handle https://github.com/owner/repo.git
    # Handle git@github.com:owner/repo.git  
    # Handle other formats
    # Return (repo_name, owner) or (repo_name, None)
```

## ALGORITHM
```
1. Parse repo_url using multiple patterns (HTTPS, SSH, etc.)
2. Extract owner and repo components, set owner=None if extraction fails
3. Log warning if falling back to owner=None naming
4. Generate cache file path using enhanced naming: "repo.issues.json" vs "owner_repo.issues.json" 
5. Add DEBUG logging for all cache operations (hit/miss/age/count)
6. Maintain existing cache logic with enhanced observability
```

## DATA
### Input Parameters
- `repo_url: str` - Repository URL in various formats
- `repo_name: str` - Repository name for fallback
- `repo_full_name: str` - Expected "owner/repo" format, but now handles edge cases

### Return Values
- `_parse_repo_identifier()` returns `tuple[str, str | None]` - (repo_name, owner)
- `get_cached_eligible_issues()` returns `List[IssueData]` - Same as before
- Cache file naming: `"owner_repo.issues.json"` or `"repo.issues.json"`

### Enhanced Logging
```python
# DEBUG level metrics logging
logger.debug(f"Cache hit for {repo_name}: age={cache_age_minutes}m, issues={issue_count}")
logger.debug(f"Cache miss for {repo_name}: reason='{miss_reason}'")
logger.warning(f"Using fallback cache naming for {repo_name}: owner could not be determined from URL {repo_url}")
```

### Error Handling
- **URL parsing failures**: Set owner=None, log warning, continue with fallback naming
- **Cache corruption**: Existing broad exception handler with enhanced logging
- **File I/O errors**: Existing graceful degradation to `get_eligible_issues()`

## Implementation Notes
- **Backward compatible**: Existing "owner_repo.issues.json" files continue to work
- **Enhanced observability**: DEBUG logging helps validate caching effectiveness
- **Robust fallback**: Handles edge cases in repository URL formats
- **Minimal complexity**: Builds on existing patterns without major architectural changes
- **Test coverage**: Comprehensive tests for new URL parsing and edge case scenarios