# Step 2: Replace _parse_repo_identifier with Simple String Split

## Overview
Replace the complex URL parsing logic in `get_cached_eligible_issues()` with simple string operations that work directly with the "owner/repo" format.

## LLM Prompt
```
Implement the simplified repository identifier parsing in get_cached_eligible_issues() as specified in pr_info/steps/summary.md.

Requirements:
1. Replace the problematic _parse_repo_identifier() call with simple string split
2. Handle edge cases (no slash, multiple slashes)
3. Ensure cache file naming continues to work correctly
4. Maintain the same function signature and return values
5. Run the tests from Step 1 to verify behavior

The goal is to eliminate spurious warnings while preserving all existing functionality.
```

## WHERE: File Paths
- **Primary**: `src/mcp_coder/cli/commands/coordinator.py`
- **Function**: `get_cached_eligible_issues()` around lines 614-618

## WHAT: Main Functions

### Function to Modify
```python
def get_cached_eligible_issues(
    repo_full_name: str,
    issue_manager: IssueManager,
    force_refresh: bool = False,
    cache_refresh_minutes: int = 1440,
) -> List[IssueData]:
```

### Logic Replacement
```python
# REPLACE lines ~614-618:
# OLD CODE:
# repo_url = getattr(issue_manager, "repo_url", repo_full_name)
# if not isinstance(repo_url, str):
#     repo_url = repo_full_name
# repo_name, owner = _parse_repo_identifier(repo_url, repo_full_name)

# NEW CODE:
if "/" in repo_full_name:
    owner, repo_name = repo_full_name.split("/", 1)
else:
    owner, repo_name = None, repo_full_name
```

## HOW: Integration Points
- **Imports**: No new imports needed
- **Function Signature**: Unchanged - maintains backward compatibility
- **Error Handling**: Leverage existing try/catch in the function
- **Cache Logic**: Existing `_get_cache_file_path()` call remains unchanged

## ALGORITHM: Core Logic
```python
# Repository identifier parsing:
1. Check if repo_full_name contains "/"
2. If yes: split on first "/" to get (owner, repo_name)
3. If no: set owner=None, repo_name=repo_full_name  
4. Pass to existing _get_cache_file_path() function
5. Continue with existing cache logic unchanged
```

## DATA: Return Values and Structures

### Input Parameters (Unchanged)
- `repo_full_name: str` - Expected format: "owner/repo" 
- `issue_manager: IssueManager` - GitHub API client
- `force_refresh: bool` - Cache bypass flag
- `cache_refresh_minutes: int` - Cache expiration threshold

### Output (Unchanged)
- `List[IssueData]` - Same format as before
- **Side Effects**: Cache file with correct naming, no spurious warnings

### Variable Changes
```python
# Before:
repo_url: str = "owner/repo" (fallback value)
repo_name: str, owner: Optional[str] = _parse_repo_identifier(...)

# After: 
owner: Optional[str] = "owner" or None
repo_name: str = "repo" or full string
```

## Implementation Notes

### Edge Case Handling
- **Multiple slashes**: `split("/", 1)` handles "owner/repo/extra" → ("owner", "repo/extra")
- **No slash**: Direct assignment to repo_name, owner=None
- **Empty string**: Handled by existing validation in cache logic

### Backward Compatibility
- **Function signature**: Unchanged
- **Return format**: Identical to existing
- **Cache file naming**: Same pattern via `_get_cache_file_path()`

### Error Resilience
- **Invalid inputs**: Existing try/catch block handles edge cases
- **Fallback behavior**: Maintains graceful degradation to direct API calls