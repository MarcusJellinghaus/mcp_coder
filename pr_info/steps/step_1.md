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
- get_cached_eligible_issues()

Keep `_filter_eligible_issues` in coordinator/core.py (it has coordinator-specific logic).

The new module should:
1. Import dependencies directly (no late binding needed for most functions)
2. Accept `filter_fn` as a parameter to `get_cached_eligible_issues()` to call back to coordinator's `_filter_eligible_issues`
3. Maintain the same function signatures and behavior

Do NOT modify any other files in this step.
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

### Functions to Move

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

def get_cached_eligible_issues(
    repo_full_name: str,
    issue_manager: IssueManager,
    filter_fn: Callable[[List[IssueData]], List[IssueData]],
    fallback_fn: Callable[[IssueManager], List[IssueData]],
    force_refresh: bool = False,
    cache_refresh_minutes: int = 1440,
) -> List[IssueData]:
    """Get eligible issues using cache for performance and duplicate protection."""
```

## HOW

### Imports Required
```python
import json
import logging
from datetime import timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TypedDict

from ..github_operations.github_utils import RepoIdentifier
from ..github_operations.issue_manager import IssueData, IssueManager
from ..timezone_utils import (
    format_for_cache,
    is_within_duration,
    now_utc,
    parse_iso_timestamp,
)
```

### Key Change: Callback Pattern

The `get_cached_eligible_issues` function needs two callbacks:
- `filter_fn`: To filter eligible issues (calls coordinator's `_filter_eligible_issues`)
- `fallback_fn`: For error fallback (calls coordinator's `get_eligible_issues`)

This avoids circular imports since issue_cache is in a lower layer than coordinator.

## ALGORITHM

```
# get_cached_eligible_issues pseudocode:
1. Parse repo_full_name -> RepoIdentifier
2. Load cache file (or empty structure if not exists)
3. Check duplicate protection (skip if checked < 50 seconds ago)
4. Determine refresh strategy (full vs incremental based on age)
5. Fetch fresh issues from GitHub API
6. Merge fresh into cache, save cache
7. Call filter_fn to get eligible issues
8. Return filtered list
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

### Constants (from workflow_constants.py)
```python
DUPLICATE_PROTECTION_SECONDS = 50  # Import from coordinator or define locally
```

## TESTS

No test changes in this step - tests will be updated in Step 3.
