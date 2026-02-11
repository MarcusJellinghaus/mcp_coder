# Step 1: Add `additional_issues` Parameter to Cache

## LLM Prompt

```
You are implementing Step 1 of issue #436 "Fix Closed Issues Being Restarted".

Read pr_info/steps/summary.md for context, then implement the following:

Add an optional `additional_issues` parameter to the cache module that allows fetching specific issues even if they're closed. This is a minimal change to enable the orchestrator to ensure session issues are available in the cache.

Follow Test-Driven Development:
1. First write the tests
2. Then implement the functionality
3. Run tests to verify

Refer to this step file (step_1.md) for detailed specifications.
```

---

## WHERE: File Locations

### Implementation
- **File**: `src/mcp_coder/utils/github_operations/issues/cache.py`
- **Function**: `get_all_cached_issues()`

### Tests
- **File**: `tests/utils/github_operations/test_issue_cache.py` (NEW FILE)

---

## WHAT: Main Functions and Signatures

### Function to Modify

```python
def get_all_cached_issues(
    repo_full_name: str,
    issue_manager: "IssueManager",
    force_refresh: bool = False,
    cache_refresh_minutes: int = 1440,
    additional_issues: list[int] | None = None,  # ← NEW PARAMETER
) -> List[IssueData]:
    """Get all cached issues using cache for performance.
    
    Args:
        repo_full_name: Repository in "owner/repo" format
        issue_manager: IssueManager for GitHub API calls
        force_refresh: Bypass cache entirely
        cache_refresh_minutes: Full refresh threshold (default: 1440 = 24 hours)
        additional_issues: Optional list of issue numbers to fetch even if closed.
                          These are fetched via individual API calls and merged into cache.
    
    Returns:
        List of ALL cached issues including additional issues if provided.
    """
```

### Helper Function to Add

```python
def _fetch_additional_issues(
    issue_manager: "IssueManager",
    additional_issue_numbers: list[int],
    repo_name: str,
) -> dict[str, IssueData]:
    """Fetch specific issues by number via individual API calls.
    
    Args:
        issue_manager: IssueManager for GitHub API calls
        additional_issue_numbers: List of issue numbers to fetch
        repo_name: Repository name for logging
    
    Returns:
        Dict mapping issue number (as string) to IssueData
    """
```

---

## HOW: Integration Points

### Imports (No changes needed)
All necessary imports already exist:
- `IssueManager` from `.manager`
- `List` from typing
- `IssueData` from `.types`

### Integration with Existing Flow

The function already has this structure:
1. Load cache
2. Check duplicate protection
3. Fetch and merge issues
4. Update cache
5. Return all cached issues

**New logic inserts between steps 3 and 4**:
- After fetching open issues
- Before updating cache
- Fetch additional issues and merge them

---

## ALGORITHM: Core Logic (Pseudocode)

### In `get_all_cached_issues()` (after line 294, before cache save):

```python
# Step 3.5: Fetch additional issues if provided
if additional_issues:
    additional_dict = _fetch_additional_issues(
        issue_manager, 
        additional_issues, 
        repo_name
    )
    cache_data["issues"].update(additional_dict)
```

### New function `_fetch_additional_issues()`:

```python
def _fetch_additional_issues(issue_manager, additional_issue_numbers, repo_name):
    result = {}
    for issue_num in additional_issue_numbers:
        # Skip if already in cache
        if str(issue_num) in cache_data["issues"]:
            continue
        
        # Fetch via API
        try:
            issue = issue_manager.get_issue(issue_num)
            if issue["number"] != 0:  # Valid issue
                result[str(issue_num)] = issue
        except Exception as e:
            # Generic exception handling - catches all API failures (404, rate limits, etc.)
            logger.warning(f"Failed to fetch issue #{issue_num}: {e}")
    
    return result
```

---

## DATA: Return Values and Structures

### Input Data
```python
additional_issues: list[int] | None = None
# Example: [414, 408, 399]
```

### Internal Data
```python
additional_dict: Dict[str, IssueData]
# Example: {
#     "414": {"number": 414, "state": "closed", ...},
#     "408": {"number": 408, "state": "closed", ...}
# }
```

### Return Data
```python
-> List[IssueData]
# Returns ALL cached issues (open + additional)
# Additional issues merged into cache_data["issues"] before return
```

---

## TEST SPECIFICATIONS

### Test File: `tests/utils/github_operations/test_issue_cache.py`

#### Test 1: `test_additional_issues_fetched_and_cached`
**Given**: Cache has open issues, additional_issues=[123] where #123 is closed  
**When**: Call `get_all_cached_issues(additional_issues=[123])`  
**Then**: 
- Issue #123 is fetched via API
- Issue #123 is in returned list
- Issue #123 is saved to cache

#### Test 2: `test_additional_issues_skipped_if_in_cache`
**Given**: Cache already has issue #123  
**When**: Call `get_all_cached_issues(additional_issues=[123])`  
**Then**: 
- No API call for #123
- Issue #123 is in returned list (from cache)

#### Test 3: `test_no_additional_issues_backward_compatible`
**Given**: Existing cache with open issues  
**When**: Call `get_all_cached_issues()` (without additional_issues)  
**Then**: 
- Behaves exactly as before
- Only open issues returned

#### Test 4: `test_additional_issues_with_api_failure`
**Given**: API fails for issue #123  
**When**: Call `get_all_cached_issues(additional_issues=[123])`  
**Then**: 
- Warning logged
- Other issues still returned
- No exception raised

#### Test 5: `test_additional_issues_empty_list`
**Given**: Cache with open issues  
**When**: Call `get_all_cached_issues(additional_issues=[])`  
**Then**: 
- Behaves as if parameter not provided
- Only open issues returned

---

## IMPLEMENTATION CHECKLIST

- [ ] Write test file with 5 test cases above
- [ ] Run tests (should fail - TDD)
- [ ] Add `additional_issues` parameter to function signature
- [ ] Implement `_fetch_additional_issues()` helper
- [ ] Add logic to call helper and merge results
- [ ] Add debug logging for additional issues fetch
- [ ] Run tests (should pass)
- [ ] Verify backward compatibility (existing tests still pass)

---

## NOTES

- **Backward Compatibility**: Default value `None` ensures existing calls work unchanged
- **Error Handling**: Generic `Exception` catching is intentional - simpler and catches all API failures (404, rate limits, network errors, etc.). Individual failures are logged but don't stop overall operation.
- **Cache Efficiency**: Check if issue already in cache before API call
- **Logging**: Use DEBUG level for additional issues fetch to avoid noise
