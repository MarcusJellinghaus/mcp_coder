# Step 5: Add TypedDict for Cache Data Structure

## LLM Prompt
```
Review the summary at pr_info/steps/summary.md for context on Issue #231 coordinator cache invalidation.

Implement a TypedDict for the cache data structure to improve type safety across cache-related functions.

Focus on:
- Define CacheData TypedDict with proper field types
- Update function signatures to use CacheData instead of Dict[str, Any]
- Ensure mypy passes with the new types
- Follow existing codebase patterns for TypedDict usage

Reference Decision 10 in pr_info/steps/Decisions.md for context on this change.
```

## WHERE: File Locations
- **Primary**: `src/mcp_coder/cli/commands/coordinator.py`
- **Tests**: `tests/utils/test_coordinator_cache.py` (verify existing tests still pass)

## WHAT: Type Definition and Function Signature Updates

### New TypedDict Definition
```python
from typing import TypedDict

class CacheData(TypedDict):
    """Type definition for coordinator issue cache structure.
    
    Attributes:
        last_checked: ISO 8601 timestamp of last cache refresh, or None if never checked
        issues: Dictionary mapping issue number (as string) to IssueData
    """
    last_checked: Optional[str]
    issues: Dict[str, IssueData]
```

### Functions to Update
```python
def _load_cache_file(cache_file_path: Path) -> CacheData:
    ...

def _save_cache_file(cache_file_path: Path, cache_data: CacheData) -> bool:
    ...

# Internal usage in these functions (no signature change needed):
# - _update_issue_labels_in_cache()
# - get_cached_eligible_issues()
# - _log_stale_cache_entries()
```

## HOW: Integration Points

### Imports to Add/Modify
```python
# Update existing import line
from typing import Any, Dict, List, Optional, TypedDict
```

### Placement
- Add `CacheData` TypedDict definition after the existing imports
- Place near other type definitions or constants at module level
- Position before the cache helper functions that use it

## ALGORITHM: Implementation Steps

```
1. Add TypedDict import to typing imports
2. Define CacheData TypedDict after imports section
3. Update _load_cache_file return type: Dict[str, Any] -> CacheData
4. Update _save_cache_file parameter type: Dict[str, Any] -> CacheData
5. Run mypy to verify type consistency
6. Run existing tests to ensure no regressions
```

## DATA: Type Structure

### CacheData Structure
```python
CacheData = {
    "last_checked": Optional[str],  # ISO 8601 timestamp or None
    "issues": Dict[str, IssueData]  # issue_number (str) -> IssueData
}
```

### Example Cache Data
```python
{
    "last_checked": "2025-01-03T10:30:00+00:00",
    "issues": {
        "123": {
            "number": 123,
            "state": "open",
            "labels": ["status-02:awaiting-planning", "bug"],
            "updated_at": "2025-01-03T09:00:00Z",
            "url": "https://github.com/test/repo/issues/123",
            "title": "Test issue",
            "body": "Test issue body",
            "assignees": [],
            "user": "testuser",
            "created_at": "2025-01-03T08:00:00Z",
            "locked": False,
        }
    }
}
```

## Success Criteria

### Type Safety
- mypy passes with no new errors
- Function signatures clearly indicate cache data structure
- IDE autocompletion works for cache data fields

### Backward Compatibility
- All existing tests pass without modification
- No runtime behavior changes
- Cache files remain compatible (same JSON structure)

### Code Quality
- TypedDict follows existing patterns in codebase
- Clear docstring explaining the type structure
- Minimal changes to existing code

## Implementation Notes

### Why TypedDict over dataclass/NamedTuple
- Cache data is loaded from/saved to JSON - TypedDict maps naturally
- Existing code uses dictionary access patterns (`cache_data["issues"]`)
- No need for methods or computed properties
- TypedDict provides type hints without runtime overhead

### Considerations
- `IssueData` is already defined in `issue_manager.py` as a TypedDict
- Cache structure mirrors what's stored in JSON files
- No changes needed to cache file format or storage logic
