# Step 2: Update Orchestrator to Use `additional_issues`

## LLM Prompt

```
You are implementing Step 2 of issue #436 "Fix Closed Issues Being Restarted".

Read pr_info/steps/summary.md for context, then implement the following:

Update the orchestrator to pass session issue numbers to the cache via the new `additional_issues` parameter. This ensures closed issues from existing sessions are available in the cache.

Follow Test-Driven Development:
1. First write the tests
2. Then implement the functionality
3. Run tests to verify

Refer to this step file (step_2.md) for detailed specifications.
```

---

## WHERE: File Locations

### Implementation
- **File**: `src/mcp_coder/workflows/vscodeclaude/orchestrator.py`
- **Function**: `restart_closed_sessions()`

### Tests
- **File**: `tests/workflows/vscodeclaude/test_orchestrator_cache.py` (NEW FILE)

---

## WHAT: Main Functions and Signatures

### Function to Modify

```python
def restart_closed_sessions(
    cached_issues_by_repo: dict[str, dict[int, IssueData]] | None = None,
) -> list[VSCodeClaudeSession]:
    """Restart sessions where VSCode was closed.
    
    Args:
        cached_issues_by_repo: Dict mapping repo_full_name to issues dict.
                               If provided, avoids API calls for staleness checks
                               and file regeneration.
    
    Returns:
        List of restarted sessions
    """
```

**Note**: Function signature does NOT change. We only modify the internal implementation where it calls `get_all_cached_issues()`.

### Helper Function to Add

```python
def _build_cached_issues_by_repo(
    sessions: list[VSCodeClaudeSession],
) -> dict[str, dict[int, IssueData]]:
    """Build cached issues dict for all repos with sessions.
    
    Fetches issues from cache with additional_issues parameter to ensure
    closed issues from existing sessions are included.
    
    Args:
        sessions: List of all sessions
    
    Returns:
        Dict mapping repo_full_name to dict of issues (issue_number -> IssueData)
    """
```

---

## HOW: Integration Points

### Current Code (orchestrator.py around lines 695-730)

Currently, the code has logic scattered throughout the session loop:

```python
for session in store["sessions"]:
    # ... various checks ...
    
    # Get cached issues for this repo (if available)
    repo_cached_issues: dict[int, IssueData] | None = None
    if cached_issues_by_repo is not None:
        repo_cached_issues = cached_issues_by_repo.get(repo_full_name)
    
    # Get issue data from cache or fetch from API
    if repo_cached_issues and issue_number in repo_cached_issues:
        issue = repo_cached_issues[issue_number]
    else:
        issue_manager = IssueManager(repo_url=repo_url)
        issue = issue_manager.get_issue(issue_number)
```

### New Code Pattern

Add logic **at the beginning of the function** to build cache if not provided:

```python
def restart_closed_sessions(
    cached_issues_by_repo: dict[str, dict[int, IssueData]] | None = None,
) -> list[VSCodeClaudeSession]:
    from .sessions import remove_session
    
    store = load_sessions()
    
    # NEW: Build cache with session issues if not provided
    if cached_issues_by_repo is None:
        cached_issues_by_repo = _build_cached_issues_by_repo(store["sessions"])
    
    # Rest of existing code unchanged...
```

This ensures closed issues from sessions are in the cache.

---

## ALGORITHM: Core Logic (Pseudocode)

### New helper function `_build_cached_issues_by_repo()`:

```python
def _build_cached_issues_by_repo(sessions):
    # Group sessions by repo
    sessions_by_repo = defaultdict(list)
    for session in sessions:
        sessions_by_repo[session["repo"]].append(session["issue_number"])
    
    # Fetch cached issues for each repo with session issue numbers
    cached_issues_by_repo = {}
    for repo_full_name, issue_numbers in sessions_by_repo.items():
        repo_url = f"https://github.com/{repo_full_name}"
        issue_manager = IssueManager(repo_url=repo_url)
        
        # Fetch with additional_issues to include closed session issues
        all_issues = get_all_cached_issues(
            repo_full_name=repo_full_name,
            issue_manager=issue_manager,
            force_refresh=False,
            cache_refresh_minutes=get_cache_refresh_minutes(),
            additional_issues=issue_numbers,  # ← KEY CHANGE
        )
        
        # Convert to dict for fast lookup
        cached_issues_by_repo[repo_full_name] = {
            issue["number"]: issue for issue in all_issues
        }
    
    return cached_issues_by_repo
```

### Modification in `restart_closed_sessions()` (beginning of function):

```python
# Load sessions
store = load_sessions()

# Build cache with session issues if not provided externally
if cached_issues_by_repo is None:
    cached_issues_by_repo = _build_cached_issues_by_repo(store["sessions"])

# Rest of function unchanged...
```

---

## DATA: Return Values and Structures

### Input to `_build_cached_issues_by_repo()`
```python
sessions: list[VSCodeClaudeSession]
# Example: [
#     {"repo": "owner/repo", "issue_number": 414, ...},
#     {"repo": "owner/repo", "issue_number": 408, ...},
#     {"repo": "other/repo", "issue_number": 123, ...}
# ]
```

### Intermediate Data
```python
sessions_by_repo: dict[str, list[int]]
# Example: {
#     "owner/repo": [414, 408],
#     "other/repo": [123]
# }
```

### Return from `_build_cached_issues_by_repo()`
```python
-> dict[str, dict[int, IssueData]]
# Example: {
#     "owner/repo": {
#         414: {"number": 414, "state": "closed", ...},
#         408: {"number": 408, "state": "closed", ...},
#         100: {"number": 100, "state": "open", ...}  # Other open issues
#     },
#     "other/repo": {
#         123: {"number": 123, "state": "open", ...}
#     }
# }
```

---

## TEST SPECIFICATIONS

### Test File: `tests/workflows/vscodeclaude/test_orchestrator_cache.py`

#### Test 1: `test_restart_builds_cache_with_session_issues`
**Given**: 
- No cached_issues_by_repo provided
- Sessions exist for issues #414 (closed) and #100 (open)  
**When**: Call `restart_closed_sessions()`  
**Then**: 
- Cache is built with `additional_issues=[414, 100]`
- Issue #414 is in cache (closed issue from session)
- Issue #100 is in cache (open issue from session)

#### Test 2: `test_restart_uses_provided_cache`
**Given**: 
- cached_issues_by_repo provided with issues
- Sessions exist  
**When**: Call `restart_closed_sessions(cached_issues_by_repo=...)`  
**Then**: 
- Provided cache is used (not rebuilt)
- No additional cache fetch calls

#### Test 3: `test_restart_skips_closed_issues`
**Given**: 
- Session exists for issue #414 (closed)  
**When**: Call `restart_closed_sessions()`  
**Then**: 
- Issue #414 is in cache (via additional_issues)
- Issue #414 is detected as closed
- Issue #414 is skipped (logged "Skipping closed issue")
- No VSCode restart attempted

#### Test 4: `test_build_cache_groups_by_repo`
**Given**: 
- Sessions for issues #414, #408 in "owner/repo"
- Session for issue #123 in "other/repo"  
**When**: Call `_build_cached_issues_by_repo(sessions)`  
**Then**: 
- Two cache fetch calls (one per repo)
- First call: `additional_issues=[414, 408]`
- Second call: `additional_issues=[123]`

#### Test 5: `test_restart_with_no_sessions`
**Given**: No sessions exist  
**When**: Call `restart_closed_sessions()`  
**Then**: 
- Empty dict returned
- No cache fetches
- No errors

---

## IMPLEMENTATION CHECKLIST

- [ ] Write test file with 5 test cases above
- [ ] Run tests (should fail - TDD)
- [ ] Add import for `defaultdict` from `collections` (if not already present)
- [ ] Implement `_build_cached_issues_by_repo()` helper
- [ ] Modify `restart_closed_sessions()` to call helper if cache not provided
- [ ] Add debug logging for cache building
- [ ] Run tests (should pass)
- [ ] Verify existing orchestrator tests still pass
- [ ] Manual test with real closed issues

---

## NOTES

### Backward Compatibility
- If `cached_issues_by_repo` is provided externally (e.g., from status display), use it as-is
- If not provided, build it with session issues included
- This maintains existing behavior while fixing the closed issue problem

### Performance
- Cache is built once at function start, not per-session
- Uses existing `get_all_cached_issues()` with duplicate protection
- Groups sessions by repo to minimize API calls

### Why Not Build Cache in Caller?
The issue description suggests building cache in the orchestrator command handler and passing it down. However, building it inside `restart_closed_sessions()` is simpler:
1. Single place to modify
2. Function is self-contained
3. Works correctly whether cache is provided or not
4. Easier to test

If needed, we can later refactor to build cache at a higher level, but this approach satisfies the immediate requirement.

**Decision**: Keep the simpler approach (build cache inside function). The note in Step 2 is sufficient documentation - no separate decision file needed.

### Integration with Status Display
The status display function `display_status_table()` already accepts `cached_issues_by_repo`. If we want to optimize further, we could build the cache once in the orchestrator command and pass it to both `restart_closed_sessions()` and `display_status_table()`. However, this is an optimization for later, not required for the fix.
