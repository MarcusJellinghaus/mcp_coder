# Step 13: Pass Cached Issues to Staleness Checks

## LLM Prompt

```
You are implementing Step 13 of the vscodeclaude feature. Read pr_info/steps/summary.md for context.

This step eliminates duplicate `get_issue()` API calls by passing cached issues to functions
that check staleness and regenerate files.

Current problem:
- is_session_stale() calls get_issue() individually (~1s per call)
- restart_closed_sessions() calls get_issue() again for file regeneration (~1s per call)
- Each session causes 2+ API calls that could use cached data

Solution: Pass the cached issues dict (from Step 12) and look up by issue number instead.

After changes, run all code quality checks and fix any issues.
```

## Overview

Refactor `is_session_stale()`, `get_issue_current_status()`, and `restart_closed_sessions()` to accept
pre-fetched issue data instead of making individual GitHub API calls.

---

## Task 1: Refactor get_issue_current_status

### WHERE
- `src/mcp_coder/utils/vscodeclaude/status.py`

### WHAT
Add optional `cached_issues` parameter to avoid API calls.

### BEFORE
```python
def get_issue_current_status(
    issue_manager: IssueManager,
    issue_number: int,
) -> tuple[str | None, bool]:
    """Get current status label and open/closed state for an issue."""
    try:
        issue = issue_manager.get_issue(issue_number)  # API call!
        ...
```

### AFTER
```python
def get_issue_current_status(
    issue_number: int,
    cached_issues: dict[int, IssueData] | None = None,
    issue_manager: IssueManager | None = None,
) -> tuple[str | None, bool]:
    """Get current status label and open/closed state for an issue.
    
    Args:
        issue_number: GitHub issue number
        cached_issues: Pre-fetched issues dict (preferred, avoids API call)
        issue_manager: IssueManager for fallback API call (required if cached_issues missing)
    
    Returns:
        Tuple of (status_label, is_open)
    """
    # Try cache first
    if cached_issues is not None and issue_number in cached_issues:
        issue = cached_issues[issue_number]
        is_open = issue["state"] == "open"
        for label in issue["labels"]:
            if label.startswith("status-"):
                return label, is_open
        return None, is_open
    
    # Fallback to API call
    if issue_manager is None:
        raise ValueError("Either cached_issues or issue_manager must be provided")
    
    try:
        issue = issue_manager.get_issue(issue_number)
        ...
```

### ALGORITHM
```
1. If cached_issues provided and issue_number in cache:
   a. Look up issue from cache
   b. Extract state and status label
   c. Return (status, is_open)
2. Else if issue_manager provided:
   a. Call get_issue() API
   b. Extract state and status label
   c. Return (status, is_open)
3. Else raise ValueError
```

---

## Task 2: Refactor is_session_stale

### WHERE
- `src/mcp_coder/utils/vscodeclaude/status.py`

### WHAT
Add optional `cached_issues` parameter.

### BEFORE
```python
def is_session_stale(session: VSCodeClaudeSession) -> bool:
    """Check if session's issue status has changed."""
    ...
    issue_manager: IssueManager = coordinator.IssueManager(repo_url=repo_url)
    current_status, is_open = get_issue_current_status(issue_manager, issue_number)
```

### AFTER
```python
def is_session_stale(
    session: VSCodeClaudeSession,
    cached_issues: dict[int, IssueData] | None = None,
) -> bool:
    """Check if session's issue status has changed.
    
    Args:
        session: Session to check
        cached_issues: Pre-fetched issues dict (avoids API call if provided)
    """
    ...
    # Use cache if available, otherwise create manager for fallback
    if cached_issues is not None:
        current_status, is_open = get_issue_current_status(
            issue_number, cached_issues=cached_issues
        )
    else:
        issue_manager: IssueManager = coordinator.IssueManager(repo_url=repo_url)
        current_status, is_open = get_issue_current_status(
            issue_number, issue_manager=issue_manager
        )
```

---

## Task 3: Refactor is_issue_closed

### WHERE
- `src/mcp_coder/utils/vscodeclaude/status.py`

### WHAT
Add optional `cached_issues` parameter.

### BEFORE
```python
def is_issue_closed(session: VSCodeClaudeSession) -> bool:
    ...
    _, is_open = get_issue_current_status(issue_manager, issue_number)
```

### AFTER
```python
def is_issue_closed(
    session: VSCodeClaudeSession,
    cached_issues: dict[int, IssueData] | None = None,
) -> bool:
    ...
    if cached_issues is not None:
        _, is_open = get_issue_current_status(issue_number, cached_issues=cached_issues)
    else:
        issue_manager: IssueManager = coordinator.IssueManager(repo_url=repo_url)
        _, is_open = get_issue_current_status(issue_number, issue_manager=issue_manager)
```

---

## Task 4: Refactor restart_closed_sessions

### WHERE
- `src/mcp_coder/utils/vscodeclaude/orchestrator.py`

### WHAT
1. Accept `cached_issues` parameter
2. Use cache for `is_session_stale()` check
3. Use cache for `regenerate_session_files()` issue data

### BEFORE
```python
def restart_closed_sessions() -> list[VSCodeClaudeSession]:
    ...
    if is_session_stale(session):
        ...
    issue = issue_manager.get_issue(issue_number)  # Duplicate fetch!
    regenerate_session_files(session, issue)
```

### AFTER
```python
def restart_closed_sessions(
    cached_issues_by_repo: dict[str, dict[int, IssueData]] | None = None,
) -> list[VSCodeClaudeSession]:
    """Restart sessions where VSCode was closed.
    
    Args:
        cached_issues_by_repo: Dict mapping repo_full_name to issues dict
                              If provided, avoids API calls for staleness checks
    """
    ...
    # Get cached issues for this repo (if available)
    repo_cached_issues = None
    if cached_issues_by_repo is not None:
        repo_cached_issues = cached_issues_by_repo.get(repo_full_name)
    
    # Check staleness using cache
    if is_session_stale(session, cached_issues=repo_cached_issues):
        ...
    
    # Get issue data from cache or fetch
    if repo_cached_issues and issue_number in repo_cached_issues:
        issue = repo_cached_issues[issue_number]
    else:
        issue_manager: IssueManager = coordinator.IssueManager(repo_url=repo_url)
        issue = issue_manager.get_issue(issue_number)
    
    regenerate_session_files(session, issue)
```

---

## Task 5: Update Callers to Pass Cache

### WHERE
- `src/mcp_coder/cli/commands/coordinator/commands.py`

### WHAT
Build cached issues dict and pass to functions.

### ALGORITHM (in execute_coordinator_vscodeclaude)
```
1. Load all repos from config
2. For each repo:
   a. Create IssueManager
   b. Call get_all_cached_issues() 
   c. Build issues_by_number: {issue["number"]: issue for issue in cached}
3. Build cached_issues_by_repo: {repo_full_name: issues_by_number}
4. Call restart_closed_sessions(cached_issues_by_repo)
5. For each repo, call process_eligible_issues(cached_issues=issues_by_number)
```

---

## Task 6: Update display_status_table

### WHERE
- `src/mcp_coder/utils/vscodeclaude/status.py`

### WHAT
Pass cached issues to `is_issue_closed()` and `is_session_stale()` calls.

### BEFORE
```python
def display_status_table(...):
    ...
    if is_issue_closed(session):  # API call per session
        ...
    stale = is_session_stale(session)  # Another API call per session
```

### AFTER
```python
def display_status_table(
    sessions: list[VSCodeClaudeSession],
    eligible_issues: list[tuple[str, IssueData]],
    repo_filter: str | None = None,
    cached_issues_by_repo: dict[str, dict[int, IssueData]] | None = None,
) -> None:
    ...
    repo_cached_issues = None
    if cached_issues_by_repo:
        repo_cached_issues = cached_issues_by_repo.get(session["repo"])
    
    if is_issue_closed(session, cached_issues=repo_cached_issues):
        ...
    stale = is_session_stale(session, cached_issues=repo_cached_issues)
```

---

## Task 7: Add Tests

### WHERE
- `tests/utils/vscodeclaude/test_status.py`

### TEST CASES
1. `test_get_issue_current_status_uses_cache` - Verify cache lookup works
2. `test_get_issue_current_status_fallback_to_api` - Verify API fallback
3. `test_is_session_stale_uses_cache` - Verify cache is used when provided
4. `test_is_issue_closed_uses_cache` - Verify cache is used when provided

---

## Verification

After all changes:
1. Run `mcp__code-checker__run_pytest_check` with `-n auto` and exclusion markers
2. Run `mcp__code-checker__run_pylint_check`
3. Run `mcp__code-checker__run_mypy_check`
4. Manually test with `mcp-coder --log-level debug coordinator vscodeclaude`
5. Verify in logs: No individual `get_issue` calls for sessions that have cached data
6. Fix any issues found

## Expected Performance Improvement

Before:
- `list_issues` per repo: 7-45 seconds each (90+ seconds total)
- `get_issue` per session: ~1 second each (duplicated)
- Total for 3 repos, 3 sessions: ~100+ seconds

After:
- Cache hit: <1 second (returns cached data)
- Incremental refresh: 1-5 seconds (only fetches changed issues)
- No individual `get_issue` calls (all from cache)
- Total for 3 repos, 3 sessions: <5 seconds
