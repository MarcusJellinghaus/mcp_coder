# Step 2: Implement Core Cache Logic

## Objective
Create the core caching function `get_cached_eligible_issues()` that handles cache storage, duplicate protection, and incremental fetching.

## LLM Prompt
```
Based on the GitHub API caching implementation summary, implement Step 2: Core cache logic function.

Requirements:
- Implement `get_cached_eligible_issues()` function in coordinator.py
- Handle cache file storage in ~/.mcp_coder/coordinator_cache/
- Implement 1-minute duplicate protection per repository
- Support incremental vs full refresh logic
- Include comprehensive error handling with graceful fallback
- Write tests first following TDD approach

Use the extended `list_issues()` method with `since` parameter from Step 1. Refer to the summary for architecture context.
```

## WHERE
- **File**: `src/mcp_coder/cli/commands/coordinator.py`
- **Test File**: `tests/utils/test_coordinator_cache.py` (new file)

## WHAT
### Core Function
```python
def get_cached_eligible_issues(
    repo_full_name: str,  # Format: "owner/repo"
    issue_manager: IssueManager, 
    force_refresh: bool = False,
    cache_refresh_minutes: int = 1440
) -> List[IssueData]:
```

### Helper Functions
```python
def _load_cache_file(cache_file_path: Path) -> dict
def _save_cache_file(cache_file_path: Path, cache_data: dict) -> bool  # Uses atomic write
def _get_cache_file_path(repo_full_name: str) -> Path  # repo_full_name is "owner/repo" format
def _log_stale_cache_entries(cached_issues: dict, fresh_issues: dict) -> None  # Detailed staleness logging
```

### Test Functions
```python
def test_get_cached_eligible_issues_first_run()
def test_get_cached_eligible_issues_incremental_update()
def test_get_cached_eligible_issues_full_refresh()
def test_get_cached_eligible_issues_duplicate_protection()
def test_get_cached_eligible_issues_force_refresh()
def test_get_cached_eligible_issues_corrupted_cache()
def test_staleness_logging_detects_label_changes()
def test_staleness_logging_detects_missing_issues()
```

## HOW
### Integration Points
- **Imports**: `from datetime import datetime, timedelta`, `from pathlib import Path`, `import json`
- **Position**: Add before `execute_coordinator_run()` function
- **Cache directory**: `Path.home() / ".mcp_coder" / "coordinator_cache"`
- **Cache file naming**: Use full repo identifier `owner_repo.issues.json` (derived from `owner/repo` by replacing `/` with `_`)

### Cache File Format
```json
{
  "last_checked": "2025-12-27T10:30:00Z",
  "issues": {
    "123": {"number": 123, "state": "open", "labels": ["bug"], "updated_at": "2025-12-27T09:00:00Z"}
  }
}
```

## ALGORITHM
```
1. Check duplicate protection: if last_checked < 1 minute ago, return empty list [] (skip processing this repo)
2. Load existing cache file or create empty cache structure
3. Determine refresh strategy: incremental vs full based on cache age
4. Fetch issues using appropriate method (since vs full)
5. On full refresh: compare cached vs fresh issues, log any staleness detected
6. Merge fetched issues with cached issues, update cache (atomic write)
7. Filter cached issues for state="open" and apply eligibility rules
```

## DATA
### Input Parameters
- `repo_full_name: str` - Full repository identifier in "owner/repo" format (e.g., "anthropics/claude-code")
- `issue_manager: IssueManager` - For GitHub API calls  
- `force_refresh: bool = False` - Bypass cache entirely
- `cache_refresh_minutes: int = 1440` - Full refresh threshold

### Return Value  
- `List[IssueData]` - Eligible issues (open state, meeting bot pickup criteria)

### Cache Data Structure
```python
CacheData = {
    "last_checked": str,  # ISO format datetime
    "issues": Dict[str, IssueData]  # issue_number -> IssueData
}
```

### Error Handling
- **Cache corruption**: Delete cache file, proceed with full fetch
- **Permission errors**: Log warning, proceed with full fetch (no cache)
- **JSON errors**: Log warning, recreate cache file
- **All errors**: Fall back to existing `get_eligible_issues()` behavior

### Staleness Logging (on full refresh)
Log each stale cache entry with details of what changed:
```
Issue #42: cached labels ['status-02:awaiting-planning'] != actual ['status-03:planning']
Issue #17: cached state 'open' != actual 'closed'
Issue #55: no longer exists in repository
```

## Implementation Notes
- **Pure function**: No side effects except cache file I/O
- **Graceful degradation**: Any error returns same result as current implementation
- **Atomic file writes**: Write to temp file, then rename to prevent corruption on crash/interruption:
  ```python
  # Atomic write pattern - prevents partial writes on crash
  temp_path = cache_path.with_suffix('.tmp')
  temp_path.write_text(json.dumps(cache_data, indent=2))
  temp_path.replace(cache_path)  # Atomic rename
  ```
- **Detailed staleness logging**: On full refresh, compare cached vs fresh and log each discrepancy at INFO level
- **Minimal logging**: INFO for skips and staleness, DEBUG for cache hits, WARNING for errors