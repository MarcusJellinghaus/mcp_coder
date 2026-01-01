# Step 2: Implement Simplified Repository Identifier Handling

## Overview
Replace the complex URL parsing logic with a simple `_split_repo_identifier()` function, remove the old `_parse_repo_identifier()` function, simplify `_get_cache_file_path()` by removing the unused `owner` parameter, and simplify the exception handler.

## LLM Prompt
```
Implement the simplified repository identifier handling as specified in pr_info/steps/summary.md.

Requirements:
1. Add new _split_repo_identifier() function that splits "owner/repo" into (owner, repo_name)
2. Replace the _parse_repo_identifier() call in get_cached_eligible_issues() with the new function
3. Delete the entire _parse_repo_identifier() function
4. Simplify the exception handler to use repo_full_name directly for logging
5. Run the tests from Step 1 to verify behavior

The goal is to eliminate spurious warnings while preserving all existing functionality.
```

## WHERE: File Paths
- **Primary**: `src/mcp_coder/cli/commands/coordinator.py`
- **Functions to modify**: `get_cached_eligible_issues()`
- **Function to add**: `_split_repo_identifier()`
- **Function to delete**: `_parse_repo_identifier()`

## WHAT: Main Functions

### New Function to Add
```python
def _split_repo_identifier(repo_full_name: str) -> tuple[str, str]:
    """Split 'owner/repo' format into (owner, repo_name).
    
    Repository Identifier Terminology:
    | Term | Format | Example |
    |------|--------|--------|
    | `repo_url` | Full GitHub URL | `https://github.com/owner/repo.git` |
    | `repo_full_name` | owner/repo | `MarcusJellinghaus/mcp_coder` |
    | `repo_name` | Just the repo | `mcp_coder` |
    | `owner` | Just the owner | `MarcusJellinghaus` |
    
    Args:
        repo_full_name: Repository in "owner/repo" format (exactly one slash required)
        
    Returns:
        Tuple of (owner, repo_name)
        
    Raises:
        ValueError: If input doesn't contain exactly one slash
    """
    slash_count = repo_full_name.count("/")
    if slash_count != 1:
        raise ValueError(
            f"Invalid repo_full_name '{repo_full_name}': expected 'owner/repo' format "
            f"(exactly one slash), got {slash_count} slashes"
        )
    owner, repo_name = repo_full_name.split("/")
    return owner, repo_name
```

### Function to Delete
```python
# Delete entire _parse_repo_identifier() function (~37 lines)
# This function attempted to parse URLs but caused spurious warnings
```

### Function to Simplify: `_get_cache_file_path()`
```python
# BEFORE:
def _get_cache_file_path(repo_full_name: str, owner: str | None = None) -> Path:
    # ... complex branching logic for owner=None fallback

# AFTER:
def _get_cache_file_path(repo_full_name: str) -> Path:
    """Get cache file path for repository.
    
    Args:
        repo_full_name: Repository in "owner/repo" format
        
    Returns:
        Path to cache file (e.g., ~/.mcp_coder/coordinator_cache/owner_repo.issues.json)
    """
    cache_dir = Path.home() / ".mcp_coder" / "coordinator_cache"
    safe_name = repo_full_name.replace("/", "_")
    return cache_dir / f"{safe_name}.issues.json"
```

### Logic Replacement in get_cached_eligible_issues()
```python
# REPLACE the _parse_repo_identifier() call with:
owner, repo_name = _split_repo_identifier(repo_full_name)
```

### Exception Handler Simplification
```python
# REPLACE the complex exception handler with:
except Exception as e:
    _log_cache_metrics("miss", repo_full_name, reason=f"error_{type(e).__name__}")
    logger.warning(f"Cache error for {repo_full_name}: {e}, falling back to direct fetch")
    return get_eligible_issues(issue_manager)
```

## HOW: Integration Points
- **Imports**: No new imports needed
- **Function Signature**: `get_cached_eligible_issues()` unchanged - maintains backward compatibility
- **Cache Logic**: Existing `_get_cache_file_path()` call remains unchanged

## ALGORITHM: Core Logic
```python
# Implementation steps:
1. Add _split_repo_identifier() function near other helper functions
2. In get_cached_eligible_issues(), replace _parse_repo_identifier() call with _split_repo_identifier()
3. Delete entire _parse_repo_identifier() function
4. Simplify exception handler to use repo_full_name directly
5. Verify with: grep -r "_parse_repo_identifier" src/ (should return no results)
```

## DATA: Return Values and Structures

### _split_repo_identifier() Return Values
```python
_split_repo_identifier("owner/repo") -> ("owner", "repo")
_split_repo_identifier("just-repo") -> raises ValueError (0 slashes)
_split_repo_identifier("owner/repo/extra") -> raises ValueError (2 slashes)
```

### get_cached_eligible_issues() (Unchanged)
- **Input**: Same parameters as before
- **Output**: `List[IssueData]` - Same format as before
- **Side Effects**: Cache file with correct naming, no spurious warnings

## Implementation Notes

### Edge Case Handling
- **No slash**: Raises ValueError (invalid input)
- **Multiple slashes**: Raises ValueError (invalid input)
- **Empty string**: Raises ValueError (0 slashes)

### Backward Compatibility
- **Function signature**: Unchanged
- **Return format**: Identical to existing
- **Cache file naming**: Same pattern via `_get_cache_file_path()`

### Verification
```bash
# After implementation, verify no references remain:
grep -r "_parse_repo_identifier" src/
grep -r "_parse_repo_identifier" tests/
# Both should return no results
```