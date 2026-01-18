# Step 1: Create issue_cache.py Module

## LLM Prompt

```
Read pr_info/steps/summary.md for context.

Implement Step 1: Create the new `src/mcp_coder/utils/github_operations/issue_cache.py` module.

Move the following from `src/mcp_coder/cli/commands/coordinator/core.py`:
- CacheData TypedDict
- _load_cache_file()
- _save_cache_file()
- _get_cache_file_path()
- _log_cache_metrics()
- _log_stale_cache_entries()
- _update_issue_labels_in_cache()

Create a NEW function `get_all_cached_issues()` by extracting the caching logic from 
`get_cached_eligible_issues()`. This function should:
- Handle all cache operations (load, save, refresh strategy, duplicate protection)
- Return ALL cached issues (unfiltered)
- NOT call _filter_eligible_issues (that stays in coordinator)

The filtering wrapper stays in coordinator/core.py (Step 2).

Do NOT modify coordinator/core.py in this step - only create the new module.
```

## WHERE

**New file**: `src/mcp_coder/utils/github_operations/issue_cache.py`

## WHAT

### TypedDict
```python
class CacheData(TypedDict):
    """Type definition for coordinator issue cache structure."""
    last_checked: Optional[str]
    issues: Dict[str, IssueData]
```

### Helper Functions to Move (unchanged)

```python
def _load_cache_file(cache_file_path: Path) -> CacheData:
    """Load cache file or return empty cache structure."""

def _save_cache_file(cache_file_path: Path, cache_data: CacheData) -> bool:
    """Save cache data to file using atomic write."""

def _get_cache_file_path(repo_identifier: RepoIdentifier) -> Path:
    """Get cache file path using RepoIdentifier."""

def _log_cache_metrics(action: str, repo_name: str, **kwargs: Any) -> None:
    """Log detailed cache performance metrics at DEBUG level."""

def _log_stale_cache_entries(
    cached_issues: Dict[str, IssueData], 
    fresh_issues: Dict[str, IssueData]
) -> None:
    """Log detailed staleness information when cached data differs."""

def _update_issue_labels_in_cache(
    repo_full_name: str, 
    issue_number: int, 
    old_label: str, 
    new_label: str
) -> None:
    """Update issue labels in cache after successful dispatch."""
```

### NEW Function: `get_all_cached_issues()`

```python
def get_all_cached_issues(
    repo_full_name: str,
    issue_manager: IssueManager,
    force_refresh: bool = False,
    cache_refresh_minutes: int = 1440,
) -> List[IssueData]:
    """Get all cached issues using cache for performance and duplicate protection.
    
    This function handles:
    - Cache loading and saving
    - Duplicate protection (skip if checked < 50 seconds ago)
    - Refresh strategy (full vs incremental based on age)
    - Fetching fresh issues from GitHub API
    - Merging fresh issues into cache
    
    Args:
        repo_full_name: Repository in "owner/repo" format
        issue_manager: IssueManager for GitHub API calls
        force_refresh: Bypass cache entirely
        cache_refresh_minutes: Full refresh threshold (default: 1440 = 24 hours)
    
    Returns:
        List of ALL cached issues (unfiltered). Caller is responsible for filtering.
        Returns empty list if duplicate protection triggers.
    
    Raises:
        CacheError: If cache operations fail (caller should handle fallback)
    """
```

## HOW

### Imports Required
```python
import json
import logging
from datetime import timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, TypedDict

from .github_utils import RepoIdentifier
from .issue_manager import IssueData, IssueManager
from ..timezone_utils import (
    format_for_cache,
    is_within_duration,
    now_utc,
    parse_iso_timestamp,
)
```

### Key Changes from Original

1. **`_update_issue_labels_in_cache`**: Remove late binding, call helpers directly:
   ```python
   # Before (in coordinator):
   cache_file_path = coordinator._get_cache_file_path(repo_identifier)
   
   # After (in issue_cache):
   cache_file_path = _get_cache_file_path(repo_identifier)
   ```

2. **`get_all_cached_issues`**: Extract from `get_cached_eligible_issues`, but:
   - Remove the `coordinator._filter_eligible_issues()` call
   - Remove the `coordinator.get_eligible_issues()` fallback
   - Return `list(cache_data["issues"].values())` directly
   - Let caller handle filtering and error fallback

### Constant to Define
```python
DUPLICATE_PROTECTION_SECONDS = 50  # From workflow_constants.py
```

## ALGORITHM

```
# get_all_cached_issues pseudocode:
1. Parse repo_full_name -> RepoIdentifier
2. Load cache file (or empty structure if not exists)
3. Check duplicate protection (return empty list if checked < 50 seconds ago)
4. Determine refresh strategy (full vs incremental based on age)
5. Fetch fresh issues from GitHub API
6. Merge fresh into cache, save cache
7. Return ALL cached issues (unfiltered)
```

## DATA

### CacheData Structure
```python
{
    "last_checked": "2025-01-03T10:30:00Z",  # ISO 8601 timestamp or None
    "issues": {
        "123": IssueData,  # issue_number as string key
        "456": IssueData,
    }
}
```

## TESTS

No test changes in this step - tests will be updated in Step 4.
